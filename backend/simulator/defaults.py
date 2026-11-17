"""Single source for the new-project template and reproducible test fixtures."""
from simulator.schemas.project import Project
from simulator.schemas.hardware import Hardware


def default_project() -> Project:
    hardware = Hardware(id="", project_id="").serialize()
    return Project.model_validate({
        "project_id": "", "algorithm": "ophanim", "user_id": "local", "title": "Untitled", "description": "",
        "hardware": hardware,
        "experiment": {"id": "", "project_id": "", "start_time": "2025-12-01T00:00:00+00:00",
                       "end_time": "2025-12-01T02:00:00+00:00", "time_slot": 30, "missions": []},
        "constellation": {"id": "", "project_id": "", "name": "Untitled", "description": "",
                          "number_of_planes": 1, "number_of_sat_per_planes": 1,
                          "phase_factor": 0, "altitude": 600000, "inclination": 90},
        "satellites": [], "ground_stations": [], "rois": [],
    })
