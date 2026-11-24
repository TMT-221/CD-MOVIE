"""Lab 02 C.1-C.4: catalog, internal data and sales REST API."""
import os
import secrets
from contextlib import closing
from datetime import date
from decimal import Decimal
from typing import Annotated

import mysql.connector
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

import read_data
import sales_data
from database import get_connection
from write_data import transaction

app = FastAPI(title="Movie CD Store API", version="0.2.0",
              description="Lab 02: catalog, internal data and sales; training environment only")


class MovieSummary(BaseModel):
    MaPhim: int
    TenPhim: str
    NamPhatHanh: int | None


class Movie(MovieSummary):
    DaoDien: str | None
    ThoiLuong: int | None


class MovieGenre(BaseModel):
    MaPhim: int
    TenPhim: str
    TenTheLoai: str


class Product(BaseModel):
    MaDia: int
    TenPhim: str
    PhienBan: str | None
    GiaBan: Decimal
    SoLuongTon: int


def require_viewer_config():
    # The shared read_data helpers use environment-based credentials.
    # Fail closed if the API is accidentally configured with another DB user.
    if os.getenv("DB_USER", "cd_viewer") != "cd_viewer" or not os.getenv("DB_PASSWORD"):
        raise HTTPException(503, "Catalog database configuration unavailable")


@app.exception_handler(mysql.connector.Error)
def database_error(request: Request, exc: mysql.connector.Error):
    # Never expose SQL, credentials or server internals in HTTP responses.
    if exc.errno == 1644:
        messages = {
            "Nhan vien khong ton tai hoac khong dang lam": (403, "Employee inactive or missing"),
            "Dia CD khong ton tai": (404, "Product not found"),
            "Hoa don phai co it nhat mot chi tiet": (409, "Invoice has no items"),
            "Chi hoa don DangTao moi duoc hoan tat": (409, "Invoice is not a draft"),
            "Hoa don khong ton tai hoac khong o trang thai DangTao": (409, "Invoice is not a draft"),
            "Khong du ton kho: giao dich da duoc huy": (409, "Insufficient stock"),
            "So luong mua phai lon hon 0": (422, "Quantity must be positive"),
            "Khoang ngay thong ke khong hop le": (422, "Invalid date range"),
        }
        status, detail = messages.get(exc.msg, (409, "Business rule rejected"))
    elif exc.errno == 1062:
        status, detail = 409, "Record already exists"
    elif exc.errno in (1451, 1452):
        status, detail = 409, "Invalid record reference"
    elif exc.errno == 3819:
        status, detail = 422, "Constraint rejected the input"
    else:
        status, detail = 503, "Database unavailable"
    return JSONResponse(status_code=status, content={"detail": detail})


@app.get("/", tags=["System"])
def home():
    return {"service": "Movie CD Store API", "version": app.version}


@app.get("/health", tags=["System"])
def health():
    require_viewer_config()
    rows = read_data.fetch_all("SELECT 1 AS OK, CURRENT_USER() AS Account, CURRENT_ROLE() AS ActiveRole")
    if (not rows or rows[0]["OK"] != 1
            or not rows[0]["Account"].startswith("cd_viewer@")
            or "role_cd_viewer" not in rows[0]["ActiveRole"]):
        raise HTTPException(503, "Catalog database unavailable")
    return {"status": "ok", "database": "connected"}


@app.get("/movies", response_model=list[Movie], tags=["Movies"])
def movies():
    require_viewer_config()
    return read_data.list_movies()


@app.get("/movies/search", response_model=list[MovieSummary], tags=["Movies"])
def search_movies(keyword: Annotated[str, Query(min_length=1, max_length=200)]):
    require_viewer_config()
    keyword = keyword.strip()
    if not keyword:
        raise HTTPException(422, "Keyword must not be blank")
    return read_data.search_movies(keyword)


@app.get("/movies/genres", response_model=list[MovieGenre], tags=["Movies"])
def genres():
    require_viewer_config()
    return read_data.movie_genres()


@app.get("/products", response_model=list[Product], tags=["Products"])
def products():
    require_viewer_config()
    return read_data.list_products()


@app.get("/products/{product_id}", response_model=Product, tags=["Products"])
def product_detail(product_id: Annotated[int, Path(gt=0, le=2147483647)]):
    require_viewer_config()
    rows = read_data.fetch_all("""SELECT d.MaDia, p.TenPhim, d.PhienBan,
                                       d.GiaBan, d.SoLuongTon
                                FROM DIA_CD d JOIN PHIM p ON p.MaPhim = d.MaPhim
                                WHERE d.MaDia = %s""", (product_id,))
    if not rows:
        raise HTTPException(404, "Product not found")
    return rows[0]


# C.3: HTTP Basic for a local training application. These are API credentials,
# not MySQL passwords. Do not expose this service over plain public HTTP.
basic = HTTPBasic(auto_error=False)
PositiveID = Annotated[int, Field(gt=0, le=2147483647, strict=True)]
PathID = Annotated[int, Path(gt=0, le=2147483647)]


def role_password(role):
    password = os.getenv(f"DB_{role.upper()}_PASSWORD")
    if not password:
        raise HTTPException(503, "Internal database configuration unavailable")
    return password


def role_rows(role, sql, params=()):
    with closing(get_connection(user=f"cd_{role}", password=role_password(role))) as conn:
        with closing(conn.cursor(dictionary=True)) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def current_role(credentials: Annotated[HTTPBasicCredentials | None, Depends(basic)]):
    if credentials is not None and credentials.username in ("sales", "manager"):
        expected = os.getenv(f"API_{credentials.username.upper()}_PASSWORD")
        if expected and secrets.compare_digest(credentials.password.encode(), expected.encode()):
            return credentials.username
    raise HTTPException(401, "Invalid API credentials", headers={"WWW-Authenticate": "Basic"})


def require_manager(role: Annotated[str, Depends(current_role)]):
    if role != "manager":
        raise HTTPException(403, "Manager access required")
    return role


def require_sales(role: Annotated[str, Depends(current_role)]):
    if role != "sales":
        raise HTTPException(403, "Sales access required")
    try:
        employee = int(os.environ["API_SALES_EMPLOYEE_ID"])
        if not 0 < employee <= 2147483647:
            raise ValueError
    except (KeyError, ValueError):
        raise HTTPException(503, "Sales identity configuration unavailable") from None
    # Manager read connection is used only for the server-side identity check.
    rows = role_rows("manager", "SELECT TrangThaiLamViec FROM NHAN_VIEN WHERE MaPerson=%s", (employee,))
    if not rows or rows[0]["TrangThaiLamViec"] != "DangLam":
        raise HTTPException(403, "Employee inactive or missing")
    return employee


class Customer(BaseModel):
    MaPerson: int
    HoTen: str


class Employee(Customer):
    TrangThaiLamViec: str
    MaQuanLy: int | None
    LoaiNhanVien: str


@app.get("/customers", response_model=list[Customer], tags=["Internal"])
def customers(role: Annotated[str, Depends(current_role)]):
    if role == "sales":
        require_sales(role)
    return role_rows(role, "SELECT MaPerson, HoTen FROM vw_KhachHangBanHang ORDER BY MaPerson")


@app.get("/employees", response_model=list[Employee], tags=["Internal"])
def employees(role: Annotated[str, Depends(require_manager)]):
    return role_rows(role, """SELECT n.MaPerson, p.HoTen, n.TrangThaiLamViec, n.MaQuanLy,
        CASE WHEN q.MaPerson IS NOT NULL THEN 'Manager'
             WHEN f.MaPerson IS NOT NULL THEN 'Full-time'
             WHEN t.MaPerson IS NOT NULL THEN 'Part-time' ELSE 'Unclassified' END AS LoaiNhanVien
        FROM NHAN_VIEN n JOIN PERSON p ON p.MaPerson=n.MaPerson
        LEFT JOIN NHAN_VIEN_FULL_TIME f ON f.MaPerson=n.MaPerson
        LEFT JOIN NHAN_VIEN_PART_TIME t ON t.MaPerson=n.MaPerson
        LEFT JOIN QUAN_LY q ON q.MaPerson=n.MaPerson ORDER BY n.MaPerson""")


# C.4: invoice ownership checks at the application boundary. The underlying
# MySQL role is shared and cannot enforce per-employee ownership by itself.
class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InvoiceCreate(InputModel):
    MaHD: PositiveID
    MaKhachHang: PositiveID


class InvoiceItem(InputModel):
    MaDia: PositiveID
    SoLuong: PositiveID


class InvoiceStatus(BaseModel):
    MaHD: int
    TrangThai: str


class InvoiceTotal(BaseModel):
    MaHD: int
    TongTien: Decimal


class ProductPatch(InputModel):
    GiaBan: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2, allow_inf_nan=False)] | None = None
    SoLuongTon: Annotated[int, Field(ge=0, le=2147483647, strict=True)] | None = None

    @model_validator(mode="after")
    def nonempty(self):
        if self.GiaBan is None and self.SoLuongTon is None:
            raise ValueError("Supply at least one product field")
        return self


class Revenue(BaseModel):
    NgayLap: date
    SoHoaDon: int
    DoanhThu: Decimal


def owned_invoice(invoice_id, employee):
    # Return the same 404 for missing and another employee's invoice.
    rows = role_rows("manager", "SELECT MaHD, TrangThai FROM HOA_DON WHERE MaHD=%s AND MaNhanVien=%s",
                     (invoice_id, employee))
    if not rows:
        raise HTTPException(404, "Invoice not found")
    return rows[0]


@app.post("/invoices", status_code=201, response_model=InvoiceStatus, tags=["Sales"])
def create_invoice(body: InvoiceCreate, employee: Annotated[int, Depends(require_sales)]):
    sales_data.create_invoice(role_password("sales"), body.MaHD, body.MaKhachHang, employee)
    return {"MaHD": body.MaHD, "TrangThai": "DangTao"}


@app.post("/invoices/{invoice_id}/items", status_code=201, tags=["Sales"])
def add_item(invoice_id: PathID, body: InvoiceItem, employee: Annotated[int, Depends(require_sales)]):
    owned_invoice(invoice_id, employee)
    sales_data.add_invoice_item(role_password("sales"), invoice_id, body.MaDia, body.SoLuong)
    return {"MaHD": invoice_id, "MaDia": body.MaDia, "SoLuong": body.SoLuong}


@app.get("/invoices/{invoice_id}/total", response_model=InvoiceTotal, tags=["Sales"])
def invoice_total(invoice_id: PathID, employee: Annotated[int, Depends(require_sales)]):
    owned_invoice(invoice_id, employee)
    return {"MaHD": invoice_id, "TongTien": sales_data.invoice_total(role_password("sales"), invoice_id)}


@app.post("/invoices/{invoice_id}/complete", response_model=InvoiceStatus, tags=["Sales"])
def complete_invoice(invoice_id: PathID, employee: Annotated[int, Depends(require_sales)]):
    owned_invoice(invoice_id, employee)
    sales_data.complete_invoice(role_password("sales"), invoice_id)
    return {"MaHD": invoice_id, "TrangThai": "HoanTat"}


@app.patch("/products/{product_id}", response_model=Product, tags=["Management"])
def patch_product(product_id: PathID, body: ProductPatch, role: Annotated[str, Depends(require_manager)]):
    # Partial update, no read/modify/write in separate transactions. COALESCE
    # retains omitted fields; lock and read updated row in the same transaction.
    with transaction("cd_manager", role_password(role)) as cursor:
        cursor.execute("""UPDATE DIA_CD SET GiaBan=COALESCE(%s,GiaBan),
            SoLuongTon=COALESCE(%s,SoLuongTon) WHERE MaDia=%s""",
            (body.GiaBan, body.SoLuongTon, product_id))
        cursor.execute("""SELECT d.MaDia,p.TenPhim,d.PhienBan,d.GiaBan,d.SoLuongTon
            FROM DIA_CD d JOIN PHIM p ON p.MaPhim=d.MaPhim WHERE d.MaDia=%s""", (product_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(404, "Product not found")
        return dict(zip(cursor.column_names, row))


@app.get("/reports/revenue", response_model=list[Revenue], tags=["Management"])
def revenue(start_date: date, end_date: date, role: Annotated[str, Depends(require_manager)]):
    if start_date > end_date or end_date == date.max:
        raise HTTPException(422, "Invalid date range")
    rows = sales_data.revenue_report(role_password(role), start_date, end_date)
    return [dict(zip(("NgayLap", "SoHoaDon", "DoanhThu"), row)) for row in rows]
