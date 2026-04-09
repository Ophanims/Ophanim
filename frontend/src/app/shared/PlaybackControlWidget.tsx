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
      <div className="flex items-center justify-between text-sm opacity-80">
        <p>Status: {status}</p>
        {rightHeader ? rightHeader : null}
      </div>

      <div className="flex items-center justify-center gap-4">
        <div className={`h-1 w-full overflow-hidden rounded-full ${barTrackClassName}`}>
          <div className={`h-full transition-all ${barFillClassName}`} style={{ width: `${progressPercent}%` }} />
        </div>

        <div className="flex gap-2">
          {onRefresh ? (
            <button onClick={onRefresh} className="p-2 text-sm" title="Refresh">
              <ArrowPathIcon className="h-5 w-5" />
            </button>
          ) : null}

          {!playing ? (
            <button onClick={onPlay} className="p-2 text-sm" title="Play">
              <PlayIcon className="h-5 w-5" />
            </button>
          ) : (
            <button onClick={onPause} className="p-2 text-sm" title="Pause">
              <PauseIcon className="h-5 w-5" />
            </button>
          )}

          {onStop ? (
            <button onClick={onStop} className="p-2 text-sm" title="Stop">
              <StopIcon className="h-5 w-5" />
            </button>
          ) : null}
        </div>
      </div>

      <div className="flex items-center justify-between text-xs opacity-70">
        <p>{progressLabel}</p>
      </div>

      {error ? <p className="text-sm text-red-600">Error: {error}</p> : null}
    </div>
  );
}
