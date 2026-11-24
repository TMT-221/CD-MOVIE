-- LAB 02 - A.5: SQL practice queries
-- MySQL 8.4 / UTF-8. Run after the schema, routines and sample data.
-- All 18 queries are read-only. Results include Lab 01 demo data if present,
-- except where a specific sample invoice ID is selected.
USE MovieCDStore;
SET NAMES utf8mb4;

-- Q01. List all movies.
SELECT MaPhim, TenPhim, NamPhatHanh, DaoDien, ThoiLuong
FROM PHIM
ORDER BY MaPhim;

-- Q02. Movies released since 2010, newest first.
SELECT MaPhim, TenPhim, NamPhatHanh
FROM PHIM
WHERE NamPhatHanh >= 2010
ORDER BY NamPhatHanh DESC, MaPhim;

-- Q03. Movies with Avengers in the title.
SELECT MaPhim, TenPhim, NamPhatHanh
FROM PHIM
WHERE TenPhim LIKE '%Avengers%'
ORDER BY MaPhim;

-- Q04. Low or zero stock (0 to 5 units).
SELECT MaDia, MaPhim, PhienBan, GiaBan, SoLuongTon
FROM DIA_CD
WHERE SoLuongTon BETWEEN 0 AND 5
ORDER BY SoLuongTon, MaDia;

-- Q05. CD editions and their movie titles.
SELECT d.MaDia, p.TenPhim, d.PhienBan, d.GiaBan, d.SoLuongTon
FROM DIA_CD AS d
JOIN PHIM AS p ON d.MaPhim = p.MaPhim
ORDER BY d.MaDia;

-- Q06. Movies and genres (one row per movie-genre pair).
SELECT p.MaPhim, p.TenPhim, t.TenTheLoai
FROM PHIM AS p
JOIN PHIM_THE_LOAI AS pt ON p.MaPhim = pt.MaPhim
JOIN THE_LOAI AS t ON pt.MaTheLoai = t.MaTheLoai
ORDER BY p.MaPhim, t.MaTheLoai;

-- Q07. Invoice, customer and employee names.
SELECT h.MaHD, kh.HoTen AS TenKhachHang, nv.HoTen AS TenNhanVien,
       h.NgayLap, h.TrangThai
FROM HOA_DON AS h
JOIN KHACH_HANG AS k ON h.MaKhachHang = k.MaPerson
JOIN PERSON AS kh ON k.MaPerson = kh.MaPerson
JOIN NHAN_VIEN AS n ON h.MaNhanVien = n.MaPerson
JOIN PERSON AS nv ON n.MaPerson = nv.MaPerson
ORDER BY h.NgayLap DESC, h.MaHD;

-- Q08. Employees with direct manager names (including employees without a manager).
SELECT n.MaPerson, p.HoTen AS TenNhanVien, n.TrangThaiLamViec,
       n.MaQuanLy, q.HoTen AS TenQuanLy
FROM NHAN_VIEN AS n
JOIN PERSON AS p ON n.MaPerson = p.MaPerson
LEFT JOIN QUAN_LY AS m ON n.MaQuanLy = m.MaPerson
LEFT JOIN PERSON AS q ON m.MaPerson = q.MaPerson
ORDER BY n.MaPerson;

-- Q09. Number of movies per genre, including empty genres.
SELECT t.MaTheLoai, t.TenTheLoai, COUNT(pt.MaPhim) AS SoPhim
FROM THE_LOAI AS t
LEFT JOIN PHIM_THE_LOAI AS pt ON t.MaTheLoai = pt.MaTheLoai
GROUP BY t.MaTheLoai, t.TenTheLoai
ORDER BY SoPhim DESC, t.MaTheLoai;

-- Q10. Movies with at least three genres.
SELECT p.MaPhim, p.TenPhim, COUNT(pt.MaTheLoai) AS SoTheLoai
FROM PHIM AS p
JOIN PHIM_THE_LOAI AS pt ON p.MaPhim = pt.MaPhim
GROUP BY p.MaPhim, p.TenPhim
HAVING COUNT(pt.MaTheLoai) >= 3
ORDER BY SoTheLoai DESC, p.MaPhim;

-- Q11. Count invoices by status.
SELECT TrangThai, COUNT(*) AS SoHoaDon
FROM HOA_DON
GROUP BY TrangThai
ORDER BY TrangThai;

-- Q12. CD editions priced above the average.
SELECT d.MaDia, p.TenPhim, d.PhienBan, d.GiaBan
FROM DIA_CD AS d
JOIN PHIM AS p ON d.MaPhim = p.MaPhim
WHERE d.GiaBan > (SELECT AVG(GiaBan) FROM DIA_CD)
ORDER BY d.GiaBan DESC, d.MaDia;

-- Q13. Customers who have no invoices of any status.
SELECT k.MaPerson, p.HoTen, k.NgayDangKy
FROM KHACH_HANG AS k
JOIN PERSON AS p ON k.MaPerson = p.MaPerson
WHERE NOT EXISTS (
    SELECT 1 FROM HOA_DON AS h WHERE h.MaKhachHang = k.MaPerson
)
ORDER BY k.MaPerson;

-- Q14. People who are both customers and employees (EER overlapping).
SELECT p.MaPerson, p.HoTen
FROM PERSON AS p
WHERE EXISTS (SELECT 1 FROM KHACH_HANG AS k WHERE k.MaPerson = p.MaPerson)
  AND EXISTS (SELECT 1 FROM NHAN_VIEN AS n WHERE n.MaPerson = p.MaPerson)
ORDER BY p.MaPerson;

-- Q15. Customer and employee roles. A person with both roles appears twice.
SELECT p.MaPerson, p.HoTen, 'KhachHang' AS VaiTro
FROM PERSON AS p JOIN KHACH_HANG AS k ON p.MaPerson = k.MaPerson
UNION
SELECT p.MaPerson, p.HoTen, 'NhanVien' AS VaiTro
FROM PERSON AS p JOIN NHAN_VIEN AS n ON p.MaPerson = n.MaPerson
ORDER BY 1, 3;

-- Q16. Top five movies by units sold, completed invoices only.
SELECT p.MaPhim, p.TenPhim, SUM(ct.SoLuong) AS SoDiaDaBan
FROM PHIM AS p
JOIN DIA_CD AS d ON p.MaPhim = d.MaPhim
JOIN CHI_TIET_HOA_DON AS ct ON d.MaDia = ct.MaDia
JOIN HOA_DON AS h ON ct.MaHD = h.MaHD
WHERE h.TrangThai = 'HoanTat'
GROUP BY p.MaPhim, p.TenPhim
ORDER BY SoDiaDaBan DESC, p.MaPhim
LIMIT 5;

-- Q17. Monthly revenue by invoice creation date (not payment date).
-- Historical prices, completed invoices only; count each invoice once.
SELECT DATE_FORMAT(h.NgayLap, '%Y-%m') AS Thang,
       COUNT(DISTINCT h.MaHD) AS SoHoaDon,
       SUM(ct.SoLuong) AS SoDiaDaBan,
       SUM(ct.SoLuong * ct.DonGiaBan) AS DoanhThu
FROM HOA_DON AS h
JOIN CHI_TIET_HOA_DON AS ct ON h.MaHD = ct.MaHD
WHERE h.TrangThai = 'HoanTat'
GROUP BY DATE_FORMAT(h.NgayLap, '%Y-%m')
ORDER BY Thang;

-- Q18. Call the Lab 01 stored function and compare with direct calculation.
-- 23001 is an invoice from the 455-row sample dataset.
SELECT h.MaHD, h.TrangThai,
       fn_TinhTongTienHoaDon(h.MaHD) AS TongTienFunction,
       COALESCE(SUM(ct.SoLuong * ct.DonGiaBan), 0) AS TongTienTinhTrucTiep
FROM HOA_DON AS h
LEFT JOIN CHI_TIET_HOA_DON AS ct ON h.MaHD = ct.MaHD
WHERE h.MaHD = 23001
GROUP BY h.MaHD, h.TrangThai;
