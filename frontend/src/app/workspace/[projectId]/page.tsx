"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeftIcon, HomeIcon, InboxIcon, PlayIcon, PauseIcon } from "@heroicons/react/24/outline";
import Link from "next/link";

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const wsRef = useRef<WebSocket | null>(null);
  const [simStatus, setSimStatus] = useState("idle");
  const [tickCount, setTickCount] = useState(0);
  const [simError, setSimError] = useState<string | null>(null);

  const wsBase = useMemo(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    if (apiBase.startsWith("https://")) return apiBase.replace("https://", "wss://");
    return apiBase.replace("http://", "ws://");
  }, []);

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
          setTickCount(msg.state?.tick_count ?? 0);
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
            <p className="text-sm opacity-80">(Simulation: {simStatus}, tick: {tickCount})</p>
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
          </div>
        </div>
      </div>
    </main>
  );
}
