export type Project = {
  id: number;
  [key: string]: unknown;
  name?: string | null;
  description?: string | null;
  status?: string | null;
  timeSlot?: number | null;
  startTime?: string | null;
  endTime?: string | null;
  seed?: number | null;
  altitude?: number | null;
  inclination?: number | null;
  maximumNumberOfPlane?: number | null;
  sizeOfConstellation?: number | null;
  phaseFactor?: number | null;
  imageryWidthPx?: number | null;
  imageryHeightPx?: number | null;
  lengthOfCameraFocalMm?: number | null;
  lengthOfCameraSensorUnitUm?: number | null;
  channelsPerPixel?: number | null;
  bitsPerChannelBit?: number | null;
  maximumNumberOfProcessorCore?: number | null;
  factorOfComputationEnergy?: number | null;
  maximumConcurrentComputation?: number | null;
  maximumClockFrequencyGhz?: number | null;
  carrierFrequencyOfIslGhz?: number | null;
  carrierFrequencyOfUpGhz?: number | null;
  carrierFrequencyOfDlGhz?: number | null;
  bandwidthOfIslMhz?: number | null;
  bandwidthOfUlMhz?: number | null;
  bandwidthOfDlMhz?: number | null;
  factorOfTransmissionEnergy?: number | null;
  efficiencyOfTargetSpectrum?: number | null;
  antennaGainOfIslTransmitDbi?: number | null;
  antennaGainOfIslReceiveDbi?: number | null;
  antennaGainOfUlTransmitDbi?: number | null;
  antennaGainOfUlReceiveDbi?: number | null;
  antennaGainOfDlTransmitDbi?: number | null;
  antennaGainOfDlReceiveDbi?: number | null;
  maximumConcurrentTransmission?: number | null;
  batteryCapacityWh?: number | null;
  areaOfSolarPanelM2?: number | null;
  efficiencyOfSolarPanel?: number | null;
  efficiencyOfPowerAmplifier?: number | null;
  staticPowerOfProcessingW?: number | null;
  staticPowerOfIslTransmittingW?: number | null;
  staticPowerOfUplinkTransmittingW?: number | null;
  staticPowerOfDownlinkTransmittingW?: number | null;
  staticPowerOfOthersW?: number | null;
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
