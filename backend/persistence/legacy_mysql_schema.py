"""v0 database bootstrap for one-way migration; no project API is exposed here.
Remove this module after all installations have migrated their v0 databases.
"""
PROJECT_COLUMN_DEFINITIONS = {
    "timeSlot": "DOUBLE NULL",
    "startTime": "DATETIME NULL",
    "endTime": "DATETIME NULL",
    "seed": "BIGINT NULL",
    "altitude": "DOUBLE NULL",
    "inclination": "DOUBLE NULL",
    "maximumNumberOfPlane": "INT NULL",
    "sizeOfConstellation": "INT NULL",
    "phaseFactor": "DOUBLE NULL",
    "imageryWidthPx": "INT NULL",
    "imageryHeightPx": "INT NULL",
    "lengthOfCameraFocalMm": "DOUBLE NULL",
    "lengthOfCameraSensorUnitUm": "DOUBLE NULL",
    "channelsPerPixel": "INT NULL",
    "bitsPerChannelBit": "INT NULL",
    "maximumNumberOfProcessorCore": "INT NULL",
    "factorOfComputationEnergy": "DOUBLE NULL",
    "maximumConcurrentComputation": "INT NULL",
    "maximumClockFrequencyGhz": "DOUBLE NULL",
    "carrierFrequencyOfIslGhz": "DOUBLE NULL",
    "carrierFrequencyOfUpGhz": "DOUBLE NULL",
    "carrierFrequencyOfDlGhz": "DOUBLE NULL",
    "bandwidthOfIslMhz": "DOUBLE NULL",
    "bandwidthOfUlMhz": "DOUBLE NULL",
    "bandwidthOfDlMhz": "DOUBLE NULL",
    "factorOfTransmissionEnergy": "DOUBLE NULL",
    "efficiencyOfTargetSpectrum": "DOUBLE NULL",
    "antennaGainOfIslTransmitDbi": "DOUBLE NULL",
    "antennaGainOfIslReceiveDbi": "DOUBLE NULL",
    "antennaGainOfUlTransmitDbi": "DOUBLE NULL",
    "antennaGainOfUlReceiveDbi": "DOUBLE NULL",
    "antennaGainOfDlTransmitDbi": "DOUBLE NULL",
    "antennaGainOfDlReceiveDbi": "DOUBLE NULL",
    "maximumConcurrentTransmission": "INT NULL",
    "batteryCapacityWh": "DOUBLE NULL",
    "areaOfSolarPanelM2": "DOUBLE NULL",
    "efficiencyOfSolarPanel": "DOUBLE NULL",
    "efficiencyOfPowerAmplifier": "DOUBLE NULL",
    "staticPowerOfProcessingW": "DOUBLE NULL",
    "staticPowerOfIslTransmittingW": "DOUBLE NULL",
    "staticPowerOfUplinkTransmittingW": "DOUBLE NULL",
    "staticPowerOfDownlinkTransmittingW": "DOUBLE NULL",
    "staticPowerOfOthersW": "DOUBLE NULL",
}

LEGACY_TO_NEW_COLUMN_MAPPINGS = [
    ("planeCount", "maximumNumberOfPlane"),
    ("constellationSize", "sizeOfConstellation"),
    ("imageryLengthPx", "imageryHeightPx"),
    ("cameraFocalLengthMm", "lengthOfCameraFocalMm"),
    ("cameraSensorUnitLengthUm", "lengthOfCameraSensorUnitUm"),
    ("bitsPerChannel", "bitsPerChannelBit"),
    ("processorCoreQuantity", "maximumNumberOfProcessorCore"),
    ("processorEnergyFactor", "factorOfComputationEnergy"),
    ("maxTaskProcessingNumber", "maximumConcurrentComputation"),
    ("processorClockFrequency", "maximumClockFrequencyGhz"),
    ("transmitAntennaGain", "antennaGainOfIslTransmitDbi"),
    ("receiveAntennaGain", "antennaGainOfIslReceiveDbi"),
    ("transmitSignalPower", "factorOfTransmissionEnergy"),
    ("maxTaskTransmittingNumber", "maximumConcurrentTransmission"),
    ("batteryCapacity", "batteryCapacityWh"),
    ("solarPanelArea", "areaOfSolarPanelM2"),
    ("solarPanelEfficiency", "efficiencyOfSolarPanel"),
    ("dynamicPowerComputing", "efficiencyOfPowerAmplifier"),
    ("dynamicPowerTransmitting", "efficiencyOfTargetSpectrum"),
    ("staticPowerComputing", "staticPowerOfProcessingW"),
    ("staticPowerTransmitting", "staticPowerOfIslTransmittingW"),
    ("staticPowerOthers", "staticPowerOfOthersW"),
    ("frequencyBand", "carrierFrequencyOfIslGhz"),
    ("bandwidthMhz", "bandwidthOfIslMhz"),
    ("stationTransmitAntennaGain", "antennaGainOfUlTransmitDbi"),
    ("stationReceiveAntennaGain", "antennaGainOfDlReceiveDbi"),
    ("antennaGainOfUplinkTransmitDbi", "antennaGainOfUlTransmitDbi"),
    ("antennaGainOfDownlinkReceiveDbi", "antennaGainOfDlReceiveDbi"),
]


from persistence.mysql_connection import get_mysql_conn


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

            # Backfill new columns from legacy columns for existing rows.
            for legacy_col, new_col in LEGACY_TO_NEW_COLUMN_MAPPINGS:
                if legacy_col in existing_columns and new_col in PROJECT_COLUMN_DEFINITIONS:
                    cursor.execute(
                        f"UPDATE projects SET `{new_col}` = `{legacy_col}` WHERE `{new_col}` IS NULL AND `{legacy_col}` IS NOT NULL"
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

