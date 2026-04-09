export type Project = {
  id: number;
  name: string;
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
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type FormState = {
  name: string;
  timeSlot: string;
  startTime: string;
  endTime: string;
  altitude: string;
  inclination: string;
  planeCount: string;
  constellationSize: string;
  phaseFactor: string;
  imageryWidthPx: string;
  imageryLengthPx: string;
  cameraFocalLengthMm: string;
  cameraSensorUnitLengthUm: string;
  channelsPerPixel: string;
  bitsPerChannel: string;
  processorClockFrequency: string;
  processorCoreQuantity: string;
  processorEnergyFactor: string;
  maxTaskProcessingNumber: string;
  transmitAntennaGain: string;
  receiveAntennaGain: string;
  transmitSignalPower: string;
  maxTaskTransmittingNumber: string;
  batteryCapacity: string;
  solarPanelArea: string;
  solarPanelEfficiency: string;
  dynamicPowerComputing: string;
  dynamicPowerTransmitting: string;
  staticPowerComputing: string;
  staticPowerTransmitting: string;
  staticPowerOthers: string;
  stationTransmitAntennaGain: string;
  stationReceiveAntennaGain: string;
  stationTransmitSignalPower: string;
};

export const emptyForm: FormState = {
  name: "",
  timeSlot: "",
  startTime: "",
  endTime: "",
  altitude: "",
  inclination: "",
  planeCount: "",
  constellationSize: "",
  phaseFactor: "",
  imageryWidthPx: "",
  imageryLengthPx: "",
  cameraFocalLengthMm: "",
  cameraSensorUnitLengthUm: "",
  channelsPerPixel: "",
  bitsPerChannel: "",
  processorClockFrequency: "",
  processorCoreQuantity: "",
  processorEnergyFactor: "",
  maxTaskProcessingNumber: "",
  transmitAntennaGain: "",
  receiveAntennaGain: "",
  transmitSignalPower: "",
  maxTaskTransmittingNumber: "",
  batteryCapacity: "",
  solarPanelArea: "",
  solarPanelEfficiency: "",
  dynamicPowerComputing: "",
  dynamicPowerTransmitting: "",
  staticPowerComputing: "",
  staticPowerTransmitting: "",
  staticPowerOthers: "",
  stationTransmitAntennaGain: "",
  stationReceiveAntennaGain: "",
  stationTransmitSignalPower: "",
};

export const intFields = new Set([
  "planeCount",
  "constellationSize",
  "imageryWidthPx",
  "imageryLengthPx",
  "channelsPerPixel",
  "bitsPerChannel",
  "processorCoreQuantity",
  "maxTaskProcessingNumber",
  "maxTaskTransmittingNumber",
]);
