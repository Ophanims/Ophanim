export type SatellitePoint = {
  addr: string;
  type: string;
  id: string;
  plane: number;
  order: number;
  x: number;
  y: number;
  z: number;
  velocityVector: [number, number, number];
  solarVector: [number, number, number];
  corLat1: number;
  corLon1: number;
  corLat2: number;
  corLon2: number;
  corLat3: number;
  corLon3: number;
  corLat4: number;
  corLon4: number;
  corX1: number;
  corY1: number;
  corZ1: number;
  corX2: number;
  corY2: number;
  corZ2: number;
  corX3: number;
  corY3: number;
  corZ3: number;
  corX4: number;
  corY4: number;
  corZ4: number;
  batteryLevel: number;
  processorClockFrequency: number;
  onROI: boolean;
  onSUN: boolean;
  onSGL: boolean;
  onISL: boolean;
  onCOM: boolean;
};

export type LinkPoint = {
  id: string;
  type: string;
  status: string;
  distance: number;
  capacity: number;
  srcId: string;
  dstId: string;
  srcX: number;
  srcY: number;
  srcZ: number;
  dstX: number;
  dstY: number;
  dstZ: number;
};

export type StationPoint = {
  addr: string;
  x: number;
  y: number;
  z: number;
};

export type SunPoint = {
  addr: string;
  x: number;
  y: number;
  z: number;
};

export type EarthPoint = {
  addr: string;
  nullIslandX: number;
  nullIslandY: number;
  nullIslandZ: number;
  rotationalAngularVelocity: number;
};

export type SimulationStatus = "idle" | "connected" | "running" | "paused" | "stopped" | "closed" | "error";
