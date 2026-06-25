import type { EarthPoint, LinkPoint, SatellitePoint, StationPoint, SunPoint } from "@/app/simulation/[projectId]/simulation.model";

export type RecordSeriesEntityPoint = {
  slot_count: number;
  entity_id: string;
  entity_type?: string;
  payload?: {
    id?: string;
    type?: string;
    plane?: number;
    order?: number;
    x?: number;
    y?: number;
    z?: number;
    velocityVectorX?: number;
    velocityVectorY?: number;
    velocityVectorZ?: number;
    solarVectorX?: number;
    solarVectorY?: number;
    solarVectorZ?: number;
    corLat1?: number;
    corLon1?: number;
    corLat2?: number;
    corLon2?: number;
    corLat3?: number;
    corLon3?: number;
    corLat4?: number;
    corLon4?: number;
    corX1?: number;
    corY1?: number;
    corZ1?: number;
    corX2?: number;
    corY2?: number;
    corZ2?: number;
    corX3?: number;
    corY3?: number;
    corZ3?: number;
    corX4?: number;
    corY4?: number;
    corZ4?: number;
    batteryLevel?: number;
    processorClockFrequency?: number;
    onROI?: boolean;
    onSUN?: boolean;
    onSGL?: boolean;
    onISL?: boolean;
    onCOM?: boolean;
    addr?: string;
    null_island_x?: number;
    null_island_y?: number;
    null_island_z?: number;
    rotational_angular_velocity?: number;
  };
};

export type RecordSeriesPayload = {
  record: {
    id: number;
    project_id: number;
    status: string;
    started_at?: string;
    ended_at?: string;
  } | null;
  state_points: Array<{
    slot_count: number;
    maximum_slot?: number;
    timeslot?: number;
    payload?: {
      links?: Array<{
        id?: string;
        type?: string;
        status?: boolean;
        distance?: number;
        capacity?: number;
        src?: string;
        dst?: string;
      }>;
      [key: string]: unknown;
    };
  }>;
  entity_points: RecordSeriesEntityPoint[];
  window?: {
    start_slot: number;
    end_slot: number;
    loaded_slot_count: number;
    has_more: boolean;
  };
};

export type { EarthPoint, LinkPoint, SatellitePoint, StationPoint, SunPoint };
