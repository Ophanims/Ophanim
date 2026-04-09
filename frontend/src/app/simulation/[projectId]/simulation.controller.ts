import { useEffect, useMemo, useRef, useState } from "react";
import type { EarthPoint, SatellitePoint, SimulationStatus, StationPoint, SunPoint } from "@/app/simulation/[projectId]/simulation.model";

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
  const [sun, setSun] = useState<SunPoint | null>(null);
  const [earth, setEarth] = useState<EarthPoint | null>(null);

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
        // console.debug("Received WebSocket message:", msg);
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

          const nextStations: StationPoint[] = [];
          const nextSatellites: SatellitePoint[] = [];

          for (const entity of state.entities ?? []) {
            if (!entity || typeof entity !== "object") continue;
            const entityType = entity.type;

            if (entityType === "the_earth") {
              const x0 = Number(entity.null_island_x);
              const y0 = Number(entity.null_island_y);
              const z0 = Number(entity.null_island_z);
              const r = Number(entity.rotational_angular_velocity)
              if (!Number.isFinite(x0) || !Number.isFinite(y0) || !Number.isFinite(z0)) continue;
              setEarth({
                id: String(entity.id ?? "earth"),
                nullIslandX: Number.isFinite(x0) ? x0 : 0,
                nullIslandY: Number.isFinite(y0) ? y0 : 0,
                nullIslandZ: Number.isFinite(z0) ? z0 : 0,
                rotationalAngularVelocity: Number.isFinite(r) ? r : 0,
              });
              continue;
            } else if (entityType === "the_sun") {
              const x = Number(entity.x);
              const y = Number(entity.y);
              const z = Number(entity.z);
              if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) continue;
              setSun({
                id: String(entity.id ?? "sun"),
                x: Number.isFinite(x) ? x : 0,
                y: Number.isFinite(y) ? y : 0,
                z: Number.isFinite(z) ? z : 0,
              });
              continue;
            } else if (entityType === "earth_satellite") {
              const x = Number(entity.x);
              const y = Number(entity.y);
              const z = Number(entity.z);
              if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) continue;
              nextSatellites.push({ id: String(entity.id ?? entity.address ?? "unknown"), x, y, z });
              continue;
            } else if (entityType === "ground_station") {
              const x = Number(entity.x);
              const y = Number(entity.y);
              const z = Number(entity.z);
              if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) continue;

              nextStations.push({ id: String(entity.id ?? entity.name ?? "unknown"), x, y, z });
            }
          }

          setSatellites(nextSatellites);
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
    earth,
    sun,
    satellites,
    stations,
    play,
    pause,
    stop,
  };
}
