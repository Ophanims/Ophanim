import os
from typing import Optional
from urllib.parse import unquote, urlparse

import pymysql
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectBase(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    timeSlot: Optional[float] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    altitude: Optional[float] = None
    inclination: Optional[float] = None
    planeCount: Optional[int] = None
    constellationSize: Optional[int] = None
    phaseFactor: Optional[float] = None
    imageryWidthPx: Optional[int] = None
    imageryLengthPx: Optional[int] = None
    cameraFocalLengthMm: Optional[float] = None
    cameraSensorUnitLengthUm: Optional[float] = None
    channelsPerPixel: Optional[int] = None
    bitsPerChannel: Optional[int] = None
    processorClockFrequency: Optional[float] = None
    processorCoreQuantity: Optional[int] = None
    processorEnergyFactor: Optional[float] = None
    maxTaskProcessingNumber: Optional[int] = None
    transmitAntennaGain: Optional[float] = None
    receiveAntennaGain: Optional[float] = None
    transmitSignalPower: Optional[float] = None
    maxTaskTransmittingNumber: Optional[int] = None
    batteryCapacity: Optional[float] = None
    solarPanelArea: Optional[float] = None
    solarPanelEfficiency: Optional[float] = None
    dynamicPowerComputing: Optional[float] = None
    dynamicPowerTransmitting: Optional[float] = None
    staticPowerComputing: Optional[float] = None
    staticPowerTransmitting: Optional[float] = None
    staticPowerOthers: Optional[float] = None
    stationTransmitAntennaGain: Optional[float] = None
    stationReceiveAntennaGain: Optional[float] = None
    stationTransmitSignalPower: Optional[float] = None
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[str] = Field(default=None, max_length=50)


class ProjectCreate(ProjectBase):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    status: str = Field(default="active", max_length=50)


class ProjectUpdate(ProjectBase):
    pass


class GroundStationBase(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None


class GroundStationCreate(GroundStationBase):
    name: str = Field(min_length=1, max_length=120)
    latitude: float
    longitude: float
    altitude: float = 0.0


class GroundStationUpdate(GroundStationBase):
    pass


PROJECT_FIELDS = [
    "name",
    "timeSlot", "startTime", "endTime",
    "altitude", "inclination", "planeCount", "constellationSize", "phaseFactor",
    "imageryWidthPx", "imageryLengthPx", "cameraFocalLengthMm", "cameraSensorUnitLengthUm", "channelsPerPixel", "bitsPerChannel",
    "processorClockFrequency", "processorCoreQuantity", "processorEnergyFactor", "maxTaskProcessingNumber",
    "transmitAntennaGain", "receiveAntennaGain", "transmitSignalPower", "maxTaskTransmittingNumber",
    "batteryCapacity", "solarPanelArea", "solarPanelEfficiency", "dynamicPowerComputing", "dynamicPowerTransmitting", "staticPowerComputing", "staticPowerTransmitting", "staticPowerOthers",
    "stationTransmitAntennaGain", "stationReceiveAntennaGain", "stationTransmitSignalPower",
    "description", "status",
]

PROJECT_COLUMN_DEFINITIONS = {
    "timeSlot": "DOUBLE NULL",
    "startTime": "DATETIME NULL",
    "endTime": "DATETIME NULL",
    "altitude": "DOUBLE NULL",
    "inclination": "DOUBLE NULL",
    "planeCount": "INT NULL",
    "constellationSize": "INT NULL",
    "phaseFactor": "DOUBLE NULL",
    "imageryWidthPx": "INT NULL",
    "imageryLengthPx": "INT NULL",
    "cameraFocalLengthMm": "DOUBLE NULL",
    "cameraSensorUnitLengthUm": "DOUBLE NULL",
    "channelsPerPixel": "INT NULL",
    "bitsPerChannel": "INT NULL",
    "processorClockFrequency": "DOUBLE NULL",
    "processorCoreQuantity": "INT NULL",
    "processorEnergyFactor": "DOUBLE NULL",
    "maxTaskProcessingNumber": "INT NULL",
    "transmitAntennaGain": "DOUBLE NULL",
    "receiveAntennaGain": "DOUBLE NULL",
    "transmitSignalPower": "DOUBLE NULL",
    "maxTaskTransmittingNumber": "INT NULL",
    "batteryCapacity": "DOUBLE NULL",
    "solarPanelArea": "DOUBLE NULL",
    "solarPanelEfficiency": "DOUBLE NULL",
    "dynamicPowerComputing": "DOUBLE NULL",
    "dynamicPowerTransmitting": "DOUBLE NULL",
    "staticPowerComputing": "DOUBLE NULL",
    "staticPowerTransmitting": "DOUBLE NULL",
    "staticPowerOthers": "DOUBLE NULL",
    "stationTransmitAntennaGain": "DOUBLE NULL",
    "stationReceiveAntennaGain": "DOUBLE NULL",
    "stationTransmitSignalPower": "DOUBLE NULL",
}


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


def ensure_projects_table():
    sql = """
    CREATE TABLE IF NOT EXISTS projects (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(120) NOT NULL,
        description TEXT NULL,
        status VARCHAR(50) NOT NULL DEFAULT 'active',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            cursor.execute("SELECT DATABASE() AS db_name")
            db_name = cursor.fetchone()["db_name"]
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'projects'
                """,
                (db_name,),
            )
            existing_columns = {row["COLUMN_NAME"] for row in cursor.fetchall()}
            for column_name, column_type in PROJECT_COLUMN_DEFINITIONS.items():
                if column_name not in existing_columns:
                    cursor.execute(
                        f"ALTER TABLE projects ADD COLUMN `{column_name}` {column_type}"
                    )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ground_stations (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    project_id BIGINT NOT NULL,
                    name VARCHAR(120) NOT NULL,
                    latitude DOUBLE NOT NULL,
                    longitude DOUBLE NOT NULL,
                    altitude DOUBLE NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    CONSTRAINT fk_ground_station_project
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                        ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )

            cursor.execute(
                """
                SELECT rc.CONSTRAINT_NAME, rc.DELETE_RULE
                FROM information_schema.REFERENTIAL_CONSTRAINTS rc
                WHERE rc.CONSTRAINT_SCHEMA = %s
                  AND rc.TABLE_NAME = 'ground_stations'
                  AND rc.REFERENCED_TABLE_NAME = 'projects'
                """,
                (db_name,),
            )
            fk_row = cursor.fetchone()

            if fk_row is None:
                cursor.execute(
                    """
                    ALTER TABLE ground_stations
                    ADD CONSTRAINT fk_ground_station_project
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                    ON DELETE CASCADE
                    """
                )
            elif fk_row.get("DELETE_RULE") != "CASCADE":
                fk_name = fk_row["CONSTRAINT_NAME"]
                cursor.execute(
                    f"ALTER TABLE ground_stations DROP FOREIGN KEY `{fk_name}`"
                )
                cursor.execute(
                    """
                    ALTER TABLE ground_stations
                    ADD CONSTRAINT fk_ground_station_project
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                    ON DELETE CASCADE
                    """
                )


def project_select_fields() -> str:
    columns = ["id"] + PROJECT_FIELDS + ["created_at", "updated_at"]
    return ", ".join([f"`{col}`" for col in columns])


def fetch_project_by_id(cursor, project_id: int):
    cursor.execute(
        f"SELECT {project_select_fields()} FROM projects WHERE id = %s",
        (project_id,),
    )
    return cursor.fetchone()


@router.get("")
def list_projects():
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT {project_select_fields()}
                FROM projects
                ORDER BY updated_at DESC, id DESC
                """
            )
            return cursor.fetchall()


@router.get("/{project_id}")
def get_project(project_id: int):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            row = fetch_project_by_id(cursor, project_id)
            if not row:
                raise HTTPException(status_code=404, detail="Project not found")
            return row


@router.post("", status_code=201)
def create_project(payload: ProjectCreate):
    data = payload.model_dump()
    insert_columns = PROJECT_FIELDS
    insert_values = [data.get(col) for col in insert_columns]

    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO projects ({', '.join([f'`{c}`' for c in insert_columns])}) VALUES ({', '.join(['%s'] * len(insert_columns))})",
                tuple(insert_values),
            )
            project_id = cursor.lastrowid
            return fetch_project_by_id(cursor, project_id)


@router.put("/{project_id}")
def update_project(project_id: int, payload: ProjectUpdate):
    payload_data = payload.model_dump(exclude_unset=True)
    fields = [field for field in PROJECT_FIELDS if field in payload_data]
    values = [payload_data[field] for field in fields]

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(project_id)
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"UPDATE projects SET {', '.join([f'`{field}` = %s' for field in fields])} WHERE id = %s",
                tuple(values),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Project not found")
            return fetch_project_by_id(cursor, project_id)


@router.delete("/{project_id}")
def delete_project(project_id: int):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Project not found")
            return {"deleted": True, "project_id": project_id}


@router.get("/{project_id}/ground-stations")
def list_ground_stations(project_id: int):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            if not fetch_project_by_id(cursor, project_id):
                raise HTTPException(status_code=404, detail="Project not found")
            cursor.execute(
                """
                SELECT id, project_id, name, latitude, longitude, altitude, created_at, updated_at
                FROM ground_stations
                WHERE project_id = %s
                ORDER BY id DESC
                """,
                (project_id,),
            )
            return cursor.fetchall()


@router.post("/{project_id}/ground-stations", status_code=201)
def create_ground_station(project_id: int, payload: GroundStationCreate):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            if not fetch_project_by_id(cursor, project_id):
                raise HTTPException(status_code=404, detail="Project not found")
            cursor.execute(
                """
                INSERT INTO ground_stations (project_id, name, latitude, longitude, altitude)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    project_id,
                    payload.name,
                    payload.latitude,
                    payload.longitude,
                    payload.altitude,
                ),
            )
            station_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT id, project_id, name, latitude, longitude, altitude, created_at, updated_at
                FROM ground_stations
                WHERE id = %s
                """,
                (station_id,),
            )
            return cursor.fetchone()


@router.put("/{project_id}/ground-stations/{station_id}")
def update_ground_station(project_id: int, station_id: int, payload: GroundStationUpdate):
    payload_data = payload.model_dump(exclude_unset=True)
    fields = [field for field in ["name", "latitude", "longitude", "altitude"] if field in payload_data]
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values = [payload_data[field] for field in fields]
    values.extend([project_id, station_id])

    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            if not fetch_project_by_id(cursor, project_id):
                raise HTTPException(status_code=404, detail="Project not found")
            cursor.execute(
                f"""
                UPDATE ground_stations
                SET {', '.join([f'`{field}` = %s' for field in fields])}
                WHERE project_id = %s AND id = %s
                """,
                tuple(values),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Ground station not found")
            cursor.execute(
                """
                SELECT id, project_id, name, latitude, longitude, altitude, created_at, updated_at
                FROM ground_stations
                WHERE id = %s
                """,
                (station_id,),
            )
            return cursor.fetchone()


@router.delete("/{project_id}/ground-stations/{station_id}")
def delete_ground_station(project_id: int, station_id: int):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            if not fetch_project_by_id(cursor, project_id):
                raise HTTPException(status_code=404, detail="Project not found")
            cursor.execute(
                "DELETE FROM ground_stations WHERE project_id = %s AND id = %s",
                (project_id, station_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Ground station not found")
            return {"deleted": True, "project_id": project_id, "station_id": station_id}
