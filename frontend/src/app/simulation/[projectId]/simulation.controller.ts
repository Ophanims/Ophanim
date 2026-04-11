import { useEffect, useMemo, useRef, useState } from "react";
import type { EarthPoint, LinkPoint, SatellitePoint, SimulationStatus, StationPoint, SunPoint } from "@/app/simulation/[projectId]/simulation.model";

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
  const [links, setLinks] = useState<LinkPoint[]>([]);
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
          setStatus((prevStatus) =>
            prevStatus === "paused" || prevStatus === "stopped" ? prevStatus : "running"
          );

          const nextStations: StationPoint[] = [];
          const nextSatellites: SatellitePoint[] = [];
          const nextLinks: LinkPoint[] = [];

          for (const entity of state.entities ?? []) {
            if (!entity || typeof entity !== "object") continue;
            const entityType = entity.type;

            if (entityType === "the_earth") {
              const r = Number(entity.rotational_angular_velocity)
              setEarth({
                addr: String(entity.addr ?? "earth"),
                nullIslandX: Number(entity.nullIslandX ?? 0),
                nullIslandY: Number(entity.nullIslandZ ?? 0),
                nullIslandZ: - Number(entity.nullIslandY ?? 0),
                rotationalAngularVelocity: Number.isFinite(r) ? r : 0,
              });
              continue;
            } else if (entityType === "the_sun") {
              setSun({
                addr: String(entity.addr ?? "sun"),
                x: Number(entity.x ?? 0),
                y: Number(entity.z ?? 0),
                z: - Number(entity.y ?? 0),
              });
              continue;
            } else if (entityType === "earth_satellite") {
              const sat: SatellitePoint = {
                addr: String(entity.addr ?? "unknown"),
                type: String(entity.type ?? "unknown"),
                id: String(entity.id ?? "unknown"),
                plane: Number(entity.plane ?? 0),
                order: Number(entity.order ?? 0),
                x: Number(entity.x ?? 0),
                y: Number(entity.z ?? 0),
                z: - Number(entity.y ?? 0),
                velocityVector: [
                  Number(entity.velocityVectorX ?? 0),
                  Number(entity.velocityVectorZ ?? 0),
                  - Number(entity.velocityVectorY ?? 0),
                ] as [number, number, number],
                solarVector: [
                  Number(entity.solarVectorX ?? 0),
                  Number(entity.solarVectorZ ?? 0),
                  - Number(entity.solarVectorY ?? 0),
                ] as [number, number, number],
                corLat1: Number(entity.corLat1 ?? 0),
                corLon1: Number(entity.corLon1 ?? 0),
                corLat2: Number(entity.corLat2 ?? 0),
                corLon2: Number(entity.corLon2 ?? 0),
                corLat3: Number(entity.corLat3 ?? 0),
                corLon3: Number(entity.corLon3 ?? 0),
                corLat4: Number(entity.corLat4 ?? 0),
                corLon4: Number(entity.corLon4 ?? 0),
                corX1: Number(entity.corX1 ?? 0),
                corY1: Number(entity.corZ1 ?? 0),
                corZ1: - Number(entity.corY1 ?? 0),
                corX2: Number(entity.corX2 ?? 0),
                corY2: Number(entity.corZ2 ?? 0),
                corZ2: - Number(entity.corY2 ?? 0),
                corX3: Number(entity.corX3 ?? 0),
                corY3: Number(entity.corZ3 ?? 0),
                corZ3: - Number(entity.corY3 ?? 0),
                corX4: Number(entity.corX4 ?? 0),
                corY4: Number(entity.corZ4 ?? 0),
                corZ4: - Number(entity.corY4 ?? 0),
                batteryLevel: Number(entity.batteryLevel ?? 0),
                processorClockFrequency: Number(entity.processorClockFrequency ?? 0),
                onROI: Boolean(entity.onROI ?? false),
                onSUN: Boolean(entity.onSUN ?? false),
                onSGL: Boolean(entity.onSGL ?? false),
                onISL: Boolean(entity.onISL ?? false),
                onCOM: Boolean(entity.onCOM ?? false),
              };
              nextSatellites.push(sat);
              continue;
            } else if (entityType === "ground_station") {
              const x = Number(entity.x ?? 0);
              const y = Number(entity.z ?? 0);
              const z = - Number(entity.y ?? 0);
              const gs: StationPoint = {
                addr: String(entity.addr ?? "unknown"),
                x,
                y,
                z,
              };
              nextStations.push(gs);
            }
          }

          for (const link of state.links ?? []) {
            if (!link || typeof link !== "object") continue;
            const id = String(link.id ?? "unknown");
            const type = String(link.type ?? "unknown");
            const status = String(link.status ?? "unknown");
            const distance = Number(link.distance ?? 0);
            const capacity = Number(link.capacity ?? 0);
            const srcId = String(link.src ?? "unknown");
            const dstId = String(link.dst ?? "unknown");
            var src: SatellitePoint | StationPoint | undefined;
            var dst: SatellitePoint | StationPoint | undefined;
            if (type === "ISL") {
              src = nextSatellites.find((s) => s.addr === srcId);
              dst = nextSatellites.find((s) => s.addr === dstId);
            } else {
              src = nextSatellites.find((s) => s.addr === srcId)
              if (!src) {
                src = nextStations.find((s) => s.addr === srcId)
              }
              dst = nextStations.find((s) => s.addr === dstId)
              if (!dst) {
                dst = nextSatellites.find((s) => s.addr === dstId)
              }
            }

            if (src && dst) {
              const srcX = Number(src.x ?? 0);
              const srcY = Number(src.y ?? 0);
              const srcZ = Number(src.z ?? 0);
              const dstX = Number(dst.x ?? 0);
              const dstY = Number(dst.y ?? 0);
              const dstZ = Number(dst.z ?? 0);
              const l: LinkPoint = { id: id, type: type, status: status, distance: distance, capacity: capacity, srcId: srcId, dstId: dstId, srcX: srcX, srcY: srcY, srcZ: srcZ, dstX: dstX, dstY: dstY, dstZ: dstZ };
              nextLinks.push(l);
            }

          }

          setSatellites(nextSatellites);
          setStations(nextStations);
          setLinks(nextLinks);
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
    setLinks([]);
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
    links,
    play,
    pause,
    stop,
  };
}
