import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { FormState, Project } from "./dashboard.model";
import { emptyForm, intFields } from "./dashboard.model";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useDashboardController() {
  const router = useRouter();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [form, setForm] = useState<FormState>(emptyForm);

  const isEditing = useMemo(() => editingId !== null, [editingId]);
  const selectedProject = useMemo(
    () => projects.find((p) => p.id === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );

  async function fetchProjects() {
    try {
      setLoading(true);
      setError("");
      const resp = await fetch(`${API_BASE}/api/projects`, { cache: "no-store" });
      if (!resp.ok) throw new Error(`Load failed: ${resp.status}`);
      const data = (await resp.json()) as Project[];
      setProjects(data);
      setSelectedProjectId((prev) => {
        if (prev !== null && data.some((p) => p.id === prev)) return prev;
        return null;
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Load failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchProjects();
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

      const url = isEditing ? `${API_BASE}/api/projects/${editingId}` : `${API_BASE}/api/projects`;
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

      setProjects((prev) => {
        const next = prev.filter((p) => p.id !== id);
        setSelectedProjectId((current) => {
          if (current !== id) return current;
          return next.length > 0 ? next[0].id : null;
        });
        return next;
      });
      if (editingId === id) resetForm();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Delete failed";
      setError(msg);
    }
  }

  const toProject = (id: number) => {
    router.push(`/workspace/${id}`);
  };

  const selectProject = (id: number) => {
    setSelectedProjectId(id);
  };

  return {
    projects,
    selectedProject,
    selectedProjectId,
    loading,
    saving,
    error,
    editingId,
    isCreateModalOpen,
    isEditModalOpen,
    form,
    isEditing,
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
  };
}
