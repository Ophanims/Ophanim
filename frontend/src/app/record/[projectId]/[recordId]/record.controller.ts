import { useEffect, useMemo, useState } from "react";
import type { RecordSeriesPayload, SatellitePoint } from "./record.model";

type UseRecordPlaybackControllerArgs = {
  recordId: string;
};

export function useRecordPlaybackController({ recordId }: UseRecordPlaybackControllerArgs) {
  const apiBase = useMemo(() => process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000", []);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recordSeries, setRecordSeries] = useState<RecordSeriesPayload | null>(null);
  const [selectedFrameSlot, setSelectedFrameSlot] = useState<number | null>(null);
  const [playing, setPlaying] = useState(true);

  const loadSeries = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(
        `${apiBase}/api/simulation/record-series/${recordId}?state_limit=5000&entity_limit=50000`,
        { cache: "no-store" },
      );
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const payload = (await resp.json()) as RecordSeriesPayload;
      setRecordSeries(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load record series");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadSeries();
  }, [recordId]);

  const frameSlots = useMemo(() => {
    const points = recordSeries?.entity_points ?? [];
    const slots = new Set<number>();
    for (const p of points) {
      if (typeof p.slot_count === "number") slots.add(p.slot_count);
    }
    return Array.from(slots).sort((a, b) => a - b);
  }, [recordSeries]);

  useEffect(() => {
    if (frameSlots.length === 0) {
      setSelectedFrameSlot(null);
      return;
    }
    setSelectedFrameSlot(frameSlots[0]);
  }, [frameSlots]);

  const satellites = useMemo(() => {
    if (!recordSeries || selectedFrameSlot === null) return [];
    const out: SatellitePoint[] = [];
    for (const p of recordSeries.entity_points ?? []) {
      if (p.slot_count !== selectedFrameSlot) continue;
      const payload = p.payload;
      const entityType = payload?.type ?? p.entity_type;
      if (!payload || (entityType !== "satellite" && entityType !== "earth_satellite")) continue;

      const x = Number(payload.x);
      const y = Number(payload.y);
      const z = Number(payload.z);
      if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) continue;
      out.push({ id: String(payload.id ?? p.entity_id), x, y, z });
    }
    return out;
  }, [recordSeries, selectedFrameSlot]);

  const frameIndex = useMemo(() => {
    if (selectedFrameSlot === null) return -1;
    return frameSlots.indexOf(selectedFrameSlot);
  }, [frameSlots, selectedFrameSlot]);

  useEffect(() => {
    if (!playing || frameSlots.length <= 1) return;
    const timer = window.setInterval(() => {
      setSelectedFrameSlot((currentSlot) => {
        if (currentSlot === null) return frameSlots[0] ?? null;
        const idx = frameSlots.indexOf(currentSlot);
        const next = idx < 0 || idx >= frameSlots.length - 1 ? 0 : idx + 1;
        return frameSlots[next] ?? currentSlot;
      });
    }, 100);

    return () => window.clearInterval(timer);
  }, [playing, frameSlots]);

  return {
    loading,
    error,
    recordSeries,
    frameSlots,
    satellites,
    frameIndex,
    playing,
    setPlaying,
    loadSeries,
  };
}
