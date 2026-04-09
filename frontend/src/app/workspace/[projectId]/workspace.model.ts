export type Project = {
  id: number;
  [key: string]: unknown;
  name?: string | null;
  description?: string | null;
  status?: string | null;
  timeSlot?: number | null;
  startTime?: string | null;
  endTime?: string | null;
  altitude?: number | null;
  inclination?: number | null;
  planeCount?: number | null;
  constellationSize?: number | null;
  phaseFactor?: number | null;
  imageryWidthPx?: number | null;
  imageryLengthPx?: number | null;
  cameraFocalLengthMm?: number | null;
  cameraSensorUnitLengthUm?: number | null;
  channelsPerPixel?: number | null;
  bitsPerChannel?: number | null;
  processorClockFrequency?: number | null;
  processorCoreQuantity?: number | null;
  processorEnergyFactor?: number | null;
  maxTaskProcessingNumber?: number | null;
  transmitAntennaGain?: number | null;
  receiveAntennaGain?: number | null;
  transmitSignalPower?: number | null;
  maxTaskTransmittingNumber?: number | null;
  batteryCapacity?: number | null;
  solarPanelArea?: number | null;
  solarPanelEfficiency?: number | null;
  dynamicPowerComputing?: number | null;
  dynamicPowerTransmitting?: number | null;
  staticPowerComputing?: number | null;
  staticPowerTransmitting?: number | null;
  staticPowerOthers?: number | null;
  stationTransmitAntennaGain?: number | null;
  stationReceiveAntennaGain?: number | null;
  stationTransmitSignalPower?: number | null;
};

export type GroundStation = {
  id: number;
  project_id: number;
  name: string;
  latitude: number;
  longitude: number;
  altitude: number;
};

export type SimulationRecord = {
  id: number;
  project_id: number;
  status: string;
  started_at: string;
  ended_at?: string | null;
};

export type SatelliteSummary = {
  id: string;
  plane: number;
  order: number;
};

export type ProjectPatch = Partial<Project>;
