import { useEffect, useMemo, useRef, useState } from "react";
import type { SatellitePoint, SimulationStatus, StationPoint } from "./simulation.model";

type UseSimulationControllerArgs = {
  projectId: string;
};

export function useSimulationController({ projectId }: UseSimulationControllerArgs) {
  const wsRef = useRef<WebSocket | null>(null);

  const [status, setStatus] = useState<SimulationStatus>("idle");
  const [tickCount, setTickCount] = useState(0);
  const [maxSlot, setMaxSlot] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [satellites, setSatellites] = useState<SatellitePoint[]>([]);
  const [stations, setStations] = useState<StationPoint[]>([]);

  const apiBase = useMemo(() => process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000", []);
  const wsBase = useMemo(() => {
    if (apiBase.startsWith("https://")) return apiBase.replace("https://", "wss://");
    return apiBase.replace("http://", "ws://");
  }, [apiBase]);

  const connectIfNeeded = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return wsRef.current;
    }

    const ws = new WebSocket(`${wsBase}/api/simulation/ws/${projectId}`);
    ws.onopen = () => {
      setStatus("connected");
      setError(null);
    };

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        console.debug("Received WebSocket message:", msg);
        if (msg?.type === "error") {
          setStatus("error");
          setError(msg?.message ?? "Simulation engine error");
          return;
        }

        if (msg?.type === "state") {
          const state = msg.state ?? {};
          setTickCount(state.slot_count ?? 0);
          const nextMaxSlot = Number(state.maximum_slot);
          setMaxSlot(Number.isFinite(nextMaxSlot) && nextMaxSlot > 0 ? nextMaxSlot : null);
          setStatus("running");

          const nextSatellites: SatellitePoint[] = [];
          const nextStations: StationPoint[] = [];
          for (const entity of state.entities ?? []) {
            if (!entity || typeof entity !== "object") continue;
            const entityType = entity.type;
            if (entityType !== "earth_satellite") continue;

            const x = Number(entity.x);
            const y = Number(entity.y);
            const z = Number(entity.z);
            if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) continue;

            nextSatellites.push({ id: String(entity.id ?? entity.address ?? "unknown"), x, y, z });
          }
          setSatellites(nextSatellites);
          for (const entity of state.entities ?? []) {
            if (!entity || typeof entity !== "object") continue;
            const entityType = entity.type;
            if (entityType !== "ground_station") continue;

            const x = Number(entity.x);
            const y = Number(entity.y);
            const z = Number(entity.z);
            if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) continue;

            nextStations.push({ id: String(entity.id ?? entity.name ?? "unknown"), x, y, z });
          }
          setStations(nextStations);
        }
      } catch {
        // ignore invalid payload
      }
    };

    ws.onclose = () => {
      setStatus((prev) => (prev === "stopped" ? "stopped" : "closed"));
      wsRef.current = null;
    };

    ws.onerror = () => {
      setStatus("error");
      setError("WebSocket error");
    };

    wsRef.current = ws;
    return ws;
  };

  const play = () => {
    const ws = connectIfNeeded();
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "play" }));
      setStatus("running");
      return;
    }

    ws.addEventListener(
      "open",
      () => {
        ws.send(JSON.stringify({ action: "play" }));
        setStatus("running");
      },
      { once: true },
    );
  };

  const pause = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "pause" }));
      setStatus("paused");
    }
  };

  const stop = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "stop" }));
    }
    setStatus("stopped");
    setTickCount(0);
    setSatellites([]);
    setStations([]);
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

  return {
    status,
    tickCount,
    maxSlot,
    error,
    satellites,
    stations,
    play,
    pause,
    stop,
  };
}
