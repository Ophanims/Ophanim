"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "ophanim-timeseries-cache-v1";

type CacheEntry<T> = {
  ts: number;
  value: T;
};

type TimeseriesCache = {
  projectRecords: Record<string, CacheEntry<unknown[]>>;
  recordSeries: Record<string, CacheEntry<unknown>>;
};

const EMPTY_CACHE: TimeseriesCache = {
  projectRecords: {},
  recordSeries: {},
};

function sortedKeysByTs<T>(obj: Record<string, CacheEntry<T>>): string[] {
  return Object.entries(obj)
    .sort((a, b) => b[1].ts - a[1].ts)
    .map(([key]) => key);
}

function shrinkCacheForQuota(input: TimeseriesCache): TimeseriesCache {
  const recordKeys = sortedKeysByTs(input.recordSeries).slice(0, 2);
  const projectKeys = sortedKeysByTs(input.projectRecords).slice(0, 10);

  const recordSeries: TimeseriesCache["recordSeries"] = {};
  for (const k of recordKeys) {
    recordSeries[k] = input.recordSeries[k];
  }

  const projectRecords: TimeseriesCache["projectRecords"] = {};
  for (const k of projectKeys) {
    projectRecords[k] = input.projectRecords[k];
  }

  return { projectRecords, recordSeries };
}

function readInitialCache(): TimeseriesCache {
  if (typeof window === "undefined") return EMPTY_CACHE;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY_CACHE;
    const parsed = JSON.parse(raw) as TimeseriesCache;
    return {
      projectRecords: parsed.projectRecords ?? {},
      recordSeries: parsed.recordSeries ?? {},
    };
  } catch {
    return EMPTY_CACHE;
  }
}

export function useTimeseriesStorage() {
  const [cache, setCache] = useState<TimeseriesCache>(EMPTY_CACHE);

  useEffect(() => {
    setCache(readInitialCache());
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(cache));
    } catch {
      // Best-effort persistence: shrink cache and retry once when quota is exceeded.
      try {
        const shrunk = shrinkCacheForQuota(cache);
        window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(shrunk));
        setCache(shrunk);
      } catch {
        // If still failing, keep runtime state only and skip persistence.
      }
    }
  }, [cache]);

  const getProjectRecords = useCallback(<T,>(projectId: string, maxAgeMs = 30_000): T[] | null => {
    const entry = cache.projectRecords[projectId];
    if (!entry) return null;
    if (Date.now() - entry.ts > maxAgeMs) return null;
    return (entry.value as T[]) ?? null;
  }, [cache.projectRecords]);

  const setProjectRecords = useCallback(<T,>(projectId: string, records: T[]) => {
    setCache((prev) => ({
      ...prev,
      projectRecords: {
        ...prev.projectRecords,
        [projectId]: { ts: Date.now(), value: records },
      },
    }));
  }, []);

  const getRecordSeries = useCallback(<T,>(recordId: number, maxAgeMs = 30_000): T | null => {
    const key = String(recordId);
    const entry = cache.recordSeries[key];
    if (!entry) return null;
    if (Date.now() - entry.ts > maxAgeMs) return null;
    return (entry.value as T) ?? null;
  }, [cache.recordSeries]);

  const setRecordSeries = useCallback(<T,>(recordId: number, series: T) => {
    const key = String(recordId);
    setCache((prev) => ({
      ...prev,
      recordSeries: {
        ...prev.recordSeries,
        [key]: { ts: Date.now(), value: series },
      },
    }));
  }, []);

  const clearProjectCache = useCallback((projectId: string) => {
    setCache((prev) => {
      const next = { ...prev.projectRecords };
      delete next[projectId];
      return { ...prev, projectRecords: next };
    });
  }, []);

  return useMemo(() => ({
    getProjectRecords,
    setProjectRecords,
    getRecordSeries,
    setRecordSeries,
    clearProjectCache,
  }), [
    clearProjectCache,
    getProjectRecords,
    getRecordSeries,
    setProjectRecords,
    setRecordSeries,
  ]);
}
