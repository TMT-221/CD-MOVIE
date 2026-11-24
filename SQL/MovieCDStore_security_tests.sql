-- MovieCDStore - Lab 02 A.7: access control tests (MySQL 8.4)
-- Run EACH statement separately with the named connection, NOT all at once.
-- Expected errors are intentional. No test inserts/deletes or changes values.
-- Prerequisites: schema, routines, sample data, security script.
-- Run this identity query again after every switch of connection:
USE MovieCDStore;
SELECT CURRENT_USER() AS TaiKhoan, CURRENT_ROLE() AS VaiTro, @@port AS CongKetNoi;

-- ADMIN: cd_admin@127.0.0.1
-- T01 ALLOW: read employee data.
SELECT MaPerson, LuongThang FROM NHAN_VIEN_FULL_TIME LIMIT 5;
-- T02 ALLOW: update movie (same value, no actual change).
UPDATE PHIM SET TenPhim = TenPhim WHERE MaPhim = 20001;
-- T03 DENY: read global MySQL accounts (1142 expected).
SELECT User, Host FROM mysql.user LIMIT 5;

-- MANAGER: cd_manager@127.0.0.1
-- T04 ALLOW: read customer information.
SELECT MaPerson, HoTen, Email FROM PERSON LIMIT 5;
-- T05 ALLOW: update price (same value, no actual change).
UPDATE DIA_CD SET GiaBan = GiaBan WHERE MaDia = 22001;
-- T06 ALLOW: update stock (same value, no actual change).
UPDATE DIA_CD SET SoLuongTon = SoLuongTon WHERE MaDia = 22001;
-- T07 ALLOW: revenue report.
CALL sp_ThongKeDoanhThu('2026-01-01', '2026-12-31');
-- T08 DENY: update unauthorized column (1142 or 1143 expected).
UPDATE DIA_CD SET PhienBan = PhienBan WHERE MaDia = 22001;
-- T09 DENY: direct delete (no row matches; 1142 expected).
DELETE FROM PHIM WHERE 1 = 0;

-- SALES: cd_sales@127.0.0.1
-- T10 ALLOW: read product catalog.
SELECT MaDia, GiaBan, SoLuongTon FROM DIA_CD LIMIT 5;
-- T11 ALLOW: read limited customer view.
SELECT * FROM vw_KhachHangBanHang LIMIT 5;
-- T12 ALLOW: calculate total of existing sample invoice.
SELECT fn_TinhTongTienHoaDon(23001) AS TongTien;
-- T13 ALLOW EXECUTE: deliberately invalid employee; expected 1644 (SQLSTATE 45000).
-- If 1370 instead, EXECUTE permission is missing. No invoice is inserted.
CALL sp_TaoHoaDon(99001, 10001, -1);
-- T14 DENY: read PERSON directly (1142 expected).
SELECT * FROM PERSON LIMIT 5;
-- T15 DENY: direct invoice update (1142 expected).
UPDATE HOA_DON SET TrangThai = TrangThai WHERE MaHD = 23001;
-- T16 DENY: revenue procedure (1370 expected).
CALL sp_ThongKeDoanhThu('2026-01-01', '2026-12-31');

-- VIEWER: cd_viewer@127.0.0.1
-- T17 ALLOW: read film catalog.
SELECT MaPhim, TenPhim, NamPhatHanh FROM PHIM LIMIT 5;
-- T18 ALLOW: read price and stock.
SELECT MaDia, GiaBan, SoLuongTon FROM DIA_CD LIMIT 5;
-- T19 DENY: update product price (1142 expected).
UPDATE DIA_CD SET GiaBan = GiaBan WHERE MaDia = 22001;
-- T20 DENY: read customer view (1142 expected).
SELECT * FROM vw_KhachHangBanHang LIMIT 5;
-- T21 DENY: execute invoice function (1370 expected).
SELECT fn_TinhTongTienHoaDon(23001) AS TongTien;
-- End. Expected errors are evidence of working authorization, not script defects.
