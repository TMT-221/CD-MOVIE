-- Movie CD Store Management System
-- Lab 01 - Step 5.3: Data Definition Language (DDL)
-- Intended for MySQL 8.0.16+ (CHECK constraints are enforced).
-- Run once on a new, empty MovieCDStore database.

CREATE DATABASE IF NOT EXISTS MovieCDStore
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE MovieCDStore;

-- 1. Superclass: PERSON
CREATE TABLE PERSON (
    MaPerson INT NOT NULL,
    HoTen VARCHAR(100) NOT NULL,
    NgaySinh DATE NULL,
    GioiTinh VARCHAR(10) NULL,
    SoDienThoai VARCHAR(15) NULL,
    Email VARCHAR(100) NULL,
    DiaChi VARCHAR(255) NULL,
    CONSTRAINT pk_person PRIMARY KEY (MaPerson)
) ENGINE = InnoDB;

-- 2. Subclass: KHACH_HANG (customer)
CREATE TABLE KHACH_HANG (
    MaPerson INT NOT NULL,
    NgayDangKy DATE NULL,
    DiemTichLuy INT NOT NULL DEFAULT 0,
    CONSTRAINT pk_khach_hang PRIMARY KEY (MaPerson),
    CONSTRAINT fk_khach_hang_person FOREIGN KEY (MaPerson)
        REFERENCES PERSON (MaPerson),
    CONSTRAINT ck_khach_hang_diem CHECK (DiemTichLuy >= 0)
) ENGINE = InnoDB;

-- 3. Subclass: NHAN_VIEN (employee)
-- The FK from MaQuanLy to QUAN_LY will be added after QUAN_LY exists.
CREATE TABLE NHAN_VIEN (
    MaPerson INT NOT NULL,
    NgayVaoLam DATE NULL,
    TrangThaiLamViec VARCHAR(20) NOT NULL,
    MaQuanLy INT NULL,
    CONSTRAINT pk_nhan_vien PRIMARY KEY (MaPerson),
    CONSTRAINT fk_nhan_vien_person FOREIGN KEY (MaPerson)
        REFERENCES PERSON (MaPerson),
    CONSTRAINT ck_nhan_vien_khong_tu_quan_ly
        CHECK (MaQuanLy IS NULL OR MaQuanLy <> MaPerson)
) ENGINE = InnoDB;

-- 4. Subclass: part-time employee
CREATE TABLE NHAN_VIEN_PART_TIME (
    MaPerson INT NOT NULL,
    LuongTheoGio DECIMAL(12,2) NULL,
    SoGioToiDaTuan INT NULL,
    CONSTRAINT pk_nhan_vien_part_time PRIMARY KEY (MaPerson),
    CONSTRAINT fk_part_time_nhan_vien FOREIGN KEY (MaPerson)
        REFERENCES NHAN_VIEN (MaPerson)
) ENGINE = InnoDB;

-- 5. Subclass: full-time employee
CREATE TABLE NHAN_VIEN_FULL_TIME (
    MaPerson INT NOT NULL,
    LuongThang DECIMAL(12,2) NULL,
    SoNgayPhep INT NULL,
    CONSTRAINT pk_nhan_vien_full_time PRIMARY KEY (MaPerson),
    CONSTRAINT fk_full_time_nhan_vien FOREIGN KEY (MaPerson)
        REFERENCES NHAN_VIEN (MaPerson)
) ENGINE = InnoDB;

-- 6. Subclass: manager, necessarily a full-time employee
CREATE TABLE QUAN_LY (
    MaPerson INT NOT NULL,
    NgayBoNhiem DATE NULL,
    PhuCapQuanLy DECIMAL(12,2) NULL,
    CONSTRAINT pk_quan_ly PRIMARY KEY (MaPerson),
    CONSTRAINT fk_quan_ly_full_time FOREIGN KEY (MaPerson)
        REFERENCES NHAN_VIEN_FULL_TIME (MaPerson)
) ENGINE = InnoDB;

-- 7. Movies
CREATE TABLE PHIM (
    MaPhim INT NOT NULL,
    TenPhim VARCHAR(200) NOT NULL,
    NamPhatHanh INT NULL,
    DaoDien VARCHAR(100) NULL,
    ThoiLuong INT NULL,
    MoTa TEXT NULL,
    CONSTRAINT pk_phim PRIMARY KEY (MaPhim)
) ENGINE = InnoDB;

-- 8. Movie genres
CREATE TABLE THE_LOAI (
    MaTheLoai INT NOT NULL,
    TenTheLoai VARCHAR(100) NOT NULL,
    MoTa TEXT NULL,
    CONSTRAINT pk_the_loai PRIMARY KEY (MaTheLoai),
    CONSTRAINT uq_the_loai_ten UNIQUE (TenTheLoai)
) ENGINE = InnoDB;

-- 9. CD product/edition for each film
CREATE TABLE DIA_CD (
    MaDia INT NOT NULL,
    MaPhim INT NOT NULL,
    PhienBan VARCHAR(60) NULL,
    GiaBan DECIMAL(12,2) NOT NULL,
    SoLuongTon INT NOT NULL DEFAULT 0,
    CONSTRAINT pk_dia_cd PRIMARY KEY (MaDia),
    CONSTRAINT fk_dia_cd_phim FOREIGN KEY (MaPhim)
        REFERENCES PHIM (MaPhim),
    CONSTRAINT ck_dia_cd_gia CHECK (GiaBan > 0),
    CONSTRAINT ck_dia_cd_ton CHECK (SoLuongTon >= 0)
) ENGINE = InnoDB;

-- 10. Sales invoice
CREATE TABLE HOA_DON (
    MaHD INT NOT NULL,
    MaKhachHang INT NOT NULL,
    MaNhanVien INT NOT NULL,
    NgayLap DATETIME NOT NULL,
    TrangThai VARCHAR(30) NOT NULL,
    CONSTRAINT pk_hoa_don PRIMARY KEY (MaHD),
    CONSTRAINT fk_hoa_don_khach_hang FOREIGN KEY (MaKhachHang)
        REFERENCES KHACH_HANG (MaPerson),
    CONSTRAINT fk_hoa_don_nhan_vien FOREIGN KEY (MaNhanVien)
        REFERENCES NHAN_VIEN (MaPerson)
) ENGINE = InnoDB;

-- 11. Invoice lines (composite primary key)
CREATE TABLE CHI_TIET_HOA_DON (
    MaHD INT NOT NULL,
    MaDia INT NOT NULL,
    SoLuong INT NOT NULL,
    DonGiaBan DECIMAL(12,2) NOT NULL,
    CONSTRAINT pk_chi_tiet_hoa_don PRIMARY KEY (MaHD, MaDia),
    CONSTRAINT fk_cthd_hoa_don FOREIGN KEY (MaHD)
        REFERENCES HOA_DON (MaHD),
    CONSTRAINT fk_cthd_dia_cd FOREIGN KEY (MaDia)
        REFERENCES DIA_CD (MaDia),
    CONSTRAINT ck_cthd_so_luong CHECK (SoLuong > 0)
) ENGINE = InnoDB;

-- 12. Many-to-many relation: PHIM - THE_LOAI
CREATE TABLE PHIM_THE_LOAI (
    MaPhim INT NOT NULL,
    MaTheLoai INT NOT NULL,
    CONSTRAINT pk_phim_the_loai PRIMARY KEY (MaPhim, MaTheLoai),
    CONSTRAINT fk_phim_the_loai_phim FOREIGN KEY (MaPhim)
        REFERENCES PHIM (MaPhim),
    CONSTRAINT fk_phim_the_loai_the_loai FOREIGN KEY (MaTheLoai)
        REFERENCES THE_LOAI (MaTheLoai)
) ENGINE = InnoDB;

-- Finish the circular reference NHAN_VIEN -> QUAN_LY.
ALTER TABLE NHAN_VIEN
    ADD CONSTRAINT fk_nhan_vien_quan_ly
    FOREIGN KEY (MaQuanLy) REFERENCES QUAN_LY (MaPerson);

-- Read-only verification commands.
SHOW TABLES;
SHOW CREATE TABLE NHAN_VIEN;
SHOW CREATE TABLE QUAN_LY;
