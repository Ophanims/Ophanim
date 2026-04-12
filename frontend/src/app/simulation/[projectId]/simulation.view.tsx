import Link from "next/link";
import { ChevronLeftIcon } from "@heroicons/react/24/outline";
import { useProgress } from "@react-three/drei";
import type { EarthPoint, LinkPoint, SatellitePoint, StationPoint, SunPoint } from "./simulation.model";
import FrameWidget from "@/app/workspace/[projectId]/FrameWidget";
import PlaybackControlWidget from "@/app/shared/PlaybackControlWidget";
import {
  EARTH_MODE,
  FOOTPRINT_MODE,
  LINK_MODE,
  LATLON_MODE,
  SATELLITE_MODE,
  STATION_MODE,
  useFrameWidgetSettings,
} from "@/app/workspace/[projectId]/useFrameWidgetSettings";
import EntitySettingsWidget from "@/app/shared/EntitySettingsWidget";

type SimulationViewProps = {
  projectId: string;
  status: string;
  tickCount: number;
  maxSlot: number | null;
  error: string | null;
  sun: SunPoint | null;
  earth: EarthPoint | null;
  satellites: SatellitePoint[];
  stations: StationPoint[];
  links: LinkPoint[];
  onPlay: () => void;
  onPause: () => void;
  onStop: () => void;
};

export default function SimulationView({
  projectId,
  status,
  tickCount,
  maxSlot,
  error,
  sun,
  earth,
  satellites,
  stations,
  links,
  onPlay,
  onPause,
  onStop,
}: SimulationViewProps) {
  const {
    settings,
    earthMode,
    setEarthMode,
    latLonMode,
    setLatLonMode,
    satelliteMode,
    setSatelliteMode,
    stationMode,
    setStationMode,
    footprintMode,
    setFootprintMode,
    linkMode,
    setLinkMode,
  } = useFrameWidgetSettings({
    earthMode: EARTH_MODE.REALISTIC,
    latLonMode: LATLON_MODE.HIDDEN,
    satelliteMode: SATELLITE_MODE.SHOW,
    stationMode: STATION_MODE.SHOW,
    footprintMode: FOOTPRINT_MODE.SHOW,
    linkMode: LINK_MODE.ALL,
  });
  const totalSlot = maxSlot && maxSlot > 0 ? maxSlot : Math.max(tickCount, 1);
  const boundedTick = Math.min(Math.max(tickCount, 0), totalSlot);
  const progressPercent = Math.min(
    100,
    Math.max(0, (boundedTick / totalSlot) * 100),
  );
  const { active: assetsLoading, progress } = useProgress();
  const waitingForSimulation = !error && status === "idle";
  const showLoadingOverlay = assetsLoading || waitingForSimulation;
  const loadingText = assetsLoading
    ? `Loading Visualization textures...%`
    : "Waiting for simulation response...";

  return (
    <main className="w-full h-screen bg-black text-white relative font-sans overflow-hidden">
      <div className="absolute inset-0 flex flex-col pt-20 px-12 z-20 pointer-events-none">
        <div className="relative h-full w-full flex flex-col">
          <div className="w-full flex items-center justify-between mb-6 pointer-events-auto">
            <div className="flex items-center gap-3">
              <Link href={`/workspace/${projectId}`} className="px-3 py-2">
                <ChevronLeftIcon className="h-6 w-6" />
              </Link>
              <h1 className="text-2xl font-semibold">
                Simulation / Project {projectId}
              </h1>
            </div>
          </div>
          <PlaybackControlWidget
            status={status}
            playing={status === "running"}
            progressPercent={progressPercent}
            progressLabel={`Slot: ${boundedTick} / ${totalSlot}`}
            onPlay={onPlay}
            onPause={onPause}
            onStop={onStop}
            error={error}
            barTrackClassName="bg-gray-200"
            barFillClassName="bg-black"
            rightHeader={
              <EntitySettingsWidget
                earthMode={earthMode}
                latLonMode={latLonMode}
                satelliteMode={satelliteMode}
                stationMode={stationMode}
                footprintMode={footprintMode}
                linkMode={linkMode}
                onEarthModeChange={setEarthMode}
                onLatLonModeChange={setLatLonMode}
                onSatelliteModeChange={setSatelliteMode}
                onStationModeChange={setStationMode}
                onFootprintModeChange={setFootprintMode}
                onLinkModeChange={setLinkMode}
              />
            }
          />
        </div>
      </div>
      <div className="absolute bottom-0 w-full h-full pointer-events-none z-0">
        <FrameWidget
          sun={sun}
          earth={earth}
          satellites={satellites}
          stations={stations}
          links={links}
          slotCount={boundedTick}
          settings={settings}
        />
      </div>
      {showLoadingOverlay ? (
        <div className="pointer-events-none absolute inset-0 z-30 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3 rounded-xl bg-black/45 px-6 py-4 backdrop-blur-sm">
            <div className="relative h-10 w-10">
              <div className="absolute inset-0 rounded-full border-2 border-white/25" />
              <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-white animate-spin" />
            </div>
            <p className="text-sm text-white/90 tracking-wide">{loadingText}</p>
          </div>
        </div>
      ) : null}
    </main>
  );
}
