"use client";

import { useEffect, useRef, useState } from "react";
import {
  EARTH_MODE_OPTIONS,
  LATLON_MODE_OPTIONS,
  FOOTPRINT_MODE_OPTIONS,
  LINK_MODE_OPTIONS,
  SATELLITE_MODE_OPTIONS,
  STATION_MODE_OPTIONS,
  type EarthMode,
  type FootprintMode,
  type LinkMode,
  type LatLonMode,
  type SatelliteMode,
  type StationMode,
} from "@/app/workspace/[projectId]/useFrameWidgetSettings";
import { Cog6ToothIcon } from "@heroicons/react/24/solid";

type EntitySettingsWidgetProps = {
  earthMode: EarthMode;
  latLonMode: LatLonMode;
  satelliteMode: SatelliteMode;
  stationMode: StationMode;
  footprintMode: FootprintMode;
  linkMode: LinkMode;
  onEarthModeChange: (mode: EarthMode) => void;
  onLatLonModeChange: (mode: LatLonMode) => void;
  onSatelliteModeChange: (mode: SatelliteMode) => void;
  onStationModeChange: (mode: StationMode) => void;
  onFootprintModeChange: (mode: FootprintMode) => void;
  onLinkModeChange: (mode: LinkMode) => void;
};

export default function EntitySettingsWidget({
  earthMode,
  latLonMode,
  satelliteMode,
  stationMode,
  footprintMode,
  linkMode,
  onEarthModeChange,
  onLatLonModeChange,
  onSatelliteModeChange,
  onStationModeChange,
  onFootprintModeChange,
  onLinkModeChange,
}: EntitySettingsWidgetProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handlePointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, []);

  return (
    <div ref={rootRef} className="relative inline-flex items-start text-xs">
      <button
        type="button"
        className="flex rounded-full bg-black/50 p-2 text-white gap-2 transition hover:bg-white/20"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-haspopup="dialog"
      >
        <Cog6ToothIcon className="h-5 w-5" />
      </button>

      {open ? (
        <div className="absolute right-0 bottom-full z-40 mt-2 w-[22rem] rounded-xl border border-white/15 bg-black/90 p-4 shadow-2xl backdrop-blur-md">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="flex flex-col gap-1">
              <span className="text-white/70">Earth</span>
              <select
                className="rounded bg-white/10 px-2 py-1.5 text-white"
                value={earthMode}
                onChange={(e) => onEarthModeChange(e.target.value as EarthMode)}
              >
                {EARTH_MODE_OPTIONS.map((mode) => (
                  <option
                    key={mode.value}
                    value={mode.value}
                    className="text-black"
                  >
                    {mode.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1">
              <span className="text-white/70">Lat/Lon</span>
              <select
                className="rounded bg-white/10 px-2 py-1.5 text-white"
                value={latLonMode}
                onChange={(e) =>
                  onLatLonModeChange(e.target.value as LatLonMode)
                }
              >
                {LATLON_MODE_OPTIONS.map((mode) => (
                  <option
                    key={mode.value}
                    value={mode.value}
                    className="text-black"
                  >
                    {mode.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1">
              <span className="text-white/70">Satellites</span>
              <select
                className="rounded bg-white/10 px-2 py-1.5 text-white"
                value={satelliteMode}
                onChange={(e) =>
                  onSatelliteModeChange(e.target.value as SatelliteMode)
                }
              >
                {SATELLITE_MODE_OPTIONS.map((mode) => (
                  <option
                    key={mode.value}
                    value={mode.value}
                    className="text-black"
                  >
                    {mode.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1">
              <span className="text-white/70">Stations</span>
              <select
                className="rounded bg-white/10 px-2 py-1.5 text-white"
                value={stationMode}
                onChange={(e) =>
                  onStationModeChange(e.target.value as StationMode)
                }
              >
                {STATION_MODE_OPTIONS.map((mode) => (
                  <option
                    key={mode.value}
                    value={mode.value}
                    className="text-black"
                  >
                    {mode.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1">
              <span className="text-white/70">Footprint</span>
              <select
                className="rounded bg-white/10 px-2 py-1.5 text-white"
                value={footprintMode}
                onChange={(e) =>
                  onFootprintModeChange(e.target.value as FootprintMode)
                }
              >
                {FOOTPRINT_MODE_OPTIONS.map((mode) => (
                  <option
                    key={mode.value}
                    value={mode.value}
                    className="text-black"
                  >
                    {mode.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1">
              <span className="text-white/70">Links</span>
              <select
                className="rounded bg-white/10 px-2 py-1.5 text-white"
                value={linkMode}
                onChange={(e) => onLinkModeChange(e.target.value as LinkMode)}
              >
                {LINK_MODE_OPTIONS.map((mode) => (
                  <option
                    key={mode.value}
                    value={mode.value}
                    className="text-black"
                  >
                    {mode.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      ) : null}
    </div>
  );
}
