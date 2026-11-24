"""Lab 02 B.2: verify a real MySQL connection and close it."""
import mysql.connector

from database import get_connection


def main():
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION(), @@port, DATABASE(), CURRENT_USER(), CURRENT_ROLE()")
        version, port, database, user, role = cursor.fetchone()
        print(f"MySQL version: {version}")
        print(f"Port: {port}")
        print(f"Database: {database}")
        print(f"User: {user}")
        print(f"Role: {role}")
        cursor.execute("SELECT COUNT(*) FROM PHIM")
        (count,) = cursor.fetchone()
        print(f"Movies: {count}")
        if not version.startswith("8.4.") or database.lower() != "moviecdstore":
            raise RuntimeError("Unexpected server or database")
        if not user.startswith("cd_viewer@") or "role_cd_viewer" not in role:
            raise RuntimeError("Expected cd_viewer with its active role")
        if count == 0:
            raise RuntimeError("Movie catalog is empty")
        print("Connection test: PASS")
    except (mysql.connector.Error, KeyError, ValueError, RuntimeError) as exc:
        print(f"Connection test: FAIL ({exc})")
        raise SystemExit(1) from exc
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if connection is not None:
                connection.close()
                print("Connection closed")


if __name__ == "__main__":
    main()
