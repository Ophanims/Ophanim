import { FormEvent, ReactNode } from "react";
import {
  ArrowPathIcon,
  PencilSquareIcon,
  PlayCircleIcon,
  PlusIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import Earth from "../section/earthbg";
import type { FormState, Project } from "./dashboard.model";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-md p-4">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide">
        {title}
      </h3>
      <div className="grid gap-3 md:grid-cols-2">{children}</div>
    </section>
  );
}

function TextInput({
  label,
  field,
  form,
  setField,
  type = "text",
  required = false,
  disabled = false,
}: {
  label: string;
  field: keyof FormState;
  form: FormState;
  setField: <K extends keyof FormState>(key: K, value: FormState[K]) => void;
  type?: "text" | "number" | "datetime-local";
  required?: boolean;
  disabled?: boolean;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium">{label}</span>
      <input
        type={type}
        value={form[field]}
        onChange={(e) => setField(field, e.target.value)}
        className="rounded-md border px-3 py-2 text-sm outline-none"
        required={required}
        disabled={disabled}
      />
    </label>
  );
}

function ModalForm({
  title,
  onClose,
  submitLabel,
  onSubmit,
  saving,
  isEditing,
  editingId,
  form,
  setField,
}: {
  title: string;
  onClose: () => void;
  submitLabel: string;
  onSubmit: (e: FormEvent<HTMLFormElement>) => Promise<void>;
  saving: boolean;
  isEditing: boolean;
  editingId: number | null;
  form: FormState;
  setField: <K extends keyof FormState>(key: K, value: FormState[K]) => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative bg-black/80 text-white w-full max-w-5xl max-h-[92vh] overflow-y-auto rounded-xl border p-6 shadow-2xl">
        <div className="mb-5 flex items-center justify-between gap-4">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-md border px-3 py-1.5 text-sm"
            type="button"
          >
            Close
          </button>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <Section title="Basic">
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-medium">ID</span>
              <input
                value={isEditing ? String(editingId) : "Auto-generated"}
                className="rounded-md border px-3 py-2 text-sm outline-none"
                disabled
              />
            </label>
            <TextInput
              label="Name"
              field="name"
              form={form}
              setField={setField}
              required
            />
          </Section>

          <Section title="Simulation Parameters">
            <TextInput
              label="Time Slot"
              field="timeSlot"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Start Time"
              field="startTime"
              form={form}
              setField={setField}
              type="datetime-local"
            />
            <TextInput
              label="End Time"
              field="endTime"
              form={form}
              setField={setField}
              type="datetime-local"
            />
          </Section>

          <Section title="Orbital Parameters">
            <TextInput
              label="Altitude"
              field="altitude"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Inclination"
              field="inclination"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Quantity of Plane"
              field="planeCount"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Size of Constellation"
              field="constellationSize"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Phase Factor"
              field="phaseFactor"
              form={form}
              setField={setField}
              type="number"
            />
          </Section>

          <Section title="Observation Parameters">
            <TextInput
              label="Imagery Width (px)"
              field="imageryWidthPx"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Imagery Length (px)"
              field="imageryLengthPx"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Camera Focal Length (mm)"
              field="cameraFocalLengthMm"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Camera Sensor Unit Length (um)"
              field="cameraSensorUnitLengthUm"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Channels Per Pixel"
              field="channelsPerPixel"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Bits Per Channel"
              field="bitsPerChannel"
              form={form}
              setField={setField}
              type="number"
            />
          </Section>

          <Section title="Computation Parameters">
            <TextInput
              label="Processor Clock Frequency"
              field="processorClockFrequency"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Processor Core Quantity"
              field="processorCoreQuantity"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Processor Energy Factor"
              field="processorEnergyFactor"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Maximum Task Processing Number"
              field="maxTaskProcessingNumber"
              form={form}
              setField={setField}
              type="number"
            />
          </Section>

          <Section title="Communication Parameters">
            <TextInput
              label="Transmit Antenna Gain"
              field="transmitAntennaGain"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Receive Antenna Gain"
              field="receiveAntennaGain"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Transmit Signal Power"
              field="transmitSignalPower"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Maximum Task Transmitting Number"
              field="maxTaskTransmittingNumber"
              form={form}
              setField={setField}
              type="number"
            />
          </Section>

          <Section title="Energy Parameters">
            <TextInput
              label="Battery Capacity"
              field="batteryCapacity"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Solar Panel Area"
              field="solarPanelArea"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Solar Panel Efficiency"
              field="solarPanelEfficiency"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Dynamic Power of Computing"
              field="dynamicPowerComputing"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Dynamic Power of Transmitting"
              field="dynamicPowerTransmitting"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Static Power of Computing"
              field="staticPowerComputing"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Static Power of Transmitting"
              field="staticPowerTransmitting"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Static Power of Others"
              field="staticPowerOthers"
              form={form}
              setField={setField}
              type="number"
            />
          </Section>

          <Section title="Station Parameters">
            <TextInput
              label="Transmit Antenna Gain"
              field="stationTransmitAntennaGain"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Receive Antenna Gain"
              field="stationReceiveAntennaGain"
              form={form}
              setField={setField}
              type="number"
            />
            <TextInput
              label="Transmit Signal Power"
              field="stationTransmitSignalPower"
              form={form}
              setField={setField}
              type="number"
            />
          </Section>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded-md px-4 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "Saving..." : submitLabel}
            </button>

            <button
              type="button"
              onClick={onClose}
              className="rounded-md border px-4 py-2 text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

type DashboardViewProps = {
  projects: Project[];
  selectedProject: Project | null;
  selectedProjectId: number | null;
  loading: boolean;
  saving: boolean;
  error: string;
  editingId: number | null;
  isCreateModalOpen: boolean;
  isEditModalOpen: boolean;
  isEditing: boolean;
  form: FormState;
  fetchProjects: () => Promise<void>;
  openCreateModal: () => void;
  closeCreateModal: () => void;
  closeEditModal: () => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => Promise<void>;
  startEdit: (project: Project) => void;
  removeProject: (id: number) => Promise<void>;
  toProject: (id: number) => void;
  selectProject: (id: number) => void;
  setField: <K extends keyof FormState>(key: K, value: FormState[K]) => void;
};

export default function DashboardView(props: DashboardViewProps) {
  const {
    projects,
    selectedProject,
    selectedProjectId,
    loading,
    saving,
    error,
    editingId,
    isCreateModalOpen,
    isEditModalOpen,
    isEditing,
    form,
    fetchProjects,
    openCreateModal,
    closeCreateModal,
    closeEditModal,
    handleSubmit,
    startEdit,
    removeProject,
    toProject,
    selectProject,
    setField,
  } = props;

  return (
    <main className="w-full h-screen relative font-sans overflow-hidden">
      {/* <div className="absolute bottom-0 w-full h-full pointer-events-none z-0">
        <Earth isFull={false} />
      </div> */}
      <div className="absolute inset-0 flex flex-col py-20 px-40 z-20">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-6xl font-bold tracking-tight">OPHANIM</h1>
            <p className="text-xl tracking-tight">
              Lightweight Satellite Constellation Simulator
            </p>
          </div>
        </div>
        <div className="flex w-full">
          <section className="w-1/2 p-4">
            <div className="flex flex-col gap-2 mb-8 text-sm">
              <h2 className="text-lg font-semibold">Start</h2>
              <button
                onClick={openCreateModal}
                className="items-center gap-2 inline-flex"
              >
                <PlusIcon className="h-5 w-5" /> <span>Create Project</span>
              </button>
              <button
                onClick={() => void fetchProjects()}
                className="items-center gap-2 inline-flex"
              >
                <ArrowPathIcon className="h-5 w-5" /> <span>Refresh List</span>
              </button>
            </div>

            {isCreateModalOpen && (
              <ModalForm
                title="Create Project"
                submitLabel="Create Project"
                onClose={closeCreateModal}
                onSubmit={handleSubmit}
                saving={saving}
                isEditing={isEditing}
                editingId={editingId}
                form={form}
                setField={setField}
              />
            )}

            {isEditModalOpen && isEditing && (
              <ModalForm
                title="Edit Project"
                submitLabel="Update Project"
                onClose={closeEditModal}
                onSubmit={handleSubmit}
                saving={saving}
                isEditing={isEditing}
                editingId={editingId}
                form={form}
                setField={setField}
              />
            )}

            <div className="py-2">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Projects</h2>
              </div>

              {error && <div className="mb-4 px-3 py-2 text-sm">{error}</div>}

              {loading ? (
                <p>Loading...</p>
              ) : projects.length === 0 ? (
                <p>No projects yet. Create one to get started.</p>
              ) : (
                <div
                  className={`grid gap-4 ${selectedProject ? "lg:grid-cols-2" : "grid-cols-1"}`}
                >
                  <div className="overflow-x-auto text-sm">
                    {projects.map((p) => (
                      <div
                        key={p.id}
                        className={`flex cursor-pointer gap-3 ${selectedProjectId === p.id ? "bg-white/10" : ""}`}
                        onClick={() => selectProject(p.id)}
                      >
                        <span className="py-3 font-bold">{p.name}</span>
                        <span className="py-3">
                          {new Date(p.updated_at).toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>

          <div className="h-full w-[1px] bg-black"></div>

          <section className="w-1/2 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Project Detail</h3>
              {selectedProject ? (
                <>
                  <div className="flex gap-2">
                    <button
                      onClick={() => startEdit(selectedProject)}
                      className="px-2 py-1"
                    >
                      <PencilSquareIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => removeProject(selectedProject.id)}
                      className="px-2 py-1"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => toProject(selectedProject.id)}
                      className="px-2 py-1"
                    >
                      <PlayCircleIcon className="h-5 w-5" />
                    </button>
                  </div>
                </>
              ) : null}
            </div>
            {selectedProject ? (
              <div className="space-y-2 text-sm">
                <p>
                  <span className="opacity-70">ID:</span> {selectedProject.id}
                </p>
                <p>
                  <span className="opacity-70">Name:</span>{" "}
                  {selectedProject.name}
                </p>
                <p>
                  <span className="opacity-70">Status:</span>{" "}
                  {selectedProject.status ?? "-"}
                </p>
                <p>
                  <span className="opacity-70">Time Slot:</span>{" "}
                  {selectedProject.timeSlot ?? "-"}
                </p>
                <p>
                  <span className="opacity-70">Start Time:</span>{" "}
                  {selectedProject.startTime ?? "-"}
                </p>
                <p>
                  <span className="opacity-70">End Time:</span>{" "}
                  {selectedProject.endTime ?? "-"}
                </p>
                <p>
                  <span className="opacity-70">Altitude:</span>{" "}
                  {selectedProject.altitude ?? "-"}
                </p>
                <p>
                  <span className="opacity-70">Inclination:</span>{" "}
                  {selectedProject.inclination ?? "-"}
                </p>
                <p>
                  <span className="opacity-70">Plane Count:</span>{" "}
                  {selectedProject.planeCount ?? "-"}
                </p>
                <p>
                  <span className="opacity-70">Constellation Size:</span>{" "}
                  {selectedProject.constellationSize ?? "-"}
                </p>
                <p>
                  <span className="opacity-70">Updated:</span>{" "}
                  {new Date(selectedProject.updated_at).toLocaleString()}
                </p>
              </div>
            ) : null}
          </section>
        </div>
      </div>
    </main>
  );
}
