"use client";

import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
// import Link from "next/link";
import { useRouter } from "next/navigation";
import { PlayIcon } from "@heroicons/react/24/solid";
import Earth from "../section/earthbg";
import { ArrowPathIcon, PlusIcon } from "@heroicons/react/24/outline";

type Project = {
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

type FormState = {
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

const emptyForm: FormState = {
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

const intFields = new Set([
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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
              label="Camera Sensor Unit Length (μm)"
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

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [form, setForm] = useState<FormState>(emptyForm);

  const isEditing = useMemo(() => editingId !== null, [editingId]);

  async function fetchProjects() {
    try {
      setLoading(true);
      setError("");
      const resp = await fetch(`${API_BASE}/api/projects`, { cache: "no-store" });
      if (!resp.ok) throw new Error(`Load failed: ${resp.status}`);
      const data = (await resp.json()) as Project[];
      setProjects(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Load failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchProjects();
  }, []);

  function resetForm() {
    setForm(emptyForm);
    setEditingId(null);
  }

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function valueOf(v: unknown): string {
    return v === null || v === undefined ? "" : String(v);
  }

  function projectToForm(project: Project): FormState {
    return {
      name: valueOf(project.name),
      timeSlot: valueOf(project.timeSlot),
      startTime: valueOf(project.startTime),
      endTime: valueOf(project.endTime),
      altitude: valueOf(project.altitude),
      inclination: valueOf(project.inclination),
      planeCount: valueOf(project.planeCount),
      constellationSize: valueOf(project.constellationSize),
      phaseFactor: valueOf(project.phaseFactor),
      imageryWidthPx: valueOf(project.imageryWidthPx),
      imageryLengthPx: valueOf(project.imageryLengthPx),
      cameraFocalLengthMm: valueOf(project.cameraFocalLengthMm),
      cameraSensorUnitLengthUm: valueOf(project.cameraSensorUnitLengthUm),
      channelsPerPixel: valueOf(project.channelsPerPixel),
      bitsPerChannel: valueOf(project.bitsPerChannel),
      processorClockFrequency: valueOf(project.processorClockFrequency),
      processorCoreQuantity: valueOf(project.processorCoreQuantity),
      processorEnergyFactor: valueOf(project.processorEnergyFactor),
      maxTaskProcessingNumber: valueOf(project.maxTaskProcessingNumber),
      transmitAntennaGain: valueOf(project.transmitAntennaGain),
      receiveAntennaGain: valueOf(project.receiveAntennaGain),
      transmitSignalPower: valueOf(project.transmitSignalPower),
      maxTaskTransmittingNumber: valueOf(project.maxTaskTransmittingNumber),
      batteryCapacity: valueOf(project.batteryCapacity),
      solarPanelArea: valueOf(project.solarPanelArea),
      solarPanelEfficiency: valueOf(project.solarPanelEfficiency),
      dynamicPowerComputing: valueOf(project.dynamicPowerComputing),
      dynamicPowerTransmitting: valueOf(project.dynamicPowerTransmitting),
      staticPowerComputing: valueOf(project.staticPowerComputing),
      staticPowerTransmitting: valueOf(project.staticPowerTransmitting),
      staticPowerOthers: valueOf(project.staticPowerOthers),
      stationTransmitAntennaGain: valueOf(project.stationTransmitAntennaGain),
      stationReceiveAntennaGain: valueOf(project.stationReceiveAntennaGain),
      stationTransmitSignalPower: valueOf(project.stationTransmitSignalPower),
    };
  }

  function buildPayload() {
    const payload: Record<string, string | number | null> = {};

    (Object.keys(form) as Array<keyof FormState>).forEach((key) => {
      const raw = form[key].trim();

      if (key === "name") {
        payload.name = raw;
        return;
      }

      if (key === "startTime" || key === "endTime") {
        payload[key] = raw ? raw.replace("T", " ") : null;
        return;
      }

      if (!raw) {
        payload[key] = null;
        return;
      }

      if (intFields.has(key)) {
        payload[key] = Number.parseInt(raw, 10);
      } else {
        payload[key] = Number.parseFloat(raw);
      }
    });

    return payload;
  }

  function openCreateModal() {
    resetForm();
    setIsCreateModalOpen(true);
  }

  function closeCreateModal() {
    setIsCreateModalOpen(false);
    resetForm();
  }

  function closeEditModal() {
    setIsEditModalOpen(false);
    resetForm();
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!form.name.trim()) return;

    try {
      setSaving(true);
      setError("");

      const payload = buildPayload();

      const url = isEditing
        ? `${API_BASE}/api/projects/${editingId}`
        : `${API_BASE}/api/projects`;
      const method = isEditing ? "PUT" : "POST";

      const resp = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || `${method} failed`);
      }

      await fetchProjects();
      if (isEditing) {
        closeEditModal();
      } else {
        closeCreateModal();
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Save failed";
      setError(msg);
    } finally {
      setSaving(false);
    }
  }

  function startEdit(project: Project) {
    setEditingId(project.id);
    setForm(projectToForm(project));
    setIsEditModalOpen(true);
  }

  async function removeProject(id: number) {
    const ok = window.confirm("Are you sure you want to delete this project?");
    if (!ok) return;

    try {
      setError("");
      const resp = await fetch(`${API_BASE}/api/projects/${id}`, {
        method: "DELETE",
      });
      if (!resp.ok) throw new Error(`Delete failed: ${resp.status}`);

      setProjects((prev) => prev.filter((p) => p.id !== id));
      if (editingId === id) resetForm();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Delete failed";
      setError(msg);
    }
  }

  const router = useRouter();

  const backhome = () => {
    router.push("/");
  };

  const toProject = (id: number) => {
    router.push(`/workspace/${id}`);
  }

  return (
    <main className="w-full h-screen text-white relative font-sans overflow-hidden">
      <div className="absolute bottom-0 w-full h-full pointer-events-none z-0">
        <Earth isFull={false} />
      </div>
      <div className="absolute inset-0 flex flex-col p-20 z-20">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              Dashboard
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={openCreateModal}
              className="rounded-md border px-4 py-2 text-sm font-semibold"
            >
              <PlusIcon className="h-4 w-4 inline" /> Create Project
            </button>
          </div>
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

        <section className="rounded-xl border p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Project List</h2>
            <button onClick={fetchProjects} className="rounded-md px-3 py-1.5 text-sm">
              <ArrowPathIcon className="h-4 w-4 inline" />
            </button>
          </div>

          {error && (
            <div className="mb-4 rounded-md border px-3 py-2 text-sm">
              {error}
            </div>
          )}

          {loading ? (
            <p>Loading...</p>
          ) : projects.length === 0 ? (
            <p>No projects yet. Create one to get started.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b text-left">
                    {/* <th className="px-2 py-3">ID</th> */}
                    <th className="px-2 py-3">Name</th>
                    <th className="px-2 py-3">Time Slot</th>
                    <th className="px-2 py-3">Altitude</th>
                    <th className="px-2 py-3">Inclination</th>
                    <th className="px-2 py-3">Updated</th>
                    <th className="px-2 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr key={p.id} className="border-b align-top">
                      {/* <td className="px-2 py-3">{p.id}</td> */}
                      <td className="px-2 py-3 font-medium">{p.name}</td>
                      <td className="px-2 py-3">{p.timeSlot ?? "-"}</td>
                      <td className="px-2 py-3">{p.altitude ?? "-"}</td>
                      <td className="px-2 py-3">{p.inclination ?? "-"}</td>
                      <td className="px-2 py-3">
                        {new Date(p.updated_at).toLocaleString()}
                      </td>
                      <td className="px-2 py-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => startEdit(p)}
                            className="rounded border px-2 py-1 text-xs"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => removeProject(p.id)}
                            className="rounded border px-2 py-1 text-xs"
                          >
                            Delete
                          </button>
                          <button
                            onClick={() => toProject(p.id)}
                            className="rounded border px-2 py-1 text-xs"
                          >
                            Open
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
