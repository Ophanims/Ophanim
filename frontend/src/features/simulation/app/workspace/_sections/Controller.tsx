import { PauseIcon,PlayIcon } from "@heroicons/react/24/outline";
import { useEffect,useState } from "react";
import { useFrames } from "../useFramesContext";

export default function Player() {
  const { frames, selected_frame_index, set_selected_frame_index, follow_live, set_follow_live } = useFrames();
  const [is_playing, set_is_playing] = useState(false);
  useEffect(() => {
    if (!is_playing) return;
    const interval = setInterval(() => set_selected_frame_index((previous) => Math.min(previous + 1, frames.length - 1)), 200);
    return () => clearInterval(interval);
  }, [is_playing, frames.length, set_selected_frame_index]);
  const frame = frames[selected_frame_index];
  return <div className="absolute bottom-0 left-0 z-20 flex w-full items-center gap-3 bg-black/80 p-3 text-xs text-white">
    <button aria-label={is_playing ? "Pause playback" : "Play playback"} onClick={() => { set_follow_live(false); set_is_playing(!is_playing); }}>
      {is_playing ? <PauseIcon className="h-5 w-5" /> : <PlayIcon className="h-5 w-5" />}
    </button>
    <input aria-label="Frame" type="range" min={0} max={Math.max(0, frames.length - 1)} value={selected_frame_index}
      onChange={(event) => { set_follow_live(false); set_is_playing(false); set_selected_frame_index(Number(event.target.value)); }} className="flex-1" />
    <span>{frame?.time ?? "No frames"}</span>
    <label><input type="checkbox" checked={follow_live} onChange={(event) => { set_follow_live(event.target.checked); set_is_playing(false); }} /> Live</label>
  </div>;
}
