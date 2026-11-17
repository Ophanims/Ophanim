"""Each environment owns and closes its logging handlers."""
import logging
from uuid import uuid4
from simulator.settings import SIMULATION_OUTPUT_DIR


class SystemLogger:
    def __init__(self, name: str, level: int = logging.INFO):
        directory = SIMULATION_OUTPUT_DIR / "log"
        directory.mkdir(parents=True, exist_ok=True)
        instance_id = uuid4().hex
        self._logger = logging.Logger(f"{name}.{instance_id}", level)
        handler = logging.FileHandler(directory / f"{name}_{instance_id}.log")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        self._logger.addHandler(handler)

    def debug(self, message, *args, **kwargs):
        self._logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self._logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self._logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self._logger.error(message, *args, **kwargs)

    def close(self):
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)
