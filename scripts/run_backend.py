"""Run the shared API locally with this repository's virtual environment."""
import argparse
import os
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def load_environment() -> None:
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
    encode = lambda key: quote(os.environ[key], safe="")
    os.environ.setdefault("DATABASE_URL", f"postgresql://{encode('DB_USER')}:{encode('DB_PASSWORD')}@127.0.0.1:{os.environ.get('DB_PORT', '15432')}/{encode('DB_NAME')}")
    os.environ.setdefault("MYSQL_URL", f"mysql+pymysql://{encode('MYSQL_USER')}:{encode('MYSQL_PASSWORD')}@127.0.0.1:{os.environ.get('MYSQL_PORT', '3306')}/{encode('MYSQL_DATABASE')}")


if __name__ == "__main__":
    load_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=int(os.environ.get("BACKEND_PORT", "8000")))
    parser.add_argument("--reload", action="store_true")
    arguments = parser.parse_args()
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=arguments.port, reload=arguments.reload)
