"""Optional one-time import from existing MySQL/Timescale databases; never runs at app startup."""
import asyncio
import os
from urllib.parse import quote
from run_backend import load_environment


def main():
    load_environment()
    encode = lambda key: quote(os.environ[key], safe="")
    if "MYSQL_URL" not in os.environ:
        os.environ["MYSQL_URL"] = f"mysql+pymysql://{encode('MYSQL_USER')}:{encode('MYSQL_PASSWORD')}@127.0.0.1:{os.environ.get('MYSQL_PORT', '3306')}/{encode('MYSQL_DATABASE')}"
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = f"postgresql://{encode('DB_USER')}:{encode('DB_PASSWORD')}@127.0.0.1:{os.environ.get('DB_PORT', '15432')}/{encode('DB_NAME')}"
    from persistence.schema_bootstrap import ensure_projects_table, ensure_record_schema
    from simulator.services.project_migration import migrate_ophanim_projects
    from simulator.services.record_migration import migrate_ophanim_records
    ensure_projects_table()
    print(f"Imported projects: {migrate_ophanim_projects()}")
    asyncio.run(ensure_record_schema())
    print(f"Imported records: {migrate_ophanim_records()}")


if __name__ == "__main__":
    main()
