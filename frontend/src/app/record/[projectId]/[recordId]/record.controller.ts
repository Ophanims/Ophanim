import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { RecordSeriesPayload, SatellitePoint } from "./record.model";

const INITIAL_WINDOW_SLOT_LIMIT = 120;
const PREFETCH_TRIGGER_RATIO = 0.7;
const WINDOW_SLOT_LIMIT = 120;

type UseRecordPlaybackControllerArgs = {
  recordId: string;
};

export function useRecordPlaybackController({ recordId }: UseRecordPlaybackControllerArgs) {
  const apiBase = useMemo(() => process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000", []);
  const requestVersionRef = useRef(0);

  const [loading, setLoading] = useState(false);
  const [buffering, setBuffering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recordSeries, setRecordSeries] = useState<RecordSeriesPayload | null>(null);
  const [selectedFrameSlot, setSelectedFrameSlot] = useState<number | null>(null);
  const [playing, setPlaying] = useState(true);
  const [hasMore, setHasMore] = useState(true);

  const mergeRecordSeries = (previous: RecordSeriesPayload, next: RecordSeriesPayload): RecordSeriesPayload => {
    const mergedStatePoints = [...(previous.state_points ?? []), ...(next.state_points ?? [])].sort(
      (left, right) => left.slot_count - right.slot_count,
    );
    const mergedEntityPoints = [...(previous.entity_points ?? []), ...(next.entity_points ?? [])].sort(
      (left, right) => left.slot_count - right.slot_count || left.entity_id.localeCompare(right.entity_id),
    );

    return {
      ...previous,
      ...next,
      state_points: mergedStatePoints,
      entity_points: mergedEntityPoints,
      window: next.window ?? previous.window,
    };
  };

  const loadSeriesWindow = useCallback(
    async (startSlot: number, slotLimit: number, mode: "initial" | "append") => {
      const requestVersion = ++requestVersionRef.current;

      if (mode === "initial") {
        setLoading(true);
        setError(null);
        setHasMore(true);
        setRecordSeries(null);
        setSelectedFrameSlot(null);
      } else {
        setBuffering(true);
      }

      try {
        const resp = await fetch(
          `${apiBase}/api/simulation/record-series/${recordId}?start_slot=${startSlot}&slot_limit=${slotLimit}`,
          { cache: "no-store" },
        );
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const payload = (await resp.json()) as RecordSeriesPayload;

        if (requestVersion !== requestVersionRef.current) return;

        setRecordSeries((previous) => (previous && mode === "append" ? mergeRecordSeries(previous, payload) : payload));
        setHasMore(payload.window?.has_more ?? false);
      } catch (err) {
        if (requestVersion === requestVersionRef.current) {
          setError(err instanceof Error ? err.message : "Failed to load record series");
          setPlaying(false);
        }
      } finally {
        if (requestVersion === requestVersionRef.current) {
          setLoading(false);
          setBuffering(false);
        }
      }
    },
    [apiBase, recordId],
  );

  const loadSeries = useCallback(async () => {
    await loadSeriesWindow(0, INITIAL_WINDOW_SLOT_LIMIT, "initial");
  }, [loadSeriesWindow]);

  useEffect(() => {
    void loadSeries();
  }, [loadSeries, recordId]);

  const frameSlots = useMemo(() => {
    const points = recordSeries?.state_points ?? [];
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
    setSelectedFrameSlot((currentSlot) => {
      if (currentSlot === null) return frameSlots[0] ?? null;
      return frameSlots.includes(currentSlot) ? currentSlot : frameSlots[0] ?? null;
    });
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
      out.push({
        addr: String(p.entity_id ?? payload.id ?? "unknown"),
        type: String(payload.type ?? p.entity_type ?? "earth_satellite"),
        id: String(payload.id ?? p.entity_id ?? "unknown"),
        plane: 0,
        order: 0,
        x,
        y,
        z,
        velocityVector: [0, 0, 0],
        solarVector: [0, 0, 0],
        corLat1: 0,
        corLon1: 0,
        corLat2: 0,
        corLon2: 0,
        corLat3: 0,
        corLon3: 0,
        corLat4: 0,
        corLon4: 0,
        corX1: 0,
        corY1: 0,
        corZ1: 0,
        corX2: 0,
        corY2: 0,
        corZ2: 0,
        corX3: 0,
        corY3: 0,
        corZ3: 0,
        corX4: 0,
        corY4: 0,
        corZ4: 0,
        batteryLevel: 0,
        processorClockFrequency: 0,
        onROI: false,
        onSUN: false,
        onSGL: false,
        onISL: false,
        onCOM: false,
      });
    }
    return out;
  }, [recordSeries, selectedFrameSlot]);

  const frameIndex = useMemo(() => {
    if (selectedFrameSlot === null) return -1;
    return frameSlots.indexOf(selectedFrameSlot);
  }, [frameSlots, selectedFrameSlot]);

  useEffect(() => {
    if (!playing || loading || buffering || !hasMore || frameSlots.length === 0 || selectedFrameSlot === null) {
      return;
    }

    const currentIndex = frameSlots.indexOf(selectedFrameSlot);
    if (currentIndex < 0) return;

    const triggerIndex = Math.floor(Math.max(frameSlots.length - 1, 1) * PREFETCH_TRIGGER_RATIO);
    if (currentIndex < triggerIndex) return;

    const nextStartSlot = frameSlots[frameSlots.length - 1] + 1;
    void loadSeriesWindow(nextStartSlot, WINDOW_SLOT_LIMIT, "append");
  }, [buffering, frameSlots, hasMore, loadSeriesWindow, loading, playing, selectedFrameSlot]);

  useEffect(() => {
    if (!playing || frameSlots.length === 0) return;
    const timer = window.setInterval(() => {
      setSelectedFrameSlot((currentSlot) => {
        if (currentSlot === null) return frameSlots[0] ?? null;
        const idx = frameSlots.indexOf(currentSlot);
        if (idx < 0) return frameSlots[0] ?? null;
        if (idx < frameSlots.length - 1) return frameSlots[idx + 1] ?? currentSlot;
        if (hasMore) return currentSlot;
        return frameSlots[0] ?? currentSlot;
      });
    }, 100);

    return () => window.clearInterval(timer);
  }, [frameSlots, hasMore, playing]);

  return {
    loading,
    buffering,
    error,
    recordSeries,
    frameSlots,
    satellites,
    frameIndex,
    playing,
    hasMore,
    setPlaying,
    loadSeries,
  };
}
