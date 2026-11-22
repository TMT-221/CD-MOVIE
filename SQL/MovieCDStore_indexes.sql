-- Movie CD Store Management System
-- Lab 01 - Step 5.4: Index Documentation / supplemental indexes
-- Prerequisite: Execute MovieCDStore_schema.sql first.
-- Run the CREATE INDEX statements only once.
USE MovieCDStore;

-- Search film titles, e.g. WHERE TenPhim LIKE 'Avengers%'
CREATE INDEX idx_phim_tenphim
ON PHIM (TenPhim);

-- Filter invoices by date/time ranges, e.g. monthly sales reports
CREATE INDEX idx_hoadon_ngaylap
ON HOA_DON (NgayLap);

-- Exact phone-number searches for a person
CREATE INDEX idx_person_sodienthoai
ON PERSON (SoDienThoai);

-- Inspect indexes actually present in the database, including
-- PRIMARY, UNIQUE, and indexes required by foreign keys.
SELECT TABLE_NAME, INDEX_NAME,
       GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX SEPARATOR ', ') AS IndexedColumns,
       INDEX_TYPE, NON_UNIQUE
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'MovieCDStore'
GROUP BY TABLE_NAME, INDEX_NAME, INDEX_TYPE, NON_UNIQUE
ORDER BY TABLE_NAME, INDEX_NAME;

-- Optional: inspect whether MySQL considers an index for a prefix title search.
EXPLAIN SELECT MaPhim, TenPhim
FROM PHIM
WHERE TenPhim LIKE 'Avengers%';
