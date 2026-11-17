"""Normalize project identities and derive Walker constellation geometry."""
from uuid import uuid4
from simulator.schemas.project import Project
from simulator.schemas.satellite import SatelliteConfig
from simulator.models.constellation_model import ConstellationModel


def detect_update(project: Project) -> Project:
    project = project.snapshot()
    project.project_id = project.project_id or uuid4().hex
    project.constellation.id = project.constellation.id or uuid4().hex
    for child in [project.constellation, project.hardware, project.experiment,
                  *project.ground_stations, *project.rois, *project.experiment.missions]:
        child.project_id = project.project_id
        child.id = child.id or uuid4().hex
    constellation = ConstellationModel.from_dict(project.constellation)
    project.satellites = [SatelliteConfig(
        id=satellite.id, constellation_id=project.constellation.id,
        name=satellite.motion.name, order=satellite.order, plane=satellite.plane,
        tle1=satellite.tle1text, tle2=satellite.tle2text,
    ) for satellite in constellation.satellites]
    if constellation.satellites:
        project.constellation.orbital_period = constellation.satellites[0].op
    return project
