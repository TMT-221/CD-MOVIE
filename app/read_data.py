"""Lab 02 B.3: read and display store data using the existing MySQL roles."""
import argparse
from contextlib import closing
from decimal import Decimal

from database import get_connection


def fetch_all(sql, params=()):
    """Execute a parameterized read query, return rows, and close resources."""
    with closing(get_connection()) as connection:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def list_movies():
    return fetch_all("""SELECT MaPhim, TenPhim, NamPhatHanh, DaoDien, ThoiLuong
                        FROM PHIM ORDER BY MaPhim""")


def search_movies(keyword):
    return fetch_all("""SELECT MaPhim, TenPhim, NamPhatHanh FROM PHIM
                        WHERE TenPhim LIKE %s ORDER BY MaPhim""",
                     (f"%{keyword}%",))


def movie_genres():
    return fetch_all("""SELECT p.MaPhim, p.TenPhim, t.TenTheLoai
                        FROM PHIM p JOIN PHIM_THE_LOAI pt ON p.MaPhim = pt.MaPhim
                        JOIN THE_LOAI t ON t.MaTheLoai = pt.MaTheLoai
                        ORDER BY p.MaPhim, t.MaTheLoai""")


def list_products():
    return fetch_all("""SELECT d.MaDia, p.TenPhim, d.PhienBan, d.GiaBan, d.SoLuongTon
                        FROM DIA_CD d JOIN PHIM p ON p.MaPhim = d.MaPhim
                        ORDER BY d.MaDia""")


def low_stock(max_stock=5):
    return fetch_all("""SELECT d.MaDia, p.TenPhim, d.SoLuongTon
                        FROM DIA_CD d JOIN PHIM p ON p.MaPhim = d.MaPhim
                        WHERE d.SoLuongTon BETWEEN 0 AND %s
                        ORDER BY d.SoLuongTon, d.MaDia""", (max_stock,))


def list_customers():
    return fetch_all("""SELECT MaPerson, HoTen FROM vw_KhachHangBanHang
                        ORDER BY MaPerson""")


def monthly_revenue():
    return fetch_all("""SELECT DATE_FORMAT(h.NgayLap, '%Y-%m') AS Thang,
                               COUNT(DISTINCT h.MaHD) AS SoHoaDon,
                               SUM(ct.SoLuong * ct.DonGiaBan) AS DoanhThu
                        FROM HOA_DON h JOIN CHI_TIET_HOA_DON ct ON h.MaHD = ct.MaHD
                        WHERE h.TrangThai = 'HoanTat'
                        GROUP BY DATE_FORMAT(h.NgayLap, '%Y-%m')
                        ORDER BY Thang""")


def show_table(title, rows, limit=10):
    """Display a preview; count always reflects the full result."""
    print(f"\n=== {title} | Rows: {len(rows)} ===")
    if not rows:
        print("(No results)")
        return
    columns = list(rows[0])
    def cell(value):
        return "NULL" if value is None else str(value)
    preview = [[cell(row[key]) for key in columns] for row in rows[:limit]]
    widths = [max(len(key), *(len(row[i]) for row in preview))
              for i, key in enumerate(columns)]
    def line(values):
        return " | ".join(value.ljust(width) for value, width in zip(values, widths))
    print(line(columns))
    print("-+-".join("-" * width for width in widths))
    for row in preview:
        print(line(row))
    if len(rows) > limit:
        print(f"... showing {limit} of {len(rows)} rows")


def check(condition, label):
    if not condition:
        raise RuntimeError(f"FAIL: {label}")
    print(f"PASS: {label}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=["catalog", "customers", "reports"])
    parser.add_argument("--keyword", default="Avengers")
    parser.add_argument("--verify-fixture", action="store_true",
                        help="Check expected values on a freshly seeded CI database")
    args = parser.parse_args()
    identity = fetch_all("SELECT CURRENT_USER() AS Account, CURRENT_ROLE() AS ActiveRole")
    show_table("Connection identity", identity)
    if args.group == "catalog":
        results = [("Movies", list_movies()), ("Search: " + args.keyword, search_movies(args.keyword)),
                   ("Movie genres", movie_genres()), ("CD products", list_products())]
        for title, rows in results:
            show_table(title, rows)
        if args.verify_fixture:
            check(identity[0]["Account"].startswith("cd_viewer@") and "role_cd_viewer" in identity[0]["ActiveRole"], "Viewer role")
            check(len(results[0][1]) == 21, "21 movies")
            check({row["MaPhim"] for row in results[1][1]} == {20003, 20006}, "Avengers search")
            check(len(results[2][1]) == 64, "64 movie-genre links")
            check(len(results[3][1]) == 41, "41 products")
    elif args.group == "customers":
        rows = list_customers()
        show_table("Customer lookup", rows)
        if args.verify_fixture:
            check(identity[0]["Account"].startswith("cd_sales@") and "role_cd_sales" in identity[0]["ActiveRole"], "Sales role")
            check(len(rows) == 33, "33 customers")
            check(all(set(row) == {"MaPerson", "HoTen"} for row in rows), "Limited customer view")
    else:
        stock, revenue = low_stock(), monthly_revenue()
        show_table("Low stock (0-5)", stock)
        show_table("Monthly revenue (completed invoices only)", revenue)
        total = sum((row["DoanhThu"] for row in revenue), Decimal("0"))
        print(f"Total revenue: {total:,.2f} VND")
        if args.verify_fixture:
            check(identity[0]["Account"].startswith("cd_manager@") and "role_cd_manager" in identity[0]["ActiveRole"], "Manager role")
            check({row["MaDia"] for row in stock} == {22002, 22003, 22008, 22014, 22015, 22020, 90203}, "7 low-stock products")
            check(sum(row["SoHoaDon"] for row in revenue) == 71, "71 completed invoices")
            check(total == Decimal("11900000.00"), "Total revenue 11,900,000 VND")
    print("Read operations completed; connections closed.")


if __name__ == "__main__":
    main()
