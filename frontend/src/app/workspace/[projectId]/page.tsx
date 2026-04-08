"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeftIcon, HomeIcon, InboxIcon, PlayIcon, PauseIcon, VideoCameraIcon } from "@heroicons/react/24/outline";
import Link from "next/link";

type SimulationRecord = {
  id: number;
  project_id: number;
  status: string;
  started_at: string;
  ended_at?: string | null;
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

  const apiBase = useMemo(() => {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }, []);

  const wsBase = useMemo(() => {
    if (apiBase.startsWith("https://")) return apiBase.replace("https://", "wss://");
    return apiBase.replace("http://", "ws://");
  }, [apiBase]);

  const loadRecords = async () => {
    try {
      setRecordsLoading(true);
      setRecordsError(null);
      const resp = await fetch(`${apiBase}/api/simulation/records/${projectId}?limit=200`, {
        cache: "no-store",
      });
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      const payload = await resp.json();
      setRecords(payload?.records ?? []);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch records";
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
      { once: true }
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
    <main className="w-full h-screen relative font-sans overflow-hidden">
      <div className="absolute inset-0 flex flex-col p-20 z-20">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div className="flex gap-3 items-center justify-center">
            <h1 className="text-3xl font-bold tracking-tight">
              Project Workspace
            </h1>
            <p className="text-sm opacity-80">(Project ID: {projectId})</p>
            <p className="text-sm opacity-80">(Simulation: {simStatus}, Slot: {tickCount})</p>
            {simError ? <p className="text-sm text-red-600">(Error: {simError})</p> : null}
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
          <section className="w-full max-w-3xl rounded-lg border bg-white/90 p-4 text-sm shadow">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-base font-semibold">Simulation Records (Project {projectId})</h2>
              <button className="rounded border px-2 py-1" onClick={loadRecords}>
                Refresh
              </button>
            </div>

            {recordsLoading ? <p>Loading records...</p> : null}
            {recordsError ? <p className="text-red-600">Error: {recordsError}</p> : null}

            {!recordsLoading && !recordsError ? (
              <div className="max-h-80 overflow-auto rounded border">
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
                      <tr key={r.id} className="border-t">
                        <td className="px-3 py-2">{r.id}</td>
                        <td className="px-3 py-2">{r.status}</td>
                        <td className="px-3 py-2">{r.started_at ? new Date(r.started_at).toLocaleString() : "-"}</td>
                        <td className="px-3 py-2">{r.ended_at ? new Date(r.ended_at).toLocaleString() : "-"}</td>
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
          </section>
        ) : null}
      </div>
    </main>
  );
}
