import { useEffect,useState } from "react";
import { useFrames } from "../app/workspace/useFramesContext";
import { get_record } from "../communication/records";
import type { RecordWindow } from "../contracts/generated";

export default function RecordPlayback({ record_id }: { record_id: string }) {
  const { load_record_frames } = useFrames();
  const [start_frame, set_start_frame] = useState(0);
  const [record_window, set_record_window] = useState<RecordWindow | null>(null);
  const [error, set_error] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    get_record(record_id, start_frame, controller.signal).then((window) => {
      load_record_frames(window.frames); set_record_window(window);
    }).catch((error: Error) => { if (!controller.signal.aborted) set_error(error.message); });
    return () => controller.abort();
  }, [record_id, start_frame, load_record_frames]);
  return <div className="flex gap-4 px-4 py-2 text-xs text-white">
    <span>Replay: {record_id} · window {start_frame + 1}–{start_frame + (record_window?.frames.length ?? 0)}</span>
    <button disabled={start_frame === 0} onClick={() => set_start_frame(Math.max(0, start_frame - 600))}>Previous 600</button>
    <button disabled={!record_window?.has_more} onClick={() => set_start_frame(start_frame + 600)}>Next 600</button>
    {error && <span role="alert" className="text-red-300">{error}</span>}
  </div>;
}
