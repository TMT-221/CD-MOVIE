"""Lab 02 B.4: transaction-based writes and integration tests.
Run only against a training database. Tests create and remove their own rows.
Set DB_ADMIN_PASSWORD, DB_MANAGER_PASSWORD and DB_VIEWER_PASSWORD.
"""
import os
from contextlib import closing, contextmanager
from decimal import Decimal

import mysql.connector

from database import get_connection


@contextmanager
def transaction(user, password):
    with closing(get_connection(user=user, password=password)) as connection:
        try:
            with closing(connection.cursor()) as cursor:
                yield cursor
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def create_movie_product(admin_password, movie_id, product_id, genre_id,
                         title, price, stock):
    with transaction("cd_admin", admin_password) as cursor:
        cursor.execute("INSERT INTO PHIM (MaPhim, TenPhim) VALUES (%s, %s)",
                       (movie_id, title))
        cursor.execute("INSERT INTO PHIM_THE_LOAI (MaPhim, MaTheLoai) VALUES (%s, %s)",
                       (movie_id, genre_id))
        cursor.execute("""INSERT INTO DIA_CD
            (MaDia, MaPhim, PhienBan, GiaBan, SoLuongTon)
            VALUES (%s, %s, %s, %s, %s)""",
            (product_id, movie_id, "B4 test", price, stock))


def update_product(manager_password, product_id, price, stock):
    with transaction("cd_manager", manager_password) as cursor:
        cursor.execute("""UPDATE DIA_CD SET GiaBan = %s, SoLuongTon = %s
                          WHERE MaDia = %s""", (price, stock, product_id))


def delete_movie_product(admin_password, movie_id, product_id, genre_id):
    # Delete child rows before the parent row to respect foreign keys.
    with transaction("cd_admin", admin_password) as cursor:
        cursor.execute("DELETE FROM DIA_CD WHERE MaDia = %s AND MaPhim = %s",
                       (product_id, movie_id))
        cursor.execute("DELETE FROM PHIM_THE_LOAI WHERE MaPhim = %s AND MaTheLoai = %s",
                       (movie_id, genre_id))
        cursor.execute("DELETE FROM PHIM WHERE MaPhim = %s", (movie_id,))


def fetch_one(user, password, sql, params=()):
    with closing(get_connection(user=user, password=password)) as connection:
        with closing(connection.cursor(buffered=True)) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def read_product(viewer_password, product_id):
    return fetch_one("cd_viewer", viewer_password,
                     "SELECT GiaBan, SoLuongTon FROM DIA_CD WHERE MaDia = %s",
                     (product_id,))


def check(condition, label):
    if not condition:
        raise RuntimeError(f"FAIL: {label}")
    print(f"PASS: {label}")


def expect_error(operation, codes, label):
    try:
        operation()
    except mysql.connector.Error as exc:
        if exc.errno not in codes:
            raise
        print(f"PASS: {label} (MySQL error {exc.errno})")
    else:
        raise RuntimeError(f"FAIL: {label}; expected MySQL error {codes}")


def main():
    admin = os.environ["DB_ADMIN_PASSWORD"]
    manager = os.environ["DB_MANAGER_PASSWORD"]
    viewer = os.environ["DB_VIEWER_PASSWORD"]
    # Reserved high IDs; fail safely if already in use. Never overwrite existing data.
    movie_id, product_id, bad_movie_id, bad_product_id = 99011, 99012, 99013, 99014
    genre_id = 21001  # Existing genre in Lab 02 sample data.
    for user, password in (("cd_admin", admin), ("cd_manager", manager), ("cd_viewer", viewer)):
        account, role = fetch_one(user, password, "SELECT CURRENT_USER(), CURRENT_ROLE()")
        if not account.startswith(user + "@") or f"role_{user}" not in role:
            raise RuntimeError(f"Unexpected account/role: {account}, {role}")
    for mid in (movie_id, bad_movie_id):
        if fetch_one("cd_viewer", viewer, "SELECT MaPhim FROM PHIM WHERE MaPhim = %s", (mid,)):
            raise RuntimeError(f"Test ID {mid} already exists; choose unused test IDs")
    for pid in (product_id, bad_product_id):
        if read_product(viewer, pid) is not None:
            raise RuntimeError(f"Test ID {pid} already exists; choose unused test IDs")
    if not fetch_one("cd_viewer", viewer, "SELECT MaTheLoai FROM THE_LOAI WHERE MaTheLoai = %s", (genre_id,)):
        raise RuntimeError("Import Lab 02 sample data before running B.4")

    created = False
    try:
        # W01: real commit, verified through a fresh connection with the viewer role.
        create_movie_product(admin, movie_id, product_id, genre_id,
                             "B4 - Test movie", Decimal("50000"), 10)
        created = True
        check(read_product(viewer, product_id) == (Decimal("50000"), 10)
              and fetch_one("cd_viewer", viewer,
                  "SELECT MaPhim FROM PHIM_THE_LOAI WHERE MaPhim = %s AND MaTheLoai = %s",
                  (movie_id, genre_id)) == (movie_id,), "W01 INSERT and COMMIT")

        # W02: manager is allowed to update only price and stock.
        update_product(manager, product_id, Decimal("65000"), 15)
        check(read_product(viewer, product_id) == (Decimal("65000"), 15),
              "W02 UPDATE and COMMIT")

        # W03: valid first write followed by an invalid CHECK-constrained write.
        def invalid_update():
            with transaction("cd_manager", manager) as cursor:
                cursor.execute("UPDATE DIA_CD SET SoLuongTon = %s WHERE MaDia = %s", (20, product_id))
                cursor.execute("UPDATE DIA_CD SET GiaBan = %s WHERE MaDia = %s", (-1, product_id))
        expect_error(invalid_update, {3819}, "W03 CHECK constraint rejects negative price")
        check(read_product(viewer, product_id) == (Decimal("65000"), 15),
              "W03 ROLLBACK restored stock and price")

        # W04: failed child INSERT must roll back the new parent and link.
        expect_error(lambda: create_movie_product(admin, bad_movie_id, bad_product_id,
                     genre_id, "B4 - Invalid movie", Decimal("-1"), 10),
                     {3819}, "W04 invalid product rejected")
        check(fetch_one("cd_viewer", viewer, "SELECT MaPhim FROM PHIM WHERE MaPhim = %s",
                        (bad_movie_id,)) is None
              and read_product(viewer, bad_product_id) is None
              and fetch_one("cd_viewer", viewer,
                    "SELECT MaPhim FROM PHIM_THE_LOAI WHERE MaPhim = %s", (bad_movie_id,)) is None,
              "W04 atomic INSERT rolled back all rows")

        # W05: viewer may not change product data.
        def viewer_write():
            with transaction("cd_viewer", viewer) as cursor:
                cursor.execute("UPDATE DIA_CD SET GiaBan = %s WHERE MaDia = %s", (1, product_id))
        expect_error(viewer_write, {1142, 1143}, "W05 viewer write denied")
        check(read_product(viewer, product_id) == (Decimal("65000"), 15), "W05 data unchanged")
    finally:
        if created:
            delete_movie_product(admin, movie_id, product_id, genre_id)
    check(read_product(viewer, product_id) is None
          and fetch_one("cd_viewer", viewer, "SELECT MaPhim FROM PHIM WHERE MaPhim = %s", (movie_id,)) is None
          and fetch_one("cd_viewer", viewer, "SELECT MaPhim FROM PHIM_THE_LOAI WHERE MaPhim = %s", (movie_id,)) is None,
          "W06 DELETE and COMMIT; test records removed")
    print("B.4: all 6 write test cases PASS; connections closed.")


if __name__ == "__main__":
    main()
