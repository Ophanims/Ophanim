import { PauseIcon,PlayIcon } from "@heroicons/react/24/outline";
import { useEffect,useState } from "react";
import { useFrames } from "../useFramesContext";

export default function Player({ is_replay = false }: { is_replay?: boolean }) {
  const { frames, selected_frame_index, set_selected_frame_index, follow_live, set_follow_live } = useFrames();
  const [is_playing, set_is_playing] = useState(false);
  const is_at_end = selected_frame_index >= frames.length - 1;
  const is_advancing = is_playing && !is_at_end;
  useEffect(() => {
    if (!is_advancing) return;
    const interval = setInterval(() => set_selected_frame_index((previous) => Math.min(previous + 1, frames.length - 1)), 200);
    return () => clearInterval(interval);
  }, [is_advancing, frames.length, set_selected_frame_index]);
  const frame = frames[selected_frame_index];
  return <div className="absolute bottom-0 left-0 z-20 flex w-full items-center gap-3 bg-black/80 p-3 text-xs text-white">
    <button disabled={frames.length < 2} aria-label={is_advancing ? "Pause playback" : "Play playback"} onClick={() => {
      set_follow_live(false);
      if (is_at_end) set_selected_frame_index(0);
      set_is_playing(!is_advancing);
    }}>
      {is_advancing ? <PauseIcon className="h-5 w-5" /> : <PlayIcon className="h-5 w-5" />}
    </button>
    <input aria-label="Frame" type="range" min={0} max={Math.max(0, frames.length - 1)} value={selected_frame_index}
      onChange={(event) => { set_follow_live(false); set_is_playing(false); set_selected_frame_index(Number(event.target.value)); }} className="flex-1" />
    <span>{frame?.time ?? "No frames"}</span>
    {!is_replay && <label><input type="checkbox" checked={follow_live} onChange={(event) => { set_follow_live(event.target.checked); set_is_playing(false); }} /> Live</label>}
  </div>;
}
