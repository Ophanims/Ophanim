from simulator.schemas.base import SnapshotModel
class SatelliteSnapshot(SnapshotModel):
    addr: str
    type: str
    # spatial
    id: str
    plane: int
    order: int
    lat: float
    lon: float
    alt: float
    x: float
    y: float
    z: float
    
    # Velocity Vector
    velocity_vector_x: float
    velocity_vector_y: float
    velocity_vector_z: float
    
    # Solar Vector
    solar_vector_x: float
    solar_vector_y: float
    solar_vector_z: float

    # imagery
    cor_lat1: float
    cor_lon1: float
    cor_lat2: float
    cor_lon2: float
    cor_lat3: float
    cor_lon3: float
    cor_lat4: float
    cor_lon4: float
    
    cor_x1: float
    cor_y1: float
    cor_z1: float
    cor_x2: float
    cor_y2: float
    cor_z2: float
    cor_x3: float
    cor_y3: float
    cor_z3: float
    cor_x4: float
    cor_y4: float
    cor_z4: float

    # energy
    battery_percent: float
    processor_clock_frequency_ghz: float

    # indicators
    is_observing: bool
    is_communicating_sgl: bool
    is_processing: bool
    is_communicating_isl: bool
    is_charging: bool
    
    connections: list[str] = []

