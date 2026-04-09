"use client";

import {
  EARTH_MODE_OPTIONS,
  LATLON_MODE_OPTIONS,
  SATELLITE_MODE_OPTIONS,
  STATION_MODE_OPTIONS,
  type EarthMode,
  type LatLonMode,
  type SatelliteMode,
  type StationMode,
} from "@/app/workspace/[projectId]/useFrameWidgetSettings";

type EntitySettingsWidgetProps = {
  earthMode: EarthMode;
  latLonMode: LatLonMode;
  satelliteMode: SatelliteMode;
  stationMode: StationMode;
  onEarthModeChange: (mode: EarthMode) => void;
  onLatLonModeChange: (mode: LatLonMode) => void;
  onSatelliteModeChange: (mode: SatelliteMode) => void;
  onStationModeChange: (mode: StationMode) => void;
};

export default function EntitySettingsWidget({
  earthMode,
  latLonMode,
  satelliteMode,
  stationMode,
  onEarthModeChange,
  onLatLonModeChange,
  onSatelliteModeChange,
  onStationModeChange,
}: EntitySettingsWidgetProps) {
  return (
    <div className="flex items-center gap-3 text-xs">
      <label className="flex items-center gap-2">
        <span>Earth</span>
        <select
          className="rounded bg-white/10 px-2 py-1 text-white"
          value={earthMode}
          onChange={(e) => onEarthModeChange(e.target.value as EarthMode)}
        >
          {EARTH_MODE_OPTIONS.map((mode) => (
            <option key={mode.value} value={mode.value} className="text-black">
              {mode.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex items-center gap-2">
        <span>Lat/Lon</span>
        <select
          className="rounded bg-white/10 px-2 py-1 text-white"
          value={latLonMode}
          onChange={(e) => onLatLonModeChange(e.target.value as LatLonMode)}
        >
          {LATLON_MODE_OPTIONS.map((mode) => (
            <option key={mode.value} value={mode.value} className="text-black">
              {mode.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex items-center gap-2">
        <span>Satellites</span>
        <select
          className="rounded bg-white/10 px-2 py-1 text-white"
          value={satelliteMode}
          onChange={(e) => onSatelliteModeChange(e.target.value as SatelliteMode)}
        >
          {SATELLITE_MODE_OPTIONS.map((mode) => (
            <option key={mode.value} value={mode.value} className="text-black">
              {mode.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex items-center gap-2">
        <span>Stations</span>
        <select
          className="rounded bg-white/10 px-2 py-1 text-white"
          value={stationMode}
          onChange={(e) => onStationModeChange(e.target.value as StationMode)}
        >
          {STATION_MODE_OPTIONS.map((mode) => (
            <option key={mode.value} value={mode.value} className="text-black">
              {mode.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
