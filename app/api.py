"""Lab 02 C.1-C.2: read-only catalog REST API (run with --app-dir app)."""
import os
from decimal import Decimal
from typing import Annotated

import mysql.connector
from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import read_data

app = FastAPI(title="Movie CD Store API", version="0.1.0",
              description="Lab 02: read-only movie and CD catalog")


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
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


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
