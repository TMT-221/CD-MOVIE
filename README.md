
# Movie CD Store Management System

## Project Information

- Course: INT1313 - Database Systems
- Project: Movie CD Store Management System
- DBMS: MySQL
- Database: MovieCDStore

## Description

Database system for managing a movie CD store,
including movies, genres, CD inventory,
customers, employees, managers and invoices.

## Database Design

The database contains 12 relational tables.

The EER model includes:
- PERSON superclass
- KHACH_HANG and NHAN_VIEN subclasses
- PART_TIME and FULL_TIME employee subclasses
- QUAN_LY subclass of FULL_TIME

## Project Files

- docs/: Database documentation and diagrams
- diagrams/: Editable EER and DBML files
- sql/: SQL scripts

## SQL Execution Order

1. MovieCDStore_schema.sql
2. MovieCDStore_indexes.sql
3. MovieCDStore_routines.sql
4. MovieCDStore_routines_demo.sql

## Status

Database design and SQL scripts prepared.
Runtime testing on MySQL is pending.
