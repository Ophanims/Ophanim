export type RecordSeriesEntityPoint = {
  slot_count: number;
  entity_id: string;
  entity_type?: string;
  payload?: {
    id?: string;
    type?: string;
    x?: number;
    y?: number;
    z?: number;
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
  state_points: Array<{ slot_count: number }>;
  entity_points: RecordSeriesEntityPoint[];
};

export type SatellitePoint = {
  id: string;
  x: number;
  y: number;
  z: number;
};
