import { useEffect, useMemo, useState } from "react";
import type {
  GroundStation,
  Project,
  ProjectPatch,
  SatelliteSummary,
  SimulationRecord,
} from "./workspace.model";

type UseWorkspaceControllerArgs = {
  projectId: string;
};

export function useWorkspaceController({ projectId }: UseWorkspaceControllerArgs) {
  const apiBase = useMemo(() => process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000", []);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [project, setProject] = useState<Project | null>(null);
  const [groundStations, setGroundStations] = useState<GroundStation[]>([]);
  const [records, setRecords] = useState<SimulationRecord[]>([]);

  const [newStationName, setNewStationName] = useState("");
  const [newStationLat, setNewStationLat] = useState(0);
  const [newStationLon, setNewStationLon] = useState(0);
  const [newStationAlt, setNewStationAlt] = useState(0);

  const fetchProject = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${apiBase}/api/projects/${projectId}`, { cache: "no-store" });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const row = (await resp.json()) as Project;
      setProject(row);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch project");
    } finally {
      setLoading(false);
    }
  };

  const fetchGroundStations = async () => {
    try {
      const resp = await fetch(`${apiBase}/api/projects/${projectId}/ground-stations`, { cache: "no-store" });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const rows = (await resp.json()) as GroundStation[];
      setGroundStations(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch ground stations");
    }
  };

  const fetchRecords = async () => {
    try {
      const resp = await fetch(`${apiBase}/api/simulation/records/${projectId}?limit=200`, {
        cache: "no-store",
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const payload = await resp.json();
      const rows = (payload?.records ?? []) as SimulationRecord[];
      setRecords(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch records");
    }
  };

  const refresh = async () => {
    await Promise.all([fetchProject(), fetchGroundStations(), fetchRecords()]);
  };

  useEffect(() => {
    void refresh();
  }, [projectId]);

  const updateProject = async (patch: ProjectPatch) => {
    setSaving(true);
    setError(null);
    try {
      const resp = await fetch(`${apiBase}/api/projects/${projectId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const row = (await resp.json()) as Project;
      setProject(row);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update project");
    } finally {
      setSaving(false);
    }
  };

  const addGroundStation = async () => {
    const hasName = newStationName.trim().length > 0;
    const hasLat = Number.isFinite(newStationLat);
    const hasLon = Number.isFinite(newStationLon);
    const hasAlt = Number.isFinite(newStationAlt);

    if (!hasName || !hasLat || !hasLon || !hasAlt) {
      setError("Please provide name, latitude, longitude, and altitude before adding a station");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const resp = await fetch(`${apiBase}/api/projects/${projectId}/ground-stations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newStationName,
          latitude: newStationLat,
          longitude: newStationLon,
          altitude: newStationAlt,
        }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      setNewStationName("");
      setNewStationLat(0);
      setNewStationLon(0);
      setNewStationAlt(0);
      await fetchGroundStations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add ground station");
    } finally {
      setSaving(false);
    }
  };

  const deleteGroundStation = async (stationId: number) => {
    setSaving(true);
    setError(null);
    try {
      const resp = await fetch(`${apiBase}/api/projects/${projectId}/ground-stations/${stationId}`, {
        method: "DELETE",
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      await fetchGroundStations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete ground station");
    } finally {
      setSaving(false);
    }
  };

  const deleteRecord = async (recordId: number) => {
    setSaving(true);
    setError(null);
    try {
      const resp = await fetch(`${apiBase}/api/simulation/records/${recordId}`, {
        method: "DELETE",
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      await fetchRecords();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete record");
    } finally {
      setSaving(false);
    }
  };

  const satellites = useMemo(() => {
    if (!project) return [] as SatelliteSummary[];

    const planeCount = Number(project.planeCount ?? 0);
    const constellationSize = Number(project.constellationSize ?? 0);
    const orderCount = constellationSize / planeCount;
    if (!Number.isFinite(planeCount) || !Number.isFinite(constellationSize)) return [];
    if (planeCount <= 0 || constellationSize <= 0) return [];

    const out: SatelliteSummary[] = [];
    for (let plane = 0; plane < planeCount; plane += 1) {
      for (let order = 0; order < orderCount; order += 1) {
        out.push({ id: `@${plane * orderCount + order}`, plane, order });
      }
    }
    return out;
  }, [project]);

  return {
    project,
    setProject,
    satellites,
    groundStations,
    records,
    loading,
    saving,
    error,
    refresh,
    updateProject,
    addGroundStation,
    deleteGroundStation,
    deleteRecord,
    newStationName,
    newStationLat,
    newStationLon,
    newStationAlt,
    setNewStationName,
    setNewStationLat,
    setNewStationLon,
    setNewStationAlt,
  };
}
