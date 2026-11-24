"""Lab 02 B.5: invoke existing routines and verify sales on a training DB.
Run only on a disposable/training database, not concurrently with other tests.
Requires Lab 01 demo and the B.4 database.py / write_data.py modules.
"""
import os
from contextlib import closing
from decimal import Decimal

import mysql.connector

from database import get_connection
from write_data import transaction, fetch_one, check


def call_procedure(user, password, sql, params):
    """Execute a fixed CALL statement and consume every result set."""
    with closing(get_connection(user=user, password=password)) as connection:
        with closing(connection.cursor(buffered=True)) as cursor:
            cursor.execute(sql, params)
            rows = []
            while True:
                if cursor.with_rows:
                    rows.extend(cursor.fetchall())
                if not cursor.nextset():
                    break
            return rows
    # Sales routines manage START TRANSACTION / COMMIT / ROLLBACK themselves.


def create_invoice(password, invoice_id, customer_id, employee_id):
    call_procedure('cd_sales', password, 'CALL sp_TaoHoaDon(%s, %s, %s)',
                   (invoice_id, customer_id, employee_id))


def add_invoice_item(password, invoice_id, product_id, quantity):
    call_procedure('cd_sales', password, 'CALL sp_ThemChiTietHoaDon(%s, %s, %s)',
                   (invoice_id, product_id, quantity))


def invoice_total(password, invoice_id):
    return fetch_one('cd_sales', password, 'SELECT fn_TinhTongTienHoaDon(%s)',
                     (invoice_id,))[0]


def complete_invoice(password, invoice_id):
    call_procedure('cd_sales', password, 'CALL sp_HoanTatHoaDon(%s)', (invoice_id,))


def revenue_report(password, start_date, end_date):
    return call_procedure('cd_manager', password, 'CALL sp_ThongKeDoanhThu(%s, %s)',
                          (start_date, end_date))


def expect_business_error(operation, message):
    try:
        operation()
    except mysql.connector.Error as exc:
        if exc.errno != 1644 or exc.sqlstate != '45000' or message not in exc.msg:
            raise
    else:
        raise RuntimeError(f'Expected business error: {message}')


def main():
    admin = os.environ['DB_ADMIN_PASSWORD']
    sales = os.environ['DB_SALES_PASSWORD']
    manager = os.environ['DB_MANAGER_PASSWORD']
    for user, password in [('cd_admin', admin), ('cd_sales', sales), ('cd_manager', manager)]:
        account, role = fetch_one(user, password, 'SELECT CURRENT_USER(), CURRENT_ROLE()')
        if not account.startswith(user + '@') or f'role_{user}' not in role:
            raise RuntimeError(f'Unexpected account/role: {account}, {role}')

    # Reserved IDs and existing Lab 01 demo references. Refuse to overwrite rows.
    product_a, product_b = 99021, 99022
    invoice_a, invoice_b = 99023, 99024
    customer, employee, movie = 90101, 90102, 90201

    def read(sql, params=()):
        return fetch_one('cd_manager', manager, sql, params)

    def stock(product_id):
        row = read('SELECT SoLuongTon FROM DIA_CD WHERE MaDia = %s', (product_id,))
        return row[0] if row else None

    def status(invoice_id):
        row = read('SELECT TrangThai FROM HOA_DON WHERE MaHD = %s', (invoice_id,))
        return row[0] if row else None

    def revenue_totals():
        rows = revenue_report(manager, '2000-01-01', '2100-12-31')
        for day, count, amount in rows:
            print(f'Revenue {day}: invoices={count}, amount={amount}')
        return sum(r[1] for r in rows), sum((r[2] for r in rows), Decimal('0'))

    if any(stock(p) is not None for p in (product_a, product_b)) or any(
            status(i) is not None for i in (invoice_a, invoice_b)):
        raise RuntimeError('B.5 test IDs already exist; do not overwrite existing records')
    if (not read('SELECT MaPerson FROM KHACH_HANG WHERE MaPerson = %s', (customer,))
            or read('SELECT TrangThaiLamViec FROM NHAN_VIEN WHERE MaPerson = %s', (employee,)) != ('DangLam',)
            or not read('SELECT MaPhim FROM PHIM WHERE MaPhim = %s', (movie,))):
        raise RuntimeError('Import the Lab 01 demo before running B.5')
    baseline_count, baseline_revenue = revenue_totals()

    # Only the test harness uses admin DML to seed and remove disposable rows.
    with transaction('cd_admin', admin) as cursor:
        cursor.executemany('''INSERT INTO DIA_CD
            (MaDia, MaPhim, PhienBan, GiaBan, SoLuongTon)
            VALUES (%s, %s, %s, %s, %s)''', [
            (product_a, movie, 'B5 test A', Decimal('50000'), 10),
            (product_b, movie, 'B5 test B', Decimal('30000'), 1),
        ])
    try:
        expect_business_error(lambda: create_invoice(sales, invoice_a, customer, -1),
                              'Nhan vien khong ton tai hoac khong dang lam')
        check(status(invoice_a) is None, 'S01 Invalid employee rejected; no invoice')

        create_invoice(sales, invoice_a, customer, employee)
        check(status(invoice_a) == 'DangTao', 'S02 Invoice created in DangTao')

        expect_business_error(lambda: complete_invoice(sales, invoice_a),
                              'Hoa don phai co it nhat mot chi tiet')
        check(status(invoice_a) == 'DangTao', 'S03 Empty invoice cannot be completed')

        add_invoice_item(sales, invoice_a, product_a, 2)
        check(invoice_total(sales, invoice_a) == Decimal('100000') and stock(product_a) == 10
              and read('SELECT SoLuong, DonGiaBan FROM CHI_TIET_HOA_DON WHERE MaHD = %s AND MaDia = %s',
                       (invoice_a, product_a)) == (2, Decimal('50000')),
              'S04 Add 2 CDs; total=100000; stock remains 10')

        complete_invoice(sales, invoice_a)
        check(status(invoice_a) == 'HoanTat' and stock(product_a) == 8,
              'S05 Complete invoice; stock 10 -> 8')

        expect_business_error(lambda: complete_invoice(sales, invoice_a),
                              'Chi hoa don DangTao moi duoc hoan tat')
        check(stock(product_a) == 8 and status(invoice_a) == 'HoanTat',
              'S06 Duplicate completion rejected; no double deduction')

        create_invoice(sales, invoice_b, customer, employee)
        add_invoice_item(sales, invoice_b, product_a, 2)
        add_invoice_item(sales, invoice_b, product_b, 2)  # only one in stock
        expect_business_error(lambda: complete_invoice(sales, invoice_b),
                              'Khong du ton kho')
        check(status(invoice_b) == 'DangTao' and stock(product_a) == 8 and stock(product_b) == 1,
              'S07 Insufficient stock; atomic rollback on both products')

        count, amount = revenue_totals()
        check(count == baseline_count + 1 and amount == baseline_revenue + Decimal('100000'),
              'S08 Revenue +100000; draft excluded')
    finally:
        # Clean up invoices first; stock changes affect only disposable products.
        with transaction('cd_admin', admin) as cursor:
            cursor.execute('DELETE FROM CHI_TIET_HOA_DON WHERE MaHD IN (%s, %s)', (invoice_a, invoice_b))
            cursor.execute('DELETE FROM HOA_DON WHERE MaHD IN (%s, %s)', (invoice_a, invoice_b))
            cursor.execute('DELETE FROM DIA_CD WHERE MaDia IN (%s, %s)', (product_a, product_b))

    check(all(status(i) is None for i in (invoice_a, invoice_b))
          and all(stock(p) is None for p in (product_a, product_b))
          and revenue_totals() == (baseline_count, baseline_revenue), 'Test fixtures removed; revenue restored')
    print('B.5: all 8 sales test cases PASS; connections closed.')


if __name__ == '__main__':
    main()
