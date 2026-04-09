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
      altitude: draftProject.altitude,
      inclination: draftProject.inclination,
      planeCount: draftProject.planeCount,
      constellationSize: draftProject.constellationSize,
      phaseFactor: draftProject.phaseFactor,
      imageryWidthPx: draftProject.imageryWidthPx,
      imageryLengthPx: draftProject.imageryLengthPx,
      cameraFocalLengthMm: draftProject.cameraFocalLengthMm,
      cameraSensorUnitLengthUm: draftProject.cameraSensorUnitLengthUm,
      channelsPerPixel: draftProject.channelsPerPixel,
      bitsPerChannel: draftProject.bitsPerChannel,
      processorClockFrequency: draftProject.processorClockFrequency,
      processorCoreQuantity: draftProject.processorCoreQuantity,
      processorEnergyFactor: draftProject.processorEnergyFactor,
      maxTaskProcessingNumber: draftProject.maxTaskProcessingNumber,
      transmitAntennaGain: draftProject.transmitAntennaGain,
      receiveAntennaGain: draftProject.receiveAntennaGain,
      transmitSignalPower: draftProject.transmitSignalPower,
      maxTaskTransmittingNumber: draftProject.maxTaskTransmittingNumber,
      batteryCapacity: draftProject.batteryCapacity,
      solarPanelArea: draftProject.solarPanelArea,
      solarPanelEfficiency: draftProject.solarPanelEfficiency,
      dynamicPowerComputing: draftProject.dynamicPowerComputing,
      dynamicPowerTransmitting: draftProject.dynamicPowerTransmitting,
      staticPowerComputing: draftProject.staticPowerComputing,
      staticPowerTransmitting: draftProject.staticPowerTransmitting,
      staticPowerOthers: draftProject.staticPowerOthers,
      stationTransmitAntennaGain: draftProject.stationTransmitAntennaGain,
      stationReceiveAntennaGain: draftProject.stationReceiveAntennaGain,
      stationTransmitSignalPower: draftProject.stationTransmitSignalPower,
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
    <main className="w-full min-h-screen py-20 px-40">
      <div className="mx-auto max-w-6xl">
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

        <div className="mb-4 inline-flex p-1 text-sm">
          <button
            onClick={() => setActiveSection("information")}
            className={`rounded px-3 py-1.5 ${activeSection === "information" ? "bg-black text-white" : "hover:bg-gray-100"}`}
          >
            Information
          </button>
          <button
            onClick={() => setActiveSection("entities")}
            className={`rounded px-3 py-1.5 ${activeSection === "entities" ? "bg-black text-white" : "hover:bg-gray-100"}`}
          >
            Entities
          </button>
          <button
            onClick={() => setActiveSection("records")}
            className={`rounded px-3 py-1.5 ${activeSection === "records" ? "bg-black text-white" : "hover:bg-gray-100"}`}
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
                          onChange={(e) => setTextField("name", e.target.value)}
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
                      <span className="opacity-70">Time Slot: </span>
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
                      <span className="opacity-70">Quantity of Plane: </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.planeCount ?? ""}
                          onChange={(e) =>
                            setNumberField("planeCount", e.target.value)
                          }
                        />
                      ) : (
                        <span>{draftProject.planeCount ?? "-"}</span>
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
                          value={draftProject.constellationSize ?? ""}
                          onChange={(e) =>
                            setNumberField("constellationSize", e.target.value)
                          }
                        />
                      ) : (
                        <span>{draftProject.constellationSize ?? "-"}</span>
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
                      <span className="opacity-70">Imagery Length (px): </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.imageryLengthPx ?? ""}
                          onChange={(e) =>
                            setNumberField("imageryLengthPx", e.target.value)
                          }
                        />
                      ) : (
                        <span>{draftProject.imageryLengthPx ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Camera Focal Length (mm):{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.cameraFocalLengthMm ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "cameraFocalLengthMm",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>{draftProject.cameraFocalLengthMm ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Camera Sensor Unit Length (μm):{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.cameraSensorUnitLengthUm ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "cameraSensorUnitLengthUm",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>
                          {draftProject.cameraSensorUnitLengthUm ?? "-"}
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
                      <span className="opacity-70">Bits per Channel: </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.bitsPerChannel ?? ""}
                          onChange={(e) =>
                            setNumberField("bitsPerChannel", e.target.value)
                          }
                        />
                      ) : (
                        <span>{draftProject.bitsPerChannel ?? "-"}</span>
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
                        Processor Clock Frequency:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.processorClockFrequency ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "processorClockFrequency",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>
                          {draftProject.processorClockFrequency ?? "-"}
                        </span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Processor Core Quantity:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.processorCoreQuantity ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "processorCoreQuantity",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>{draftProject.processorCoreQuantity ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Processor Energy Factor:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.processorEnergyFactor ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "processorEnergyFactor",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>{draftProject.processorEnergyFactor ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Maximum Task Processing Number:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.maxTaskProcessingNumber ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "maxTaskProcessingNumber",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>
                          {draftProject.maxTaskProcessingNumber ?? "-"}
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
                        Transmit Antenna Gain:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.transmitAntennaGain ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "transmitAntennaGain",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>{draftProject.transmitAntennaGain ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">Receive Antenna Gain: </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.receiveAntennaGain ?? ""}
                          onChange={(e) =>
                            setNumberField("receiveAntennaGain", e.target.value)
                          }
                        />
                      ) : (
                        <span>{draftProject.receiveAntennaGain ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Transmit Signal Power:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.transmitSignalPower ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "transmitSignalPower",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>{draftProject.transmitSignalPower ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Maximum Task Transmitting Number:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.maxTaskTransmittingNumber ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "maxTaskTransmittingNumber",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>
                          {draftProject.maxTaskTransmittingNumber ?? "-"}
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
                      <span className="opacity-70">Battery Capacity: </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.batteryCapacity ?? ""}
                          onChange={(e) =>
                            setNumberField("batteryCapacity", e.target.value)
                          }
                        />
                      ) : (
                        <span>{draftProject.batteryCapacity ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">Solar Panel Area: </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.solarPanelArea ?? ""}
                          onChange={(e) =>
                            setNumberField("solarPanelArea", e.target.value)
                          }
                        />
                      ) : (
                        <span>{draftProject.solarPanelArea ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Solar Panel Efficiency:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.solarPanelEfficiency ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "solarPanelEfficiency",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>{draftProject.solarPanelEfficiency ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Dynamic Power of Computing:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.dynamicPowerComputing ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "dynamicPowerComputing",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>{draftProject.dynamicPowerComputing ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Dynamic Power of Transmitting:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.dynamicPowerTransmitting ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "dynamicPowerTransmitting",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>
                          {draftProject.dynamicPowerTransmitting ?? "-"}
                        </span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Static Power of Computing:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.staticPowerComputing ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "staticPowerComputing",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>{draftProject.staticPowerComputing ?? "-"}</span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Static Power of Transmitting:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.staticPowerTransmitting ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "staticPowerTransmitting",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>
                          {draftProject.staticPowerTransmitting ?? "-"}
                        </span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Static Power of Others:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.staticPowerOthers ?? ""}
                          onChange={(e) =>
                            setNumberField("staticPowerOthers", e.target.value)
                          }
                        />
                      ) : (
                        <span>{draftProject.staticPowerOthers ?? "-"}</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="rounded border p-3">
                  <p className="mb-2 text-sm font-semibold">
                    Station Parameters
                  </p>
                  <div className="grid grid-cols-1 gap-2 md:grid-cols-2 text-sm">
                    <div>
                      <span className="opacity-70">
                        Transmit Antenna Gain:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.stationTransmitAntennaGain ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "stationTransmitAntennaGain",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>
                          {draftProject.stationTransmitAntennaGain ?? "-"}
                        </span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">Receive Antenna Gain: </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.stationReceiveAntennaGain ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "stationReceiveAntennaGain",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>
                          {draftProject.stationReceiveAntennaGain ?? "-"}
                        </span>
                      )}
                    </div>
                    <div>
                      <span className="opacity-70">
                        Transmit Signal Power:{" "}
                      </span>
                      {isEditingProject ? (
                        <input
                          type="number"
                          className="ml-2 rounded border px-2 py-1"
                          value={draftProject.stationTransmitSignalPower ?? ""}
                          onChange={(e) =>
                            setNumberField(
                              "stationTransmitSignalPower",
                              e.target.value,
                            )
                          }
                        />
                      ) : (
                        <span>
                          {draftProject.stationTransmitSignalPower ?? "-"}
                        </span>
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
                        Lat {gs.latitude}, Lon {gs.longitude}, Alt {gs.altitude}
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
                  <p className="text-sm opacity-70">No ground stations yet.</p>
                ) : null}
              </div>
            </section>
          </div>
        ) : null}

        {activeSection === "records" ? (
          <section className="p-4">
            <h2 className="mb-3 text-lg font-semibold">Record List</h2>
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
    </main>
  );
}
