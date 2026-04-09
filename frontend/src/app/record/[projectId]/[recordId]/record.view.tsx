import Link from "next/link";
import { ArrowPathIcon, ChevronLeftIcon } from "@heroicons/react/24/outline";
import { PauseIcon, PlayIcon } from "@heroicons/react/24/solid";
import FrameWidget from "../../../workspace/[projectId]/FrameWidget";
import {
  EARTH_MODE,
  EARTH_MODE_OPTIONS,
  LATLON_MODE,
  LATLON_MODE_OPTIONS,
  SATELLITE_MODE,
  SATELLITE_MODE_OPTIONS,
  useFrameWidgetSettings,
} from "../../../workspace/[projectId]/useFrameWidgetSettings";
import type { SatellitePoint } from "./record.model";

type RecordViewProps = {
  projectId: string;
  recordId: string;
  loading: boolean;
  error: string | null;
  frameSlots: number[];
  frameIndex: number;
  satellites: SatellitePoint[];
  playing: boolean;
  onTogglePlay: () => void;
  onRefresh: () => void;
};

export default function RecordView({
  projectId,
  recordId,
  loading,
  error,
  frameSlots,
  frameIndex,
  satellites,
  playing,
  onTogglePlay,
  onRefresh,
}: RecordViewProps) {
  const { settings, earthMode, setEarthMode, latLonMode, setLatLonMode, satelliteMode, setSatelliteMode } = useFrameWidgetSettings({
    earthMode: EARTH_MODE.REALISTIC,
    latLonMode: LATLON_MODE.HIDDEN,
    satelliteMode: SATELLITE_MODE.SHOW,
  });
  const totalFrameCount = Math.max(frameSlots.length, 1);
  const currentFrame = frameIndex < 0 ? 0 : Math.min(frameIndex + 1, totalFrameCount);
  const progressPercent = Math.min(100, Math.max(0, (currentFrame / totalFrameCount) * 100));
  const status = loading ? "loading" : playing ? "playing" : "paused";

  return (
    <main className="w-full h-screen text-white relative font-sans overflow-hidden">
      <div className="absolute inset-0 flex flex-col py-12 px-20 z-20">
        <div className="relative h-full w-full flex flex-col">
          <div className="w-full flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Link href={`/workspace/${projectId}`} className="px-3 py-2">
                <ChevronLeftIcon className="h-6 w-6" />
              </Link>
              <h1 className="text-2xl font-semibold">Record / Project {projectId} / Record {recordId}</h1>
            </div>
          </div>

          <div className="absolute bottom-0 w-full mb-4">
            <div className="flex items-center justify-between text-sm opacity-80">
              <p>Status: {status}</p>
              <div className="flex items-center gap-3 text-xs">
                <label className="flex items-center gap-2">
                  <span>Earth</span>
                  <select
                    className="rounded bg-white/10 px-2 py-1 text-white"
                    value={earthMode}
                    onChange={(e) => setEarthMode(e.target.value as (typeof EARTH_MODE_OPTIONS)[number]["value"])}
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
                    onChange={(e) => setLatLonMode(e.target.value as (typeof LATLON_MODE_OPTIONS)[number]["value"])}
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
                      onChange={(e) => setSatelliteMode(e.target.value as (typeof SATELLITE_MODE_OPTIONS)[number]["value"])}
                    >
                      {SATELLITE_MODE_OPTIONS.map((mode) => (
                        <option key={mode.value} value={mode.value} className="text-black">
                          {mode.label}
                        </option>
                      ))}
                    </select>
                  </label>
              </div>
            </div>

            <div className="flex items-center justify-center gap-4">
              <div className="h-1 w-full overflow-hidden rounded-full bg-white/20">
                <div className="h-full bg-white transition-all" style={{ width: `${progressPercent}%` }} />
              </div>

              <div className="flex gap-2">
                <button onClick={onRefresh} className="p-2 text-sm" title="Refresh Frames">
                  <ArrowPathIcon className="h-5 w-5" />
                </button>
                <button onClick={onTogglePlay} className="p-2 text-sm" title={playing ? "Pause" : "Play"}>
                  {playing ? <PauseIcon className="h-5 w-5" /> : <PlayIcon className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs opacity-70">
              <p>Frame: {frameIndex < 0 ? "-" : frameIndex + 1} / {frameSlots.length}</p>
            </div>

            {loading ? <p className="text-sm opacity-80">Loading record...</p> : null}
            {error ? <p className="text-sm text-red-600">Error: {error}</p> : null}
          </div>
        </div>
      </div>

      <div className="absolute bottom-0 w-full h-full pointer-events-none z-0">
        <FrameWidget satellites={satellites} settings={settings} />
      </div>
    </main>
  );
}
