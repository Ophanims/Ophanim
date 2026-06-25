import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { EarthPoint, LinkPoint, SatellitePoint, SimulationStatus, StationPoint, SunPoint } from "@/app/simulation/[projectId]/simulation.model";

type UseSimulationControllerArgs = {
  projectId: string;
};

export function useSimulationController({ projectId }: UseSimulationControllerArgs) {
  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const dialogResolvedRef = useRef(false);
  const hasReceivedStateRef = useRef(false);

  const [status, setStatus] = useState<SimulationStatus>("idle");
  const [tickCount, setTickCount] = useState(0);
  const [maxSlot, setMaxSlot] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [satellites, setSatellites] = useState<SatellitePoint[]>([]);
  const [stations, setStations] = useState<StationPoint[]>([]);
  const [links, setLinks] = useState<LinkPoint[]>([]);
  const [sun, setSun] = useState<SunPoint | null>(null);
  const [earth, setEarth] = useState<EarthPoint | null>(null);
  const [showSaveDialog, setShowSaveDialog] = useState(false);

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
      setShowSaveDialog(false);
      dialogResolvedRef.current = false;
      hasReceivedStateRef.current = false;
    };

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        console.debug("Received WebSocket message:", msg);
        if (msg?.type === "connected") {
          return;
        }
        if (msg?.type === "simulation_ended") {
          sessionIdRef.current = msg.sessionId ?? null;
          if (!dialogResolvedRef.current && hasReceivedStateRef.current) {
            setShowSaveDialog(true);
          }
          return;
        }
        if (msg?.type === "session_created") {
          sessionIdRef.current = msg.sessionId ?? null;
          return;
        }
        if (msg?.type === "error") {
          setStatus("error");
          setError(msg?.message ?? "Simulation engine error");
          return;
        }

        if (msg?.type === "state") {
          hasReceivedStateRef.current = true;
          const state = msg.state ?? {};
          setTickCount(state.clock.slot_count ?? 0);
          const nextMaxSlot = Number(state.clock.maximum_slot);
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
                nullIslandX: Number(entity.null_island_x ?? 0),
                nullIslandY: Number(entity.null_island_z ?? 0),
                nullIslandZ: - Number(entity.null_island_y ?? 0),
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
      setStatus((prev) => {
        if (prev === "stopped" || prev === "closed") return prev;
        return "closed";
      });
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
    setShowSaveDialog(true);
  };

  const doCleanup = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "stop" }));
    }
    setStatus("stopped");
    setTickCount(0);
    setSatellites([]);
    setStations([]);
    setLinks([]);
  }, []);

  // 保存：先停止引擎（引擎会发送 simulation_ended 包含 sessionId），再写入 DB
  const handleSave = useCallback(async () => {
    setShowSaveDialog(false);
    dialogResolvedRef.current = true;
    doCleanup(); // 先停止引擎，确保 temp file 完整
    // 等 simulation_ended 消息到达并设置 sessionIdRef，再读 sid
    await new Promise((r) => setTimeout(r, 500));
    const sid = sessionIdRef.current;
    if (sid) {
      try {
        const resp = await fetch(`${apiBase}/api/simulation/record/${sid}/save?status=completed`, { method: "POST" });
        if (!resp.ok) {
          const text = await resp.text();
          console.error("Save failed:", resp.status, text);
          setError(`Save failed (${resp.status})`);
        } else {
          const data = await resp.json();
          console.log("Record saved:", data);
        }
      } catch (err) {
        console.error("Save error:", err);
        setError(String(err));
      }
    } else {
      console.error("Save skipped: no sessionId");
      setError("Save skipped: no session ID");
    }
  }, [apiBase, doCleanup, setError]);

  // 丢弃：先停止引擎，再删除 temp file
  const handleDiscard = useCallback(async () => {
    setShowSaveDialog(false);
    dialogResolvedRef.current = true;
    doCleanup();
    await new Promise((r) => setTimeout(r, 500));
    const sid = sessionIdRef.current;
    if (sid) {
      try {
        await fetch(`${apiBase}/api/simulation/record/${sid}/discard`, { method: "POST" });
      } catch {
        // ignore
      }
    }
  }, [apiBase, doCleanup]);

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
    showSaveDialog,
    play,
    pause,
    stop,
    onSave: handleSave,
    onDiscard: handleDiscard,
  };
}
