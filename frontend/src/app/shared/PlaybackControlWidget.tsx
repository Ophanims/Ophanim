"use client";

import { ArrowPathIcon } from "@heroicons/react/24/outline";
import { PauseIcon, PlayIcon, StopIcon } from "@heroicons/react/24/solid";
import type { ReactNode } from "react";

type PlaybackControlWidgetProps = {
  status: string;
  playing: boolean;
  progressPercent: number;
  progressLabel: string;
  onPlay: () => void;
  onPause: () => void;
  onStop?: () => void;
  onRefresh?: () => void;
  error?: string | null;
  barTrackClassName?: string;
  barFillClassName?: string;
  rightHeader?: ReactNode;
};

export default function PlaybackControlWidget({
  status,
  playing,
  progressPercent,
  progressLabel,
  onPlay,
  onPause,
  onStop,
  onRefresh,
  error,
  barTrackClassName = "bg-white/20",
  barFillClassName = "bg-white",
  rightHeader,
}: PlaybackControlWidgetProps) {
  return (
    <div className="absolute bottom-0 w-full mb-4 pointer-events-auto">
      <div className="flex items-center justify-center gap-4">
        <div
          className={`h-1 w-full overflow-hidden rounded-full bg-white/20 ${barTrackClassName}`}
        >
          <div
            className={`h-full transition-all bg-white ${barFillClassName}`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      <div className="flex mt-2 items-center justify-between text-xs opacity-70">
        <div className="flex gap-2">
          {onRefresh ? (
            <button
              onClick={onRefresh}
              className="flex rounded-full bg-black/50 p-2 text-sm transition hover:bg-white/20"
              title="Refresh"
            >
              <ArrowPathIcon className="h-5 w-5" />
            </button>
          ) : null}

          {!playing ? (
            <button
              onClick={onPlay}
              className="flex rounded-full bg-black/50 p-2 text-sm transition hover:bg-white/20"
              title="Play"
            >
              <PlayIcon className="h-5 w-5" />
            </button>
          ) : (
            <button
              onClick={onPause}
              className="flex rounded-full bg-black/50 p-2 text-sm transition hover:bg-white/20"
              title="Pause"
            >
              <PauseIcon className="h-5 w-5" />
            </button>
          )}

          {onStop ? (
            <button
              onClick={onStop}
              className="flex rounded-full bg-black/50 p-2 text-sm transition hover:bg-white/20"
              title="Stop"
            >
              <StopIcon className="h-5 w-5" />
            </button>
          ) : null}
          <div className="flex rounded-full bg-black/50 py-2 px-3 text-white gap-2">
            <p>{progressLabel}</p>
          </div>
          <div className="flex rounded-full bg-black/50 py-2 px-3 text-white gap-2">
            <p>Status: {status}</p>
            {/* {rightHeader ? rightHeader : null} */}
          </div>
        </div>
        {rightHeader ? rightHeader : null}
      </div>

      {error ? <p className="text-sm text-red-600">Error: {error}</p> : null}
    </div>
  );
}
