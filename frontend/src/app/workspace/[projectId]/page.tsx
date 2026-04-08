"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import {
  ArrowLeftIcon,
  HomeIcon,
  InboxIcon,
  PlayIcon,
  PauseIcon,
  VideoCameraIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { useTimeseriesStorage } from "./useTimeseriesStorage";
import RecordFrameWidget from "./RecordFrameWidget";

type SimulationRecord = {
  id: number;
  project_id: number;
  status: string;
  started_at: string;
  ended_at?: string | null;
};

type RecordSeriesStatePoint = {
  ts: string;
  slot_count: number;
};

type RecordSeriesEntityPoint = {
  ts: string;
  slot_count: number;
  entity_id: string;
  entity_type?: string;
  payload?: {
    id?: string;
    type?: string;
    x?: number;
    y?: number;
    z?: number;
  };
};

type RecordSeriesPayload = {
  record: SimulationRecord | null;
  state_points: RecordSeriesStatePoint[];
  entity_points: RecordSeriesEntityPoint[];
};

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const wsRef = useRef<WebSocket | null>(null);
  const [simStatus, setSimStatus] = useState("idle");
  const [tickCount, setTickCount] = useState(0);
  const [simError, setSimError] = useState<string | null>(null);
  const [recordsOpen, setRecordsOpen] = useState(false);
  const [recordsLoading, setRecordsLoading] = useState(false);
  const [recordsError, setRecordsError] = useState<string | null>(null);
  const [records, setRecords] = useState<SimulationRecord[]>([]);
  const [selectedRecordId, setSelectedRecordId] = useState<number | null>(null);
  const [recordSeriesLoading, setRecordSeriesLoading] = useState(false);
  const [recordSeriesError, setRecordSeriesError] = useState<string | null>(
    null,
  );
  const [recordSeries, setRecordSeries] = useState<RecordSeriesPayload | null>(
    null,
  );
  const [selectedFrameSlot, setSelectedFrameSlot] = useState<number | null>(
    null,
  );
  const [isFramePlaying, setIsFramePlaying] = useState(false);
  const {
    getProjectRecords,
    setProjectRecords,
    getRecordSeries,
    setRecordSeries: cacheRecordSeries,
  } = useTimeseriesStorage();

  const apiBase = useMemo(() => {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }, []);

  const wsBase = useMemo(() => {
    if (apiBase.startsWith("https://"))
      return apiBase.replace("https://", "wss://");
    return apiBase.replace("http://", "ws://");
  }, [apiBase]);

  const loadRecords = async (force = false) => {
    if (!force) {
      const cached = getProjectRecords<SimulationRecord>(projectId);
      if (cached) {
        setRecords(cached);
        return;
      }
    }

    try {
      setRecordsLoading(true);
      setRecordsError(null);
      const resp = await fetch(
        `${apiBase}/api/simulation/records/${projectId}?limit=200`,
        {
          cache: "no-store",
        },
      );
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      const payload = await resp.json();
      const rows = payload?.records ?? [];
      setRecords(rows);
      setProjectRecords(projectId, rows);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to fetch records";
      setRecordsError(message);
    } finally {
      setRecordsLoading(false);
    }
  };

  const connectIfNeeded = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return wsRef.current;
    }

    const ws = new WebSocket(`${wsBase}/api/simulation/ws/${projectId}`);
    ws.onopen = () => {
      setSimStatus("connected");
      setSimError(null);
    };
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        console.log("Received message:", msg);
        if (msg?.type === "error") {
          setSimStatus("error");
          setSimError(msg?.message ?? "Simulation engine error");
          return;
        }
        if (msg?.type === "ready") {
          setSimStatus("connected");
          return;
        }
        if (msg?.type === "state") {
          setTickCount(msg.state?.slot_count ?? 0);
          setSimStatus("running");
          setSimError(null);
        }
      } catch {
        // ignore invalid payload
      }
    };
    ws.onclose = () => {
      setSimStatus("closed");
      wsRef.current = null;
    };
    ws.onerror = () => setSimStatus("error");

    wsRef.current = ws;
    return ws;
  };

  const handlePlay = () => {
    const ws = connectIfNeeded();
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "play" }));
      setSimStatus("running");
      return;
    }

    ws.addEventListener(
      "open",
      () => {
        ws.send(JSON.stringify({ action: "play" }));
        setSimStatus("running");
      },
      { once: true },
    );
  };

  const handlePause = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "pause" }));
      setSimStatus("paused");
    }
  };

  const handleToggleRecords = async () => {
    const nextOpen = !recordsOpen;
    setRecordsOpen(nextOpen);
    if (nextOpen) {
      await loadRecords();
    }
  };

  const loadRecordSeries = async (recordId: number, force = false) => {
    if (!force) {
      const cached = getRecordSeries<RecordSeriesPayload>(recordId);
      if (cached) {
        setRecordSeries(cached);
        return;
      }
    }

    try {
      setRecordSeriesLoading(true);
      setRecordSeriesError(null);
      const resp = await fetch(
        `${apiBase}/api/simulation/record-series/${recordId}?state_limit=5000&entity_limit=50000`,
        { cache: "no-store" },
      );
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      const payload = (await resp.json()) as RecordSeriesPayload;
      setRecordSeries(payload);
      const compactPayload: RecordSeriesPayload = {
        record: payload.record,
        state_points: (payload.state_points ?? []).slice(-1000),
        entity_points: (payload.entity_points ?? []).slice(-3000),
      };
      cacheRecordSeries(recordId, compactPayload);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to fetch record series";
      setRecordSeriesError(message);
    } finally {
      setRecordSeriesLoading(false);
    }
  };

  const handleSelectRecord = async (recordId: number) => {
    setIsFramePlaying(false);
    setSelectedRecordId(recordId);
    await loadRecordSeries(recordId);
    setIsFramePlaying(true);
  };

  const frameSlots = useMemo(() => {
    const points = recordSeries?.entity_points ?? [];
    const slots = new Set<number>();
    for (const p of points) {
      if (typeof p.slot_count === "number") {
        slots.add(p.slot_count);
      }
    }
    return Array.from(slots).sort((a, b) => a - b);
  }, [recordSeries]);

  useEffect(() => {
    if (frameSlots.length === 0) {
      setSelectedFrameSlot(null);
      return;
    }

    // Start from the first frame when a record is selected, then autoplay loops.
    setSelectedFrameSlot(frameSlots[0]);
  }, [frameSlots, selectedRecordId]);

  const frameSatellites = useMemo(() => {
    if (!recordSeries || selectedFrameSlot === null) return [];

    const out: Array<{ id: string; x: number; y: number; z: number }> = [];
    for (const p of recordSeries.entity_points ?? []) {
      if (p.slot_count !== selectedFrameSlot) continue;

      const payload = p.payload;
      const entityType = payload?.type ?? p.entity_type;
      if (
        !payload ||
        (entityType !== "satellite" && entityType !== "earth_satellite")
      )
        continue;

      const x = Number(payload.x);
      const y = Number(payload.y);
      const z = Number(payload.z);
      if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z))
        continue;

      out.push({ id: String(payload.id ?? p.entity_id), x, y, z });
    }

    return out;
  }, [recordSeries, selectedFrameSlot]);

  const selectedFrameIndex = useMemo(() => {
    if (selectedFrameSlot === null) return -1;
    return frameSlots.indexOf(selectedFrameSlot);
  }, [frameSlots, selectedFrameSlot]);

  useEffect(() => {
    if (frameSlots.length <= 1) {
      setIsFramePlaying(false);
      return;
    }

    if (!isFramePlaying) {
      return;
    }

    const timer = window.setInterval(() => {
      setSelectedFrameSlot((currentSlot) => {
        if (currentSlot === null) {
          return frameSlots[0] ?? null;
        }

        const currentIndex = frameSlots.indexOf(currentSlot);
        const nextIndex =
          currentIndex < 0 || currentIndex >= frameSlots.length - 1
            ? 0
            : currentIndex + 1;
        return frameSlots[nextIndex] ?? currentSlot;
      });
    }, 100);

    return () => window.clearInterval(timer);
  }, [frameSlots, isFramePlaying]);

  useEffect(() => {
    if (!recordsOpen) {
      setIsFramePlaying(false);
    }
  }, [recordsOpen]);

  useEffect(() => {
    const ws = connectIfNeeded();

    return () => {
      try {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: "stop" }));
        }
        ws.close();
      } catch {
        // ignore close errors
      }
      wsRef.current = null;
    };
  }, [projectId]);

  return (
    <main className="w-full h-screen relative font-sans overflow">
      <div className="absolute inset-0 flex flex-col p-20 z-20">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div className="flex gap-3 items-center justify-center">
            <h1 className="text-3xl font-bold tracking-tight">
              Project Workspace
            </h1>
            <p className="text-sm opacity-80">(Project ID: {projectId})</p>
            <p className="text-sm opacity-80">
              (Simulation: {simStatus}, Slot: {tickCount})
            </p>
            {simError ? (
              <p className="text-sm text-red-600">(Error: {simError})</p>
            ) : null}
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="rounded-md border px-4 py-2 text-sm"
            >
              <ArrowLeftIcon className="h-4 w-4" />
            </Link>

            <Link href="/" className="rounded-md border px-4 py-2 text-sm">
              <HomeIcon className="h-4 w-4" />
            </Link>
            {simStatus !== "running" ? (
              <button
                onClick={handlePlay}
                className="rounded-md border px-4 py-2 text-sm"
                title="Play simulation"
              >
                <PlayIcon className="h-4 w-4" />
              </button>
            ) : (
              <button
                onClick={handlePause}
                className="rounded-md border px-4 py-2 text-sm"
                title="Pause simulation"
              >
                <PauseIcon className="h-4 w-4" />
              </button>
            )}
            <button className="rounded-md border px-4 py-2 text-sm">
              <InboxIcon className="h-4 w-4" />
            </button>
            <button
              onClick={handleToggleRecords}
              className="rounded-md border px-4 py-2 text-sm"
              title="Show simulation records"
            >
              <VideoCameraIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

        {recordsOpen ? (
          <section className="w-full flex flex-col text-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Simulation Records</h2>
              <button className="px-2 py-1" onClick={() => loadRecords(true)}>
                <ArrowPathIcon className="h-4 w-4" />
              </button>
            </div>

            {recordsLoading ? <p>Loading records...</p> : null}
            {recordsError ? (
              <p className="text-red-600">Error: {recordsError}</p>
            ) : null}

            <div className="w-full flex items-center gap-6 justify-center">
              {!recordsLoading && !recordsError ? (
                <div className="w-full max-h-100 overflow-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-black/5 text-left">
                        <th className="px-3 py-2">Record ID</th>
                        <th className="px-3 py-2">Status</th>
                        <th className="px-3 py-2">Started</th>
                        <th className="px-3 py-2">Ended</th>
                      </tr>
                    </thead>
                    <tbody>
                      {records.map((r) => (
                        <tr
                          key={r.id}
                          className={`border-t cursor-pointer hover:bg-black/5 ${selectedRecordId === r.id ? "bg-black/5" : ""}`}
                          onClick={() => handleSelectRecord(r.id)}
                        >
                          <td className="px-3 py-2">{r.id}</td>
                          <td className="px-3 py-2">{r.status}</td>
                          <td className="px-3 py-2">
                            {r.started_at
                              ? new Date(r.started_at).toLocaleString()
                              : "-"}
                          </td>
                          <td className="px-3 py-2">
                            {r.ended_at
                              ? new Date(r.ended_at).toLocaleString()
                              : "-"}
                          </td>
                        </tr>
                      ))}
                      {records.length === 0 ? (
                        <tr>
                          <td className="px-3 py-3 opacity-70" colSpan={4}>
                            No records yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              ) : null}

              {selectedRecordId ? (
                <div className="mt-4 p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="text-sm font-semibold">
                      Record ID - {selectedRecordId} Demonstration
                    </h3>
                    <button
                      className="px-2 py-1"
                      onClick={() => loadRecordSeries(selectedRecordId, true)}
                    >
                      <ArrowPathIcon className="h-4 w-4" />
                    </button>
                  </div>

                  {recordSeriesLoading ? <p>Loading record series...</p> : null}
                  {recordSeriesError ? (
                    <p className="text-red-600">Error: {recordSeriesError}</p>
                  ) : null}

                  {!recordSeriesLoading &&
                  !recordSeriesError &&
                  recordSeries ? (
                    <div>
                      <div className="relative w-full my-2">
                        <div className="absolute inset-0 z-20">
                          <div className="relative h-1 overflow-hidden bg-white/20">
                            <div
                              className="h-full bg-white/80 transition-all duration-200"
                              style={{
                                width:
                                  frameSlots.length <= 1 ||
                                  selectedFrameIndex < 0
                                    ? "100%"
                                    : `${(selectedFrameIndex / (frameSlots.length - 1)) * 100}%`,
                              }}
                            />
                          </div>
                        </div>
                        <RecordFrameWidget satellites={frameSatellites} />
                      </div>
                      <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                        <div className="rounded  p-2">
                          <p className="text-xs opacity-70">State points</p>
                          <p className="text-lg font-semibold">
                            {recordSeries.state_points?.length ?? 0}
                          </p>
                        </div>
                        <div className="rounded  p-2">
                          <p className="text-xs opacity-70">Entity points</p>
                          <p className="text-lg font-semibold">
                            {recordSeries.entity_points?.length ?? 0}
                          </p>
                        </div>
                        <div className="rounded  p-2">
                          <p className="text-xs opacity-70">Record status</p>
                          <p className="text-lg font-semibold">
                            {recordSeries.record?.status ?? "-"}
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          </section>
        ) : null}
      </div>
    </main>
  );
}
