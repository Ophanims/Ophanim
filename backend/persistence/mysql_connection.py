import os
from urllib.parse import unquote, urlparse
import pymysql

def _mysql_config_from_env() -> dict:
    mysql_url = os.getenv("MYSQL_URL", "").strip()
    if mysql_url:
        parsed = urlparse(mysql_url)
        return {
            "host": parsed.hostname or "mysql",
            "port": parsed.port or 3306,
            "user": unquote(parsed.username or "root"),
            "password": unquote(parsed.password or ""),
            "database": (parsed.path or "/").lstrip("/") or os.getenv("MYSQL_DATABASE", "config_db"),
        }

    return {
        "host": os.getenv("MYSQL_HOST", "mysql"),
        "port": int(os.getenv("MYSQL_PORT_INTERNAL", "3306")),
        "user": os.getenv("MYSQL_USER", "mysql_admin"),
        "password": os.getenv("MYSQL_PASSWORD", "mysql_password"),
        "database": os.getenv("MYSQL_DATABASE", "mysql_db"),
    }


def get_mysql_conn():
    cfg = _mysql_config_from_env()
    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


