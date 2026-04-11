import Link from "next/link";
import { ChevronLeftIcon } from "@heroicons/react/24/outline";
import FrameWidget from "../../../workspace/[projectId]/FrameWidget";
import PlaybackControlWidget from "@/app/shared/PlaybackControlWidget";
import EntitySettingsWidget from "@/app/shared/EntitySettingsWidget";
import {
  EARTH_MODE,
  FOOTPRINT_MODE,
  LINK_MODE,
  LATLON_MODE,
  SATELLITE_MODE,
  STATION_MODE,
  useFrameWidgetSettings,
} from "../../../workspace/[projectId]/useFrameWidgetSettings";
import type { SatellitePoint } from "./record.model";

type RecordViewProps = {
  projectId: string;
  recordId: string;
  loading: boolean;
  buffering: boolean;
  error: string | null;
  frameSlots: number[];
  frameIndex: number;
  satellites: SatellitePoint[];
  playing: boolean;
  hasMore: boolean;
  onTogglePlay: () => void;
  onRefresh: () => void;
};

export default function RecordView({
  projectId,
  recordId,
  loading,
  buffering,
  error,
  frameSlots,
  frameIndex,
  satellites,
  playing,
  hasMore,
  onTogglePlay,
  onRefresh,
}: RecordViewProps) {
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
  const totalFrameCount = Math.max(frameSlots.length, 1);
  const currentFrame = frameIndex < 0 ? 0 : Math.min(frameIndex + 1, totalFrameCount);
  const progressPercent = Math.min(100, Math.max(0, (currentFrame / totalFrameCount) * 100));
  const status = loading ? "loading" : buffering ? "buffering" : playing ? "playing" : "paused";

  return (
    <main className="w-full h-screen text-white relative font-sans overflow-hidden">
      <div className="absolute inset-0 flex flex-col py-12 px-20 z-20 pointer-events-none">
        <div className="relative h-full w-full flex flex-col">
          <div className="w-full flex items-center justify-between mb-6 pointer-events-auto">
            <div className="flex items-center gap-3">
              <Link href={`/workspace/${projectId}`} className="px-3 py-2">
                <ChevronLeftIcon className="h-6 w-6" />
              </Link>
              <h1 className="text-2xl font-semibold">Record / Project {projectId} / Record {recordId}</h1>
            </div>
          </div>
          <PlaybackControlWidget
            status={status}
            playing={playing}
            progressPercent={progressPercent}
            onPlay={onTogglePlay}
            onPause={onTogglePlay}
            onRefresh={onRefresh}
            error={error}
            progressLabel={`Frame: ${frameIndex < 0 ? "-" : frameIndex + 1} / ${frameSlots.length}${hasMore ? "+" : ""}`}
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

          {loading || buffering ? (
            <p className="absolute bottom-0 mb-1 text-sm opacity-80 pointer-events-none">
              {loading ? "Loading record..." : "Buffering next segment..."}
            </p>
          ) : null}
        </div>
      </div>

      <div className="absolute bottom-0 w-full h-full pointer-events-none z-0">
        <FrameWidget satellites={satellites} slotCount={Math.max(frameIndex, 0)} settings={settings} />
      </div>
    </main>
  );
}
