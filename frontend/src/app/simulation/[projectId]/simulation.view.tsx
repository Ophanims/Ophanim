import Link from "next/link";
import { ChevronLeftIcon } from "@heroicons/react/24/outline";
import type { SatellitePoint } from "./simulation.model";
import FrameWidget from "@/app/workspace/[projectId]/FrameWidget";
import PlaybackControlWidget from "@/app/shared/PlaybackControlWidget";
import {
  EARTH_MODE,
  LATLON_MODE,
  SATELLITE_MODE,
  useFrameWidgetSettings,
} from "@/app/workspace/[projectId]/useFrameWidgetSettings";
import EntitySettingsWidget from "@/app/shared/EntitySettingsWidget";

type SimulationViewProps = {
  projectId: string;
  status: string;
  tickCount: number;
  maxSlot: number | null;
  error: string | null;
  satellites: SatellitePoint[];
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
  satellites,
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
  } = useFrameWidgetSettings({
    earthMode: EARTH_MODE.REALISTIC,
    latLonMode: LATLON_MODE.HIDDEN,
    satelliteMode: SATELLITE_MODE.SHOW,
  });
  const totalSlot = maxSlot && maxSlot > 0 ? maxSlot : Math.max(tickCount, 1);
  const boundedTick = Math.min(Math.max(tickCount, 0), totalSlot);
  const progressPercent = Math.min(
    100,
    Math.max(0, (boundedTick / totalSlot) * 100),
  );

  return (
    <main className="w-full h-screen text-white relative font-sans overflow-hidden">
      <div className="absolute inset-0 flex flex-col py-12 px-20 z-20 pointer-events-none">
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
                onEarthModeChange={setEarthMode}
                onLatLonModeChange={setLatLonMode}
                onSatelliteModeChange={setSatelliteMode}
              />
            }
          />
        </div>
      </div>
      <div className="absolute bottom-0 w-full h-full pointer-events-none z-0">
        <FrameWidget satellites={satellites} />
      </div>
    </main>
  );
}
