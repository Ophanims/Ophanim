"use client";

import { useMemo, useState } from "react";

export const EARTH_MODE = {
  REALISTIC: "realistic",
  TEXTURE: "texture",
  SPHERE: "sphere",
  HIDDEN: "hidden",
} as const;

export const LATLON_MODE = {
  SHOW: "show",
  HIDDEN: "hidden",
} as const;

export const SATELLITE_MODE = {
  SHOW: "show",
  HIDDEN: "hidden",
} as const;

export type EarthMode = (typeof EARTH_MODE)[keyof typeof EARTH_MODE];
export type LatLonMode = (typeof LATLON_MODE)[keyof typeof LATLON_MODE];
export type SatelliteMode = (typeof SATELLITE_MODE)[keyof typeof SATELLITE_MODE];

export type FrameWidgetSettings = {
  earthMode: EarthMode;
  latLonMode: LatLonMode;
  satelliteMode: SatelliteMode;
  earthRotationSpeed: number;
  earthTransitionDuration: number;
};

export const EARTH_MODE_OPTIONS: Array<{ value: EarthMode; label: string }> = [
  { value: EARTH_MODE.REALISTIC, label: "REALISTIC" },
  { value: EARTH_MODE.TEXTURE, label: "TEXTURE" },
  { value: EARTH_MODE.SPHERE, label: "SPHERE" },
  { value: EARTH_MODE.HIDDEN, label: "HIDDEN" },
];

export const LATLON_MODE_OPTIONS: Array<{ value: LatLonMode; label: string }> = [
  { value: LATLON_MODE.SHOW, label: "SHOW" },
  { value: LATLON_MODE.HIDDEN, label: "HIDDEN" },
];

export const SATELLITE_MODE_OPTIONS: Array<{ value: SatelliteMode; label: string }> = [
  { value: SATELLITE_MODE.SHOW, label: "SHOW" },
  { value: SATELLITE_MODE.HIDDEN, label: "HIDDEN" },
];

type UseFrameWidgetSettingsArgs = Partial<FrameWidgetSettings>;

export function useFrameWidgetSettings(initial?: UseFrameWidgetSettingsArgs) {
  const [earthMode, setEarthMode] = useState<EarthMode>(initial?.earthMode ?? EARTH_MODE.REALISTIC);
  const [latLonMode, setLatLonMode] = useState<LatLonMode>(initial?.latLonMode ?? LATLON_MODE.HIDDEN);
  const [satelliteMode, setSatelliteMode] = useState<SatelliteMode>(initial?.satelliteMode ?? SATELLITE_MODE.SHOW);
  const [earthRotationSpeed, setEarthRotationSpeed] = useState<number>(initial?.earthRotationSpeed ?? 0.0012);
  const [earthTransitionDuration, setEarthTransitionDuration] = useState<number>(
    initial?.earthTransitionDuration ?? 0.35,
  );

  const settings = useMemo<FrameWidgetSettings>(
    () => ({
      earthMode,
      latLonMode,
      satelliteMode,
      earthRotationSpeed,
      earthTransitionDuration,
    }),
    [earthMode, latLonMode, satelliteMode, earthRotationSpeed, earthTransitionDuration],
  );

  return {
    settings,
    earthMode,
    setEarthMode,
    latLonMode,
    setLatLonMode,
    satelliteMode,
    setSatelliteMode,
    earthRotationSpeed,
    setEarthRotationSpeed,
    earthTransitionDuration,
    setEarthTransitionDuration,
  };
}
