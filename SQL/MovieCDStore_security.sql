-- MOVIE CD STORE - Lab 02 A.6
-- MySQL 8.4 / run as root on port 3307, after schema and routines.
-- Run once on a new set of accounts/roles. No real passwords in this file.
-- Run CREATE USER separately first and securely save the generated passwords.
USE MovieCDStore;

-- 1. Accounts: use TCP 127.0.0.1; save the generated passwords privately.
CREATE USER
    'cd_admin'@'127.0.0.1' IDENTIFIED BY RANDOM PASSWORD,
    'cd_manager'@'127.0.0.1' IDENTIFIED BY RANDOM PASSWORD,
    'cd_sales'@'127.0.0.1' IDENTIFIED BY RANDOM PASSWORD,
    'cd_viewer'@'127.0.0.1' IDENTIFIED BY RANDOM PASSWORD;

-- 2. Roles (roles are locked by default; login using user accounts).
CREATE ROLE 'role_cd_admin', 'role_cd_manager',
            'role_cd_sales', 'role_cd_viewer';

-- 3. Limited customer view, created by the administrator.
CREATE OR REPLACE SQL SECURITY DEFINER VIEW vw_KhachHangBanHang AS
SELECT k.MaPerson, p.HoTen
FROM KHACH_HANG AS k
JOIN PERSON AS p ON p.MaPerson = k.MaPerson;

-- 4. Database administrator: scope is MovieCDStore, not the whole server.
GRANT ALL PRIVILEGES ON MovieCDStore.* TO 'role_cd_admin';

-- 5. Manager: read all store data, edit only product price and stock,
--    calculate invoice totals and view revenue reports.
GRANT SELECT ON MovieCDStore.* TO 'role_cd_manager';
GRANT UPDATE (GiaBan, SoLuongTon) ON MovieCDStore.DIA_CD TO 'role_cd_manager';
GRANT EXECUTE ON PROCEDURE MovieCDStore.sp_ThongKeDoanhThu TO 'role_cd_manager';
GRANT EXECUTE ON FUNCTION MovieCDStore.fn_TinhTongTienHoaDon TO 'role_cd_manager';

-- 6. Sales: catalog and limited customer view, no direct table writes.
GRANT SELECT ON MovieCDStore.PHIM TO 'role_cd_sales';
GRANT SELECT ON MovieCDStore.THE_LOAI TO 'role_cd_sales';
GRANT SELECT ON MovieCDStore.PHIM_THE_LOAI TO 'role_cd_sales';
GRANT SELECT ON MovieCDStore.DIA_CD TO 'role_cd_sales';
GRANT SELECT ON MovieCDStore.vw_KhachHangBanHang TO 'role_cd_sales';
GRANT EXECUTE ON PROCEDURE MovieCDStore.sp_TaoHoaDon TO 'role_cd_sales';
GRANT EXECUTE ON PROCEDURE MovieCDStore.sp_ThemChiTietHoaDon TO 'role_cd_sales';
GRANT EXECUTE ON PROCEDURE MovieCDStore.sp_HoanTatHoaDon TO 'role_cd_sales';
GRANT EXECUTE ON FUNCTION MovieCDStore.fn_TinhTongTienHoaDon TO 'role_cd_sales';

-- 7. Viewer: catalog only.
GRANT SELECT ON MovieCDStore.PHIM TO 'role_cd_viewer';
GRANT SELECT ON MovieCDStore.THE_LOAI TO 'role_cd_viewer';
GRANT SELECT ON MovieCDStore.PHIM_THE_LOAI TO 'role_cd_viewer';
GRANT SELECT ON MovieCDStore.DIA_CD TO 'role_cd_viewer';

-- 8. Assign roles and enable them by default for new sessions.
GRANT 'role_cd_admin' TO 'cd_admin'@'127.0.0.1';
GRANT 'role_cd_manager' TO 'cd_manager'@'127.0.0.1';
GRANT 'role_cd_sales' TO 'cd_sales'@'127.0.0.1';
GRANT 'role_cd_viewer' TO 'cd_viewer'@'127.0.0.1';
SET DEFAULT ROLE 'role_cd_admin' TO 'cd_admin'@'127.0.0.1';
SET DEFAULT ROLE 'role_cd_manager' TO 'cd_manager'@'127.0.0.1';
SET DEFAULT ROLE 'role_cd_sales' TO 'cd_sales'@'127.0.0.1';
SET DEFAULT ROLE 'role_cd_viewer' TO 'cd_viewer'@'127.0.0.1';

-- 9. Verify effective grants (run as root; does not expose passwords).
SHOW GRANTS FOR 'cd_admin'@'127.0.0.1' USING 'role_cd_admin';
SHOW GRANTS FOR 'cd_manager'@'127.0.0.1' USING 'role_cd_manager';
SHOW GRANTS FOR 'cd_sales'@'127.0.0.1' USING 'role_cd_sales';
SHOW GRANTS FOR 'cd_viewer'@'127.0.0.1' USING 'role_cd_viewer';

-- Optional REVOKE demonstration, as root (uncomment BOTH to restore final policy):
-- REVOKE SELECT ON MovieCDStore.PHIM_THE_LOAI FROM 'role_cd_viewer';
-- GRANT SELECT ON MovieCDStore.PHIM_THE_LOAI TO 'role_cd_viewer';

-- If a generated password was not saved, reset ONLY that account as root:
-- ALTER USER 'cd_sales'@'127.0.0.1' IDENTIFIED BY RANDOM PASSWORD;
-- Do not re-run schema or routines unnecessarily. If routines are dropped and
-- recreated, verify and reapply routine-specific EXECUTE grants if needed.
-- Limitations: this is a lab RBAC setup, not row-level access control.
-- sp_TaoHoaDon accepts an employee ID from the caller; the application must
-- bind that ID to the authenticated employee to prevent impersonation.
