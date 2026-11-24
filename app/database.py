"""Reusable connection to MovieCDStore; optional explicit role credentials."""
import os

import mysql.connector


def get_connection(*, user=None, password=None):
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3307")),
        user=user if user is not None else os.getenv("DB_USER", "cd_viewer"),
        password=password if password is not None else os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "MovieCDStore"),
        charset="utf8mb4",
        connection_timeout=10,
        autocommit=False,
    )
