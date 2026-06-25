import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  EarthPoint,
  LinkPoint,
  RecordSeriesPayload,
  SatellitePoint,
  StationPoint,
  SunPoint,
} from "./record.model";

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
  const [playing, setPlaying] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  // 整体记录的总 slot 数（从 state_points 的 maximum_slot 获取）
  const totalSlots = useMemo(() => {
    const points = recordSeries?.state_points ?? [];
    for (const p of points) {
      if (typeof p.maximum_slot === "number" && p.maximum_slot > 0) return p.maximum_slot;
    }
    return 0;
  }, [recordSeries]);

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

  // 可用帧列表（已加载的 slot 去重排序）
  const frameSlots = useMemo(() => {
    const points = recordSeries?.state_points ?? [];
    const slots = new Set<number>();
    for (const p of points) {
      if (typeof p.slot_count === "number") slots.add(p.slot_count);
    }
    return Array.from(slots).sort((a, b) => a - b);
  }, [recordSeries]);

  // 当前帧在前端的帧列表中的索引
  const frameIndex = useMemo(() => {
    if (selectedFrameSlot === null) return -1;
    return frameSlots.indexOf(selectedFrameSlot);
  }, [frameSlots, selectedFrameSlot]);

  // 当前帧对应的卫星快照（坐标转换与 simulation.controller.ts 一致）
  const satellites = useMemo(() => {
    if (!recordSeries || selectedFrameSlot === null) return [];
    const out: SatellitePoint[] = [];
    for (const p of recordSeries.entity_points ?? []) {
      if (p.slot_count !== selectedFrameSlot) continue;
      const payload = p.payload;
      const entityType = payload?.type ?? p.entity_type;
      if (!payload || (entityType !== "satellite" && entityType !== "earth_satellite")) continue;

      const x = Number(payload.x);
      const y = Number(payload.z);        // backend z → scene y
      const z = -Number(payload.y);       // backend y → scene -z
      if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) continue;
      out.push({
        addr: String(p.entity_id ?? payload.id ?? "unknown"),
        type: String(payload.type ?? p.entity_type ?? "earth_satellite"),
        id: String(payload.id ?? p.entity_id ?? "unknown"),
        plane: Number(payload.plane ?? 0),
        order: Number(payload.order ?? 0),
        x,
        y,
        z,
        velocityVector: [
          Number(payload.velocityVectorX ?? 0),
          Number(payload.velocityVectorZ ?? 0),
          -Number(payload.velocityVectorY ?? 0),
        ] as [number, number, number],
        solarVector: [
          Number(payload.solarVectorX ?? 0),
          Number(payload.solarVectorZ ?? 0),
          -Number(payload.solarVectorY ?? 0),
        ] as [number, number, number],
        corLat1: Number(payload.corLat1 ?? 0),
        corLon1: Number(payload.corLon1 ?? 0),
        corLat2: Number(payload.corLat2 ?? 0),
        corLon2: Number(payload.corLon2 ?? 0),
        corLat3: Number(payload.corLat3 ?? 0),
        corLon3: Number(payload.corLon3 ?? 0),
        corLat4: Number(payload.corLat4 ?? 0),
        corLon4: Number(payload.corLon4 ?? 0),
        corX1: Number(payload.corX1 ?? 0),
        corY1: Number(payload.corZ1 ?? 0),
        corZ1: -Number(payload.corY1 ?? 0),
        corX2: Number(payload.corX2 ?? 0),
        corY2: Number(payload.corZ2 ?? 0),
        corZ2: -Number(payload.corY2 ?? 0),
        corX3: Number(payload.corX3 ?? 0),
        corY3: Number(payload.corZ3 ?? 0),
        corZ3: -Number(payload.corY3 ?? 0),
        corX4: Number(payload.corX4 ?? 0),
        corY4: Number(payload.corZ4 ?? 0),
        corZ4: -Number(payload.corY4 ?? 0),
        batteryLevel: Number(payload.batteryLevel ?? 0),
        processorClockFrequency: Number(payload.processorClockFrequency ?? 0),
        onROI: Boolean(payload.onROI ?? false),
        onSUN: Boolean(payload.onSUN ?? false),
        onSGL: Boolean(payload.onSGL ?? false),
        onISL: Boolean(payload.onISL ?? false),
        onCOM: Boolean(payload.onCOM ?? false),
      });
    }
    return out;
  }, [recordSeries, selectedFrameSlot]);

  // 当前帧对应的太阳
  const sun = useMemo<SunPoint | null>(() => {
    if (!recordSeries || selectedFrameSlot === null) return null;
    for (const p of recordSeries.entity_points ?? []) {
      if (p.slot_count !== selectedFrameSlot) continue;
      const payload = p.payload;
      if (!payload || payload.type !== "the_sun") continue;
      return {
        addr: String(payload.addr ?? "sun"),
        x: Number(payload.x ?? 0),
        y: Number(payload.z ?? 0),
        z: -Number(payload.y ?? 0),
      };
    }
    return null;
  }, [recordSeries, selectedFrameSlot]);

  // 当前帧对应的地球
  const earth = useMemo<EarthPoint | null>(() => {
    if (!recordSeries || selectedFrameSlot === null) return null;
    for (const p of recordSeries.entity_points ?? []) {
      if (p.slot_count !== selectedFrameSlot) continue;
      const payload = p.payload;
      if (!payload || payload.type !== "the_earth") continue;
      return {
        addr: String(payload.addr ?? "earth"),
        nullIslandX: Number(payload.null_island_x ?? 0),
        nullIslandY: Number(payload.null_island_z ?? 0),
        nullIslandZ: -Number(payload.null_island_y ?? 0),
        rotationalAngularVelocity: Number(payload.rotational_angular_velocity ?? 0),
      };
    }
    return null;
  }, [recordSeries, selectedFrameSlot]);

  // 当前帧对应的地面站
  const stations = useMemo<StationPoint[]>(() => {
    if (!recordSeries || selectedFrameSlot === null) return [];
    const out: StationPoint[] = [];
    for (const p of recordSeries.entity_points ?? []) {
      if (p.slot_count !== selectedFrameSlot) continue;
      const payload = p.payload;
      if (!payload || payload.type !== "ground_station") continue;
      out.push({
        addr: String(payload.addr ?? "unknown"),
        x: Number(payload.x ?? 0),
        y: Number(payload.z ?? 0),
        z: -Number(payload.y ?? 0),
      });
    }
    return out;
  }, [recordSeries, selectedFrameSlot]);

  // 当前帧对应的链路（从 state_points payload.links 中提取，并匹配实体坐标）
  const links = useMemo<LinkPoint[]>(() => {
    if (!recordSeries || selectedFrameSlot === null) return [];
    const statePoint = (recordSeries.state_points ?? []).find(
      (sp) => sp.slot_count === selectedFrameSlot,
    );
    const rawLinks = statePoint?.payload?.links ?? [];
    if (rawLinks.length === 0) return [];

    // 构建 addr → { x, y, z } 的查找表
    const entityPos = new Map<string, { x: number; y: number; z: number }>();
    for (const p of recordSeries.entity_points ?? []) {
      if (p.slot_count !== selectedFrameSlot) continue;
      const payload = p.payload;
      if (!payload) continue;
      const addr = String(payload.addr ?? p.entity_id ?? "");
      if (!addr) continue;
      entityPos.set(addr, {
        x: Number(payload.x ?? 0),
        y: Number(payload.z ?? 0),
        z: -Number(payload.y ?? 0),
      });
    }

    const out: LinkPoint[] = [];
    for (const raw of rawLinks) {
      const type = String(raw.type ?? "");
      const srcId = String(raw.src ?? "");
      const dstId = String(raw.dst ?? "");
      const src = entityPos.get(srcId);
      const dst = entityPos.get(dstId);
      if (!src || !dst) continue;
      out.push({
        id: String(raw.id ?? ""),
        type,
        status: String(raw.status ?? false),
        distance: Number(raw.distance ?? 0),
        capacity: Number(raw.capacity ?? 0),
        srcId,
        dstId,
        srcX: src.x,
        srcY: src.y,
        srcZ: src.z,
        dstX: dst.x,
        dstY: dst.y,
        dstZ: dst.z,
      });
    }
    return out;
  }, [recordSeries, selectedFrameSlot]);

  // —— 预取（播放到当前窗口尾部时加载下一段）——
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

  // —— 自动播放下一个帧 ——
  useEffect(() => {
    if (!playing || frameSlots.length === 0) return;
    const timer = window.setInterval(() => {
      setSelectedFrameSlot((currentSlot) => {
        if (currentSlot === null) return frameSlots[0] ?? null;
        const idx = frameSlots.indexOf(currentSlot);
        if (idx < 0) return frameSlots[0] ?? null;
        if (idx < frameSlots.length - 1) return frameSlots[idx + 1] ?? currentSlot;
        if (hasMore) return currentSlot; // 等待预取完成
        return currentSlot; // 播完后保持最后一帧
      });
    }, 100);

    return () => window.clearInterval(timer);
  }, [frameSlots, hasMore, playing]);

  // —— 播放完毕时停止 ——
  useEffect(() => {
    if (!playing || hasMore || frameSlots.length === 0 || selectedFrameSlot === null) return;
    const idx = frameSlots.indexOf(selectedFrameSlot);
    if (idx === frameSlots.length - 1) {
      setPlaying(false);
      setSelectedFrameSlot(frameSlots[0] ?? null);
    }
  }, [playing, hasMore, frameSlots, selectedFrameSlot]);

  // 初始化时自动播放
  useEffect(() => {
    if (!loading && !buffering && frameSlots.length > 0 && selectedFrameSlot === null) {
      setSelectedFrameSlot(frameSlots[0] ?? null);
      setPlaying(true);
    }
  }, [loading, buffering, frameSlots, selectedFrameSlot]);

  // —— 跳转到某个百分比位置 ——
  const seekToPercent = useCallback((percent: number) => {
    if (frameSlots.length === 0) return;

    // 计算目标 slot
    let targetSlot: number;
    if (totalSlots > 0 && hasMore) {
      // 知道总条数：按比例算出 slot
      targetSlot = Math.round((percent / 100) * totalSlots);
    } else {
      // 不知道总条数：按已加载的帧比例算
      const idx = Math.round((percent / 100) * (frameSlots.length - 1));
      targetSlot = frameSlots[Math.max(0, Math.min(idx, frameSlots.length - 1))];
      setSelectedFrameSlot(targetSlot);
      setPlaying(true);
      return;
    }

    // 查找已加载范围内最接近的 slot
    const closest = frameSlots.reduce((best, s) =>
      Math.abs(s - targetSlot) < Math.abs(best - targetSlot) ? s : best,
    );

    // 如果目标 slot 远超出当前窗口，加载对应区间
    const loadNeeded =
      targetSlot < frameSlots[0] ||
      targetSlot > frameSlots[frameSlots.length - 1] ||
      Math.abs(closest - targetSlot) > WINDOW_SLOT_LIMIT;

    if (loadNeeded) {
      const windowStart = Math.max(0, targetSlot - Math.floor(WINDOW_SLOT_LIMIT / 2));
      setLoading(true);
      loadSeriesWindow(windowStart, WINDOW_SLOT_LIMIT, "initial").then(() => {
        // 加载后重新在 frameSlots 中找最近 slot（useState 更新后自动触发）
      });
    }

    setSelectedFrameSlot(closest);
    setPlaying(true);
  }, [frameSlots, hasMore, loadSeriesWindow, totalSlots]);

  // 数据加载完成后，如果 selectedFrameSlot 不在 frameSlots 中（如 seek 后新数据到），跳到最近
  useEffect(() => {
    if (selectedFrameSlot === null || frameSlots.length === 0) return;
    if (!frameSlots.includes(selectedFrameSlot)) {
      const closest = frameSlots.reduce((best, s) =>
        Math.abs(s - selectedFrameSlot) < Math.abs(best - selectedFrameSlot) ? s : best,
      );
      setSelectedFrameSlot(closest);
    }
  }, [frameSlots, selectedFrameSlot]);

  return {
    loading,
    buffering,
    error,
    recordSeries,
    frameSlots,
    satellites,
    sun,
    earth,
    stations,
    links,
    frameIndex,
    playing,
    hasMore,
    totalSlots,
    setPlaying,
    loadSeries,
    seekToPercent,
  };
}
