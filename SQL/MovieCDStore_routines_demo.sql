-- DEMO ONLY. Run on an empty training database AFTER:
-- 1. MovieCDStore_schema.sql
-- 2. MovieCDStore_routines.sql
-- Do not run twice: IDs below are fixed for reproducible testing.
USE MovieCDStore;

INSERT INTO PERSON (MaPerson, HoTen)
VALUES (90101, 'Khach hang mau'), (90102, 'Nhan vien mau');

INSERT INTO KHACH_HANG (MaPerson, NgayDangKy)
VALUES (90101, CURRENT_DATE());

INSERT INTO NHAN_VIEN (MaPerson, NgayVaoLam, TrangThaiLamViec)
VALUES (90102, CURRENT_DATE(), 'DangLam');

INSERT INTO NHAN_VIEN_PART_TIME (MaPerson, LuongTheoGio, SoGioToiDaTuan)
VALUES (90102, 30000.00, 20);

INSERT INTO PHIM (MaPhim, TenPhim)
VALUES (90201, 'Phim mau');

INSERT INTO THE_LOAI (MaTheLoai, TenTheLoai)
VALUES (90202, 'The loai mau');

INSERT INTO PHIM_THE_LOAI (MaPhim, MaTheLoai)
VALUES (90201, 90202);

INSERT INTO DIA_CD (MaDia, MaPhim, PhienBan, GiaBan, SoLuongTon)
VALUES (90203, 90201, 'Ban thuong', 50000.00, 5);

CALL sp_TaoHoaDon(90301, 90101, 90102);
CALL sp_ThemChiTietHoaDon(90301, 90203, 2);

-- Expected before completion: 100000.00
SELECT fn_TinhTongTienHoaDon(90301) AS TongTien;

CALL sp_HoanTatHoaDon(90301);

-- Expected: 'HoanTat', 3 discs in stock
SELECT MaHD, TrangThai FROM HOA_DON WHERE MaHD = 90301;
SELECT MaDia, SoLuongTon FROM DIA_CD WHERE MaDia = 90203;

CALL sp_ThongKeDoanhThu(CURRENT_DATE(), CURRENT_DATE());
