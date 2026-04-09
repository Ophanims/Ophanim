export type SatellitePoint = {
  id: string;
  x: number;
  y: number;
  z: number;
};

export type StationPoint = {
  id: string;
  x: number;
  y: number;
  z: number;
};

export type SunPoint = {
  id: string;
  x: number;
  y: number;
  z: number;
};

export type EarthPoint = {
  id: string;
  nullIslandX: number;
  nullIslandY: number;
  nullIslandZ: number;
  rotationalAngularVelocity: number;
};

export type SimulationStatus = "idle" | "connected" | "running" | "paused" | "stopped" | "closed" | "error";
