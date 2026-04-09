export type SatellitePoint = {
  id: string;
  x: number;
  y: number;
  z: number;
};

export type SimulationStatus = "idle" | "connected" | "running" | "paused" | "stopped" | "closed" | "error";
