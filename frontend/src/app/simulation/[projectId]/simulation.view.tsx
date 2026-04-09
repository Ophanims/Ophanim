import Link from "next/link";
import { ArrowLeftIcon, ChevronLeftIcon } from "@heroicons/react/24/outline";
import type { SatellitePoint } from "./simulation.model";
import FrameWidget from "@/app/workspace/[projectId]/FrameWidget";
import { PauseIcon, PlayIcon, StopIcon } from "@heroicons/react/24/solid";

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
  const totalSlot = maxSlot && maxSlot > 0 ? maxSlot : Math.max(tickCount, 1);
  const boundedTick = Math.min(Math.max(tickCount, 0), totalSlot);
  const progressPercent = Math.min(
    100,
    Math.max(0, (boundedTick / totalSlot) * 100),
  );

  return (
    <main className="w-full h-screen text-white relative font-sans overflow-hidden">
      <div className="absolute inset-0 flex flex-col py-12 px-20 z-20">
        <div className="relative h-full w-full flex flex-col">
          <div className="w-full flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Link href={`/workspace/${projectId}`} className="px-3 py-2">
                <ChevronLeftIcon className="h-6 w-6" />
              </Link>
              <h1 className="text-2xl font-semibold">
                Simulation / Project {projectId}
              </h1>
            </div>
          </div>

          <div className="absolute bottom-0 w-full mb-4">
            <div className="flex items-center justify-between text-sm opacity-80">
              <p>Status: {status}</p>
            </div>
            <div className="flex items-center justify-center gap-4">
              <div className="h-1 w-full overflow-hidden rounded-full bg-gray-200">
                <div
                  className="h-full bg-black transition-all"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <div className="flex gap-2">
                {status !== "running" ? (
                  <button onClick={onPlay} className="p-2 text-sm">
                    <PlayIcon className="h-5 w-5" />
                  </button>
                ) : (
                  <button onClick={onPause} className="p-2 text-sm">
                    <PauseIcon className="h-5 w-5" />
                  </button>
                )}
                <button onClick={onStop} className="p-2 text-sm">
                  <StopIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs opacity-70">
              <p>
                Slot: {boundedTick} / {totalSlot}{" "}
              </p>
            </div>
            {error ? (
              <p className="text-sm text-red-600">Error: {error}</p>
            ) : null}
          </div>
        </div>
      </div>
      <div className="absolute bottom-0 w-full h-full pointer-events-none z-0">
        <FrameWidget satellites={satellites} />
      </div>
    </main>
  );
}
