export type Project = {
  id: number;
  name: string;
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
  seed: string;
  altitude: string;
  inclination: string;
  maximumNumberOfPlane: string;
  sizeOfConstellation: string;
  phaseFactor: string;
  imageryWidthPx: string;
  imageryHeightPx: string;
  lengthOfCameraFocalMm: string;
  lengthOfCameraSensorUnitUm: string;
  channelsPerPixel: string;
  bitsPerChannelBit: string;
  maximumNumberOfProcessorCore: string;
  factorOfComputationEnergy: string;
  maximumConcurrentComputation: string;
  maximumClockFrequencyGhz: string;
  carrierFrequencyOfIslGhz: string;
  carrierFrequencyOfUpGhz: string;
  carrierFrequencyOfDlGhz: string;
  bandwidthOfIslMhz: string;
  bandwidthOfUlMhz: string;
  bandwidthOfDlMhz: string;
  factorOfTransmissionEnergy: string;
  efficiencyOfTargetSpectrum: string;
  antennaGainOfIslTransmitDbi: string;
  antennaGainOfIslReceiveDbi: string;
  antennaGainOfUlTransmitDbi: string;
  antennaGainOfUlReceiveDbi: string;
  antennaGainOfDlTransmitDbi: string;
  antennaGainOfDlReceiveDbi: string;
  maximumConcurrentTransmission: string;
  batteryCapacityWh: string;
  areaOfSolarPanelM2: string;
  efficiencyOfSolarPanel: string;
  efficiencyOfPowerAmplifier: string;
  staticPowerOfProcessingW: string;
  staticPowerOfIslTransmittingW: string;
  staticPowerOfUplinkTransmittingW: string;
  staticPowerOfDownlinkTransmittingW: string;
  staticPowerOfOthersW: string;
};

export const emptyForm: FormState = {
  name: "",
  timeSlot: "",
  startTime: "",
  endTime: "",
  seed: "",
  altitude: "",
  inclination: "",
  maximumNumberOfPlane: "",
  sizeOfConstellation: "",
  phaseFactor: "",
  imageryWidthPx: "",
  imageryHeightPx: "",
  lengthOfCameraFocalMm: "",
  lengthOfCameraSensorUnitUm: "",
  channelsPerPixel: "",
  bitsPerChannelBit: "",
  maximumNumberOfProcessorCore: "",
  factorOfComputationEnergy: "",
  maximumConcurrentComputation: "",
  maximumClockFrequencyGhz: "",
  carrierFrequencyOfIslGhz: "",
  carrierFrequencyOfUpGhz: "",
  carrierFrequencyOfDlGhz: "",
  bandwidthOfIslMhz: "",
  bandwidthOfUlMhz: "",
  bandwidthOfDlMhz: "",
  factorOfTransmissionEnergy: "",
  efficiencyOfTargetSpectrum: "",
  antennaGainOfIslTransmitDbi: "",
  antennaGainOfIslReceiveDbi: "",
  antennaGainOfUlTransmitDbi: "",
  antennaGainOfUlReceiveDbi: "",
  antennaGainOfDlTransmitDbi: "",
  antennaGainOfDlReceiveDbi: "",
  maximumConcurrentTransmission: "",
  batteryCapacityWh: "",
  areaOfSolarPanelM2: "",
  efficiencyOfSolarPanel: "",
  efficiencyOfPowerAmplifier: "",
  staticPowerOfProcessingW: "",
  staticPowerOfIslTransmittingW: "",
  staticPowerOfUplinkTransmittingW: "",
  staticPowerOfDownlinkTransmittingW: "",
  staticPowerOfOthersW: "",
};

export const intFields = new Set([
  "maximumNumberOfPlane",
  "sizeOfConstellation",
  "imageryWidthPx",
  "imageryHeightPx",
  "channelsPerPixel",
  "bitsPerChannelBit",
  "seed",
  "maximumNumberOfProcessorCore",
  "maximumConcurrentComputation",
  "maximumConcurrentTransmission",
]);
