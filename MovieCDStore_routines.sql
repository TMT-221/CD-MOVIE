-- MOVIE CD STORE MANAGEMENT SYSTEM
-- Lab 01 / DDD Step 5.6: Stored Procedures and Functions
-- Requirement: execute MovieCDStore_schema.sql first.
-- Target: MySQL 8.0.16+ / InnoDB
-- Existing tables and columns are not changed by this script.
-- Re-run note: existing routines with these names will be replaced.
USE MovieCDStore;

DROP PROCEDURE IF EXISTS sp_ThongKeDoanhThu;
DROP PROCEDURE IF EXISTS sp_HoanTatHoaDon;
DROP PROCEDURE IF EXISTS sp_ThemChiTietHoaDon;
DROP PROCEDURE IF EXISTS sp_TaoHoaDon;
DROP FUNCTION IF EXISTS fn_TinhTongTienHoaDon;

DELIMITER $$

-- BR05: Only an active employee may create a new invoice.
CREATE PROCEDURE sp_TaoHoaDon(
    IN p_MaHD INT,
    IN p_MaKhachHang INT,
    IN p_MaNhanVien INT
)
BEGIN
    DECLARE v_TrangThai VARCHAR(20) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT TrangThaiLamViec
      INTO v_TrangThai
      FROM NHAN_VIEN
     WHERE MaPerson = p_MaNhanVien
     FOR SHARE;

    IF v_TrangThai IS NULL OR v_TrangThai <> 'DangLam' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Nhan vien khong ton tai hoac khong dang lam';
    END IF;

    INSERT INTO HOA_DON (MaHD, MaKhachHang, MaNhanVien, NgayLap, TrangThai)
    VALUES (p_MaHD, p_MaKhachHang, p_MaNhanVien, NOW(), 'DangTao');

    COMMIT;
END$$

-- BR15: Capture today's CD price in each draft invoice line.
-- Adding a line DOES NOT deduct stock. Stock is deducted upon completion.
CREATE PROCEDURE sp_ThemChiTietHoaDon(
    IN p_MaHD INT,
    IN p_MaDia INT,
    IN p_SoLuong INT
)
BEGIN
    DECLARE v_TrangThai VARCHAR(30) DEFAULT NULL;
    DECLARE v_GiaBan DECIMAL(12,2) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_SoLuong IS NULL OR p_SoLuong <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'So luong mua phai lon hon 0';
    END IF;

    START TRANSACTION;

    SELECT TrangThai
      INTO v_TrangThai
      FROM HOA_DON
     WHERE MaHD = p_MaHD
     FOR UPDATE;

    IF v_TrangThai IS NULL OR v_TrangThai <> 'DangTao' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Hoa don khong ton tai hoac khong o trang thai DangTao';
    END IF;

    SELECT GiaBan
      INTO v_GiaBan
      FROM DIA_CD
     WHERE MaDia = p_MaDia
     FOR SHARE;

    IF v_GiaBan IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Dia CD khong ton tai';
    END IF;

    INSERT INTO CHI_TIET_HOA_DON (MaHD, MaDia, SoLuong, DonGiaBan)
    VALUES (p_MaHD, p_MaDia, p_SoLuong, v_GiaBan);
    -- The composite primary key (MaHD, MaDia) prevents duplicate line items.

    COMMIT;
END$$

-- BR11 + BR13: Deduct stock atomically and complete the invoice.
CREATE PROCEDURE sp_HoanTatHoaDon(IN p_MaHD INT)
BEGIN
    DECLARE v_TrangThai VARCHAR(30) DEFAULT NULL;
    DECLARE v_SoDong INT DEFAULT 0;
    DECLARE v_SoDongDaTru INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT TrangThai
      INTO v_TrangThai
      FROM HOA_DON
     WHERE MaHD = p_MaHD
     FOR UPDATE;

    IF v_TrangThai IS NULL OR v_TrangThai <> 'DangTao' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Chi hoa don DangTao moi duoc hoan tat';
    END IF;

    SELECT COUNT(*)
      INTO v_SoDong
      FROM CHI_TIET_HOA_DON
     WHERE MaHD = p_MaHD;

    IF v_SoDong = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Hoa don phai co it nhat mot chi tiet';
    END IF;

    -- An UPDATE takes exclusive locks on modified CD rows. If any line has
    -- insufficient stock, ROW_COUNT differs from v_SoDong and all changes
    -- are rolled back. The invoice lock serializes add/complete operations.
    UPDATE DIA_CD AS d
    JOIN CHI_TIET_HOA_DON AS ct ON ct.MaDia = d.MaDia
       SET d.SoLuongTon = d.SoLuongTon - ct.SoLuong
     WHERE ct.MaHD = p_MaHD
       AND d.SoLuongTon >= ct.SoLuong;

    SET v_SoDongDaTru = ROW_COUNT();

    IF v_SoDongDaTru <> v_SoDong THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Khong du ton kho: giao dich da duoc huy';
    END IF;

    UPDATE HOA_DON
       SET TrangThai = 'HoanTat'
     WHERE MaHD = p_MaHD;

    COMMIT;
END$$

-- Returns the sum of historical line prices for a given invoice.
CREATE FUNCTION fn_TinhTongTienHoaDon(p_MaHD INT)
RETURNS DECIMAL(18,2)
NOT DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_Tong DECIMAL(18,2) DEFAULT 0.00;

    SELECT COALESCE(SUM(SoLuong * DonGiaBan), 0.00)
      INTO v_Tong
      FROM CHI_TIET_HOA_DON
     WHERE MaHD = p_MaHD;

    RETURN v_Tong;
END$$

-- Revenue per invoice creation date (not actual payment/completion date).
-- Only completed invoices are included.
CREATE PROCEDURE sp_ThongKeDoanhThu(
    IN p_TuNgay DATE,
    IN p_DenNgay DATE
)
BEGIN
    IF p_TuNgay IS NULL OR p_DenNgay IS NULL OR p_TuNgay > p_DenNgay THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Khoang ngay thong ke khong hop le';
    END IF;

    SELECT DATE(h.NgayLap) AS NgayLap,
           COUNT(DISTINCT h.MaHD) AS SoHoaDon,
           COALESCE(SUM(ct.SoLuong * ct.DonGiaBan), 0.00) AS DoanhThu
      FROM HOA_DON AS h
      JOIN CHI_TIET_HOA_DON AS ct ON ct.MaHD = h.MaHD
     WHERE h.TrangThai = 'HoanTat'
       AND h.NgayLap >= p_TuNgay
       AND h.NgayLap < DATE_ADD(p_DenNgay, INTERVAL 1 DAY)
     GROUP BY DATE(h.NgayLap)
     ORDER BY NgayLap;
END$$

DELIMITER ;

-- Verification (read-only):
SHOW PROCEDURE STATUS WHERE Db = 'MovieCDStore';
SHOW FUNCTION STATUS WHERE Db = 'MovieCDStore';
