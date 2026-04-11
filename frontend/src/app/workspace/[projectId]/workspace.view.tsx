import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeftIcon,
  ChevronLeftIcon,
  PlayIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import type {
  GroundStation,
  Project,
  ProjectPatch,
  SatelliteSummary,
  SimulationRecord,
} from "./workspace.model";
import Earth from "@/app/section/earthbg";

type WorkspaceViewProps = {
  projectId: string;
  project: Project | null;
  satellites: SatelliteSummary[];
  groundStations: GroundStation[];
  records: SimulationRecord[];
  loading: boolean;
  saving: boolean;
  error: string | null;
  onRefresh: () => void;
  onSaveProject: (patch: ProjectPatch) => void;
  onDeleteGroundStation: (stationId: number) => void;
  onDeleteRecord: (recordId: number) => void;
  onClearRecords: () => void;
  onAddGroundStation: () => void;
  newStationName: string;
  newStationLat: number;
  newStationLon: number;
  newStationAlt: number;
  setNewStationName: (v: string) => void;
  setNewStationLat: (v: number) => void;
  setNewStationLon: (v: number) => void;
  setNewStationAlt: (v: number) => void;
};

export default function WorkspaceView(props: WorkspaceViewProps) {
  const {
    projectId,
    project,
    satellites,
    groundStations,
    records,
    loading,
    saving,
    error,
    onRefresh,
    onSaveProject,
    onDeleteGroundStation,
    onDeleteRecord,
    onClearRecords,
    onAddGroundStation,
    newStationName,
    newStationLat,
    newStationLon,
    newStationAlt,
    setNewStationName,
    setNewStationLat,
    setNewStationLon,
    setNewStationAlt,
  } = props;

  const [isEditingProject, setIsEditingProject] = useState(false);
  const [draftProject, setDraftProject] = useState<Project | null>(project);
  const [activeSection, setActiveSection] = useState<
    "information" | "entities" | "records"
  >("information");

  useEffect(() => {
    setDraftProject(project);
  }, [project]);

  const setTextField = (key: keyof Project, value: string) => {
    setDraftProject((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  const setNumberField = (key: keyof Project, value: string) => {
    setDraftProject((prev) => {
      if (!prev) return prev;
      return { ...prev, [key]: value.trim() === "" ? null : Number(value) };
    });
  };

  const setDatetimeField = (key: keyof Project, value: string) => {
    setDraftProject((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  const toDatetimeLocal = (value: unknown) => {
    if (typeof value !== "string" || !value) return "";
    return value.replace(" ", "T").slice(0, 16);
  };

  const saveDraft = () => {
    if (!draftProject) return;

    const patch: ProjectPatch = {
      name: draftProject.name,
      timeSlot: draftProject.timeSlot,
      startTime: draftProject.startTime,
      endTime: draftProject.endTime,
      seed: draftProject.seed,
      altitude: draftProject.altitude,
      inclination: draftProject.inclination,
      maximumNumberOfPlane: draftProject.maximumNumberOfPlane,
      sizeOfConstellation: draftProject.sizeOfConstellation,
      phaseFactor: draftProject.phaseFactor,
      imageryWidthPx: draftProject.imageryWidthPx,
      imageryHeightPx: draftProject.imageryHeightPx,
      lengthOfCameraFocalMm: draftProject.lengthOfCameraFocalMm,
      lengthOfCameraSensorUnitUm: draftProject.lengthOfCameraSensorUnitUm,
      channelsPerPixel: draftProject.channelsPerPixel,
      bitsPerChannelBit: draftProject.bitsPerChannelBit,
      maximumClockFrequencyGhz: draftProject.maximumClockFrequencyGhz,
      maximumNumberOfProcessorCore: draftProject.maximumNumberOfProcessorCore,
      factorOfComputationEnergy: draftProject.factorOfComputationEnergy,
      maximumConcurrentComputation: draftProject.maximumConcurrentComputation,
      carrierFrequencyOfIslGhz: draftProject.carrierFrequencyOfIslGhz,
      carrierFrequencyOfUpGhz: draftProject.carrierFrequencyOfUpGhz,
      carrierFrequencyOfDlGhz: draftProject.carrierFrequencyOfDlGhz,
      bandwidthOfIslMhz: draftProject.bandwidthOfIslMhz,
      bandwidthOfUlMhz: draftProject.bandwidthOfUlMhz,
      bandwidthOfDlMhz: draftProject.bandwidthOfDlMhz,
      efficiencyOfTargetSpectrum: draftProject.efficiencyOfTargetSpectrum,
      antennaGainOfIslTransmitDbi: draftProject.antennaGainOfIslTransmitDbi,
      antennaGainOfIslReceiveDbi: draftProject.antennaGainOfIslReceiveDbi,
      antennaGainOfUlTransmitDbi: draftProject.antennaGainOfUlTransmitDbi,
      antennaGainOfUlReceiveDbi: draftProject.antennaGainOfUlReceiveDbi,
      antennaGainOfDlTransmitDbi: draftProject.antennaGainOfDlTransmitDbi,
      antennaGainOfDlReceiveDbi: draftProject.antennaGainOfDlReceiveDbi,
      factorOfTransmissionEnergy: draftProject.factorOfTransmissionEnergy,
      maximumConcurrentTransmission: draftProject.maximumConcurrentTransmission,
      batteryCapacityWh: draftProject.batteryCapacityWh,
      areaOfSolarPanelM2: draftProject.areaOfSolarPanelM2,
      efficiencyOfSolarPanel: draftProject.efficiencyOfSolarPanel,
      efficiencyOfPowerAmplifier: draftProject.efficiencyOfPowerAmplifier,
      staticPowerOfProcessingW: draftProject.staticPowerOfProcessingW,
      staticPowerOfIslTransmittingW: draftProject.staticPowerOfIslTransmittingW,
      staticPowerOfUplinkTransmittingW: draftProject.staticPowerOfUplinkTransmittingW,
      staticPowerOfDownlinkTransmittingW: draftProject.staticPowerOfDownlinkTransmittingW,
      staticPowerOfOthersW: draftProject.staticPowerOfOthersW,
    };

    onSaveProject(patch);
    setIsEditingProject(false);
  };

  const cancelEdit = () => {
    setDraftProject(project);
    setIsEditingProject(false);
  };

  const canAddGroundStation =
    newStationName.trim().length > 0 &&
    Number.isFinite(newStationLat) &&
    Number.isFinite(newStationLon) &&
    Number.isFinite(newStationAlt);

  return (
    <main className="w-full h-screen bg-black text-white relative font-sans overflow-hidden">
      <div className="absolute bottom-0 w-full h-full pointer-events-none z-0">
        <Earth isFull={false} />
      </div>
      <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
        <div className="h-screen w-full mx-auto max-w-6xl overflow-y-auto p-20">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link href="/dashboard" className="px-3 py-2">
                <ChevronLeftIcon className="h-6 w-6" />
              </Link>
              <h1 className="text-2xl font-semibold">
                Workspace / {draftProject?.name || projectId}
              </h1>
            </div>

            <div className="flex gap-2">
              <Link
                href={`/simulation/${projectId}`}
                className="flex items-center justify-center gap-2 px-3 py-2 mx-4 border rounded-xl text-sm"
              >
                <PlayIcon className="h-4 w-4" />
                <span className="">Run Simulation</span>
              </Link>
              {/* <button onClick={onRefresh} className="px-3 py-2 text-sm" disabled={loading || saving}>
              Refresh
            </button> */}
            </div>
          </div>

          {error ? (
            <p className="mb-4 text-sm text-red-600">Error: {error}</p>
          ) : null}

          <div className="inline-flex p-1 text-sm">
            <button
              onClick={() => setActiveSection("information")}
              className={`rounded px-3 py-1.5 hover:cursor-pointer ${activeSection === "information" ? "bg-white text-black" : "hover:bg-white/20"}`}
            >
              Information
            </button>
            <button
              onClick={() => setActiveSection("entities")}
              className={`rounded px-3 py-1.5 hover:cursor-pointer ${activeSection === "entities" ? "bg-white text-black" : "hover:bg-white/20"}`}
            >
              Entities
            </button>
            <button
              onClick={() => setActiveSection("records")}
              className={`rounded px-3 py-1.5 hover:cursor-pointer ${activeSection === "records" ? "bg-white text-black" : "hover:bg-white/20"}`}
            >
              Records
            </button>
          </div>

          {activeSection === "information" ? (
            <section className="p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold">Project Details</h2>
                {!isEditingProject ? (
                  <button
                    onClick={() => setIsEditingProject(true)}
                    disabled={!draftProject || saving}
                    className="rounded border px-3 py-2 text-sm"
                  >
                    Edit
                  </button>
                ) : (
                  <div className="flex gap-2">
                    <button
                      onClick={saveDraft}
                      disabled={saving}
                      className="rounded border px-3 py-2 text-sm"
                    >
                      Save
                    </button>
                    <button
                      onClick={cancelEdit}
                      disabled={saving}
                      className="rounded border px-3 py-2 text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
              {!project ? (
                <p className="text-sm opacity-70">Loading project...</p>
              ) : null}

              {draftProject ? (
                <div className="space-y-3">
                  <div className="rounded border p-3">
                    <p className="mb-2 text-sm font-semibold">Basic</p>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-2 text-sm">
                      <div>
                        <span className="opacity-70">Id: </span>
                        {draftProject.id}
                      </div>
                      <div>
                        <span className="opacity-70">Name: </span>
                        {isEditingProject ? (
                          <input
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.name ?? ""}
                            onChange={(e) =>
                              setTextField("name", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.name ?? "-"}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="rounded border p-3">
                    <p className="mb-2 text-sm font-semibold">
                      Simulation Parameters
                    </p>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-3 text-sm">
                      <div>
                        <span className="opacity-70">Time Slot (s): </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.timeSlot ?? ""}
                            onChange={(e) =>
                              setNumberField("timeSlot", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.timeSlot ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">Start Time: </span>
                        {isEditingProject ? (
                          <input
                            type="datetime-local"
                            className="ml-2 rounded border px-2 py-1"
                            value={toDatetimeLocal(draftProject.startTime)}
                            onChange={(e) =>
                              setDatetimeField("startTime", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.startTime ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">Seed: </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.seed ?? ""}
                            onChange={(e) =>
                              setNumberField("seed", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.seed ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">End Time: </span>
                        {isEditingProject ? (
                          <input
                            type="datetime-local"
                            className="ml-2 rounded border px-2 py-1"
                            value={toDatetimeLocal(draftProject.endTime)}
                            onChange={(e) =>
                              setDatetimeField("endTime", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.endTime ?? "-"}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="rounded border p-3">
                    <p className="mb-2 text-sm font-semibold">
                      Orbital Parameters
                    </p>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-3 text-sm">
                      <div>
                        <span className="opacity-70">Altitude: </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.altitude ?? ""}
                            onChange={(e) =>
                              setNumberField("altitude", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.altitude ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">Inclination: </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.inclination ?? ""}
                            onChange={(e) =>
                              setNumberField("inclination", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.inclination ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">Maximum Number of Plane: </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.maximumNumberOfPlane ?? ""}
                            onChange={(e) =>
                              setNumberField("maximumNumberOfPlane", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.maximumNumberOfPlane ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Size of Constellation:{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.sizeOfConstellation ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "sizeOfConstellation",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.sizeOfConstellation ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">Phase Factor: </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.phaseFactor ?? ""}
                            onChange={(e) =>
                              setNumberField("phaseFactor", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.phaseFactor ?? "-"}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="rounded border p-3">
                    <p className="mb-2 text-sm font-semibold">
                      Observation Parameters
                    </p>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-3 text-sm">
                      <div>
                        <span className="opacity-70">Imagery Width (px): </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.imageryWidthPx ?? ""}
                            onChange={(e) =>
                              setNumberField("imageryWidthPx", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.imageryWidthPx ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Imagery Height (px):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.imageryHeightPx ?? ""}
                            onChange={(e) =>
                              setNumberField("imageryHeightPx", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.imageryHeightPx ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Length of Camera Focal (mm):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.lengthOfCameraFocalMm ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "lengthOfCameraFocalMm",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.lengthOfCameraFocalMm ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Length of Camera Sensor Unit (μm):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.lengthOfCameraSensorUnitUm ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "lengthOfCameraSensorUnitUm",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.lengthOfCameraSensorUnitUm ?? "-"}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">Channels Per Pixel: </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.channelsPerPixel ?? ""}
                            onChange={(e) =>
                              setNumberField("channelsPerPixel", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.channelsPerPixel ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">Bits per Channel (bit): </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.bitsPerChannelBit ?? ""}
                            onChange={(e) =>
                              setNumberField("bitsPerChannelBit", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.bitsPerChannelBit ?? "-"}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="rounded border p-3">
                    <p className="mb-2 text-sm font-semibold">
                      Computation Parameters
                    </p>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-2 text-sm">
                      <div>
                        <span className="opacity-70">
                          Maximum Clock Frequency (GHz):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.maximumClockFrequencyGhz ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "maximumClockFrequencyGhz",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.maximumClockFrequencyGhz ?? "-"}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Maximum Number of Processor Core:{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.maximumNumberOfProcessorCore ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "maximumNumberOfProcessorCore",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.maximumNumberOfProcessorCore ?? "-"}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Factor of Computation Energy:{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.factorOfComputationEnergy ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "factorOfComputationEnergy",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.factorOfComputationEnergy ?? "-"}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Maximum Concurrent Computation:{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.maximumConcurrentComputation ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "maximumConcurrentComputation",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.maximumConcurrentComputation ?? "-"}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="rounded border p-3">
                    <p className="mb-2 text-sm font-semibold">
                      Communication Parameters
                    </p>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-2 text-sm">
                      <div>
                        <span className="opacity-70">
                          Carrier Frequency of ISL (GHz):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.carrierFrequencyOfIslGhz ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "carrierFrequencyOfIslGhz",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.carrierFrequencyOfIslGhz ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Carrier Frequency of UP (GHz):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.carrierFrequencyOfUpGhz ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "carrierFrequencyOfUpGhz",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.carrierFrequencyOfUpGhz ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Carrier Frequency of DL (GHz):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.carrierFrequencyOfDlGhz ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "carrierFrequencyOfDlGhz",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.carrierFrequencyOfDlGhz ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Bandwidth of ISL (MHz):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.bandwidthOfIslMhz ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "bandwidthOfIslMhz",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.bandwidthOfIslMhz ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Bandwidth of UL (MHz):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.bandwidthOfUlMhz ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "bandwidthOfUlMhz",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.bandwidthOfUlMhz ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Bandwidth of DL (MHz):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.bandwidthOfDlMhz ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "bandwidthOfDlMhz",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.bandwidthOfDlMhz ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Factor of Transmission Energy:{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.factorOfTransmissionEnergy ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "factorOfTransmissionEnergy",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.factorOfTransmissionEnergy ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Efficiency of Target Spectrum:{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.efficiencyOfTargetSpectrum ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "efficiencyOfTargetSpectrum",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.efficiencyOfTargetSpectrum ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Antenna Gain of ISL Transmit (dBi):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.antennaGainOfIslTransmitDbi ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "antennaGainOfIslTransmitDbi",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.antennaGainOfIslTransmitDbi ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Antenna Gain of ISL Receive (dBi):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.antennaGainOfIslReceiveDbi ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "antennaGainOfIslReceiveDbi",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.antennaGainOfIslReceiveDbi ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Antenna Gain of UL Transmit (dBi):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.antennaGainOfUlTransmitDbi ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "antennaGainOfUlTransmitDbi",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.antennaGainOfUlTransmitDbi ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Antenna Gain of UL Receive (dBi):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.antennaGainOfUlReceiveDbi ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "antennaGainOfUlReceiveDbi",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.antennaGainOfUlReceiveDbi ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Antenna Gain of DL Transmit (dBi):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.antennaGainOfDlTransmitDbi ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "antennaGainOfDlTransmitDbi",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.antennaGainOfDlTransmitDbi ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Antenna Gain of DL Receive (dBi):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.antennaGainOfDlReceiveDbi ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "antennaGainOfDlReceiveDbi",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.antennaGainOfDlReceiveDbi ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Maximum Concurrent Transmission:{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.maximumConcurrentTransmission ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "maximumConcurrentTransmission",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.maximumConcurrentTransmission ?? "-"}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="rounded border p-3">
                    <p className="mb-2 text-sm font-semibold">
                      Energy Parameters
                    </p>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-2 text-sm">
                      <div>
                        <span className="opacity-70">Battery Capacity (Wh): </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.batteryCapacityWh ?? ""}
                            onChange={(e) =>
                              setNumberField("batteryCapacityWh", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.batteryCapacityWh ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">Area of Solar Panel (m²): </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.areaOfSolarPanelM2 ?? ""}
                            onChange={(e) =>
                              setNumberField("areaOfSolarPanelM2", e.target.value)
                            }
                          />
                        ) : (
                          <span>{draftProject.areaOfSolarPanelM2 ?? "-"}</span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Efficiency of Solar Panel:{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.efficiencyOfSolarPanel ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "efficiencyOfSolarPanel",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.efficiencyOfSolarPanel ?? "-"}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Efficiency of Power Amplifier:{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.efficiencyOfPowerAmplifier ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "efficiencyOfPowerAmplifier",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.efficiencyOfPowerAmplifier ?? "-"}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Static Power of Processing (W):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.staticPowerOfProcessingW ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "staticPowerOfProcessingW",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.staticPowerOfProcessingW ?? "-"}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Static Power of ISL Transmitting (W):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.staticPowerOfIslTransmittingW ?? ""}
                            onChange={(e) =>
                              setNumberField("staticPowerOfIslTransmittingW", e.target.value)
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.staticPowerOfIslTransmittingW ?? "-"}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Static Power of Uplink Transmitting (W):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.staticPowerOfUplinkTransmittingW ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "staticPowerOfUplinkTransmittingW",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.staticPowerOfUplinkTransmittingW ?? "-"}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Static Power of Downlink Transmitting (W):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.staticPowerOfDownlinkTransmittingW ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "staticPowerOfDownlinkTransmittingW",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>
                            {draftProject.staticPowerOfDownlinkTransmittingW ?? "-"}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="opacity-70">
                          Static Power of Others (W):{" "}
                        </span>
                        {isEditingProject ? (
                          <input
                            type="number"
                            className="ml-2 rounded border px-2 py-1"
                            value={draftProject.staticPowerOfOthersW ?? ""}
                            onChange={(e) =>
                              setNumberField(
                                "staticPowerOfOthersW",
                                e.target.value,
                              )
                            }
                          />
                        ) : (
                          <span>{draftProject.staticPowerOfOthersW ?? "-"}</span>
                        )}
                      </div>
                    </div>
                  </div>


                  {/* <div className="rounded border p-3">
                  <p className="mb-2 text-sm font-semibold">Description</p>
                  {isEditingProject ? (
                    <textarea
                      className="w-full rounded border px-2 py-1"
                      rows={3}
                      value={draftProject.description ?? ""}
                      onChange={(e) => setTextField("description", e.target.value)}
                    />
                  ) : (
                    <p className="text-sm">{draftProject.description ?? "-"}</p>
                  )}
                </div> */}
                </div>
              ) : null}
            </section>
          ) : null}

          {activeSection === "entities" ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <section className="p-4">
                <h2 className="mb-3 text-lg font-semibold">Satellite List</h2>
                <div className="max-h-80 space-y-2 overflow-auto">
                  {satellites.map((sat) => (
                    <div key={sat.id} className="rounded border p-2 text-sm">
                      <p className="font-medium">{sat.id}</p>
                      <p className="opacity-70">
                        Plane {sat.plane}, Order {sat.order}
                      </p>
                    </div>
                  ))}
                  {satellites.length === 0 ? (
                    <p className="text-sm opacity-70">
                      No satellites derived from project parameters.
                    </p>
                  ) : null}
                </div>
              </section>

              <section className="p-4">
                <h2 className="mb-3 text-lg font-semibold">Ground Stations</h2>

                <div className="mb-4 grid grid-cols-2 gap-2">
                  <input
                    placeholder="Name"
                    className="rounded border px-2 py-1"
                    value={newStationName}
                    onChange={(e) => setNewStationName(e.target.value)}
                  />
                  <input
                    type="number"
                    placeholder="Latitude"
                    className="rounded border px-2 py-1"
                    value={newStationLat}
                    onChange={(e) => setNewStationLat(Number(e.target.value))}
                  />
                  <input
                    type="number"
                    placeholder="Longitude"
                    className="rounded border px-2 py-1"
                    value={newStationLon}
                    onChange={(e) => setNewStationLon(Number(e.target.value))}
                  />
                  <input
                    type="number"
                    placeholder="Altitude"
                    className="rounded border px-2 py-1"
                    value={newStationAlt}
                    onChange={(e) => setNewStationAlt(Number(e.target.value))}
                  />
                  <button
                    onClick={onAddGroundStation}
                    disabled={saving || !canAddGroundStation}
                    className="col-span-2 rounded border px-3 py-2 text-sm"
                  >
                    Add Ground Station
                  </button>
                </div>

                <div className="space-y-2">
                  {groundStations.map((gs) => (
                    <div
                      key={gs.id}
                      className="flex items-center justify-between rounded border p-2 text-sm"
                    >
                      <div>
                        <p className="font-medium">{gs.name}</p>
                        <p className="opacity-70">
                          Lat {gs.latitude}, Lon {gs.longitude}, Alt{" "}
                          {gs.altitude}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => onDeleteGroundStation(gs.id)}
                          className="rounded border p-1 text-red-600"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                  {groundStations.length === 0 ? (
                    <p className="text-sm opacity-70">
                      No ground stations yet.
                    </p>
                  ) : null}
                </div>
              </section>
            </div>
          ) : null}

          {activeSection === "records" ? (
            <section className="p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold">Record List</h2>
                <button
                  type="button"
                  onClick={() => {
                    if (
                      records.length > 0
                      && window.confirm("Delete all records? This action cannot be undone.")
                    ) {
                      onClearRecords();
                    }
                  }}
                  className="rounded border px-2 py-1 text-xs text-red-600 disabled:opacity-50"
                  disabled={saving || records.length === 0}
                >
                  Clear All
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="px-2 py-2">Record ID</th>
                      <th className="px-2 py-2">Status</th>
                      <th className="px-2 py-2">Started</th>
                      <th className="px-2 py-2">Ended</th>
                      <th className="px-2 py-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((r) => (
                      <tr key={r.id} className="border-b">
                        <td className="px-2 py-2">{r.id}</td>
                        <td className="px-2 py-2">{r.status}</td>
                        <td className="px-2 py-2">
                          {r.started_at
                            ? new Date(r.started_at).toLocaleString()
                            : "-"}
                        </td>
                        <td className="px-2 py-2">
                          {r.ended_at
                            ? new Date(r.ended_at).toLocaleString()
                            : "-"}
                        </td>
                        <td className="px-2 py-2">
                          <div className="flex items-center gap-2">
                            <Link
                              href={`/record/${projectId}/${r.id}`}
                              className="rounded border px-2 py-1 text-xs"
                            >
                              Open Record
                            </Link>
                            <button
                              type="button"
                              onClick={() => {
                                if (
                                  window.confirm(
                                    `Delete record ${r.id}? This action cannot be undone.`,
                                  )
                                ) {
                                  onDeleteRecord(r.id);
                                }
                              }}
                              className="rounded border px-2 py-1 text-xs text-red-600"
                              disabled={saving}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {records.length === 0 ? (
                  <p className="mt-2 text-sm opacity-70">No records yet.</p>
                ) : null}
              </div>
            </section>
          ) : null}
        </div>
      </div>
    </main>
  );
}
