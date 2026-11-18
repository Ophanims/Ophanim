import { useEffect,useState } from "react";
import Link from "next/link";
import { useFrames } from "../app/workspace/useFramesContext";
import { get_record } from "../communication/records";
import type { RecordWindow } from "../contracts/generated";

export default function RecordPlayback({ record_id, initial_window }: { record_id: string; initial_window: RecordWindow }) {
  const { load_record_frames } = useFrames();
  const [start_frame, set_start_frame] = useState(0);
  const [record_window, set_record_window] = useState<RecordWindow | null>(null);
  const [error, set_error] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    const request = start_frame === 0 ? Promise.resolve(initial_window) : get_record(record_id, start_frame, controller.signal);
    request.then((window) => {
      if (controller.signal.aborted) return;
      load_record_frames(window.frames); set_record_window(window); set_error("");
    }).catch((error: Error) => { if (!controller.signal.aborted) set_error(error.message); });
    return () => controller.abort();
  }, [record_id, start_frame, initial_window, load_record_frames]);
  const is_loading = record_window?.start_frame !== start_frame;
  return <div className="flex flex-wrap items-center gap-4 px-4 py-2 text-xs text-white">
    <span>Replay: {record_id} · window {start_frame + 1}–{start_frame + (record_window?.frames.length ?? 0)}</span>
    <button disabled={is_loading || start_frame === 0} onClick={() => set_start_frame(Math.max(0, start_frame - 600))}>Previous 600</button>
    <button disabled={is_loading || !record_window?.has_more} onClick={() => set_start_frame(start_frame + 600)}>Next 600</button>
    {is_loading && !error && <span role="status">Loading frames…</span>}
    <Link href={`/workspace/${encodeURIComponent(initial_window.record.project_id)}`} className="ml-auto rounded border border-white/20 px-3 py-1.5 hover:bg-white/10">Return to live workspace</Link>
    {error && <span role="alert" className="text-red-300">{error}</span>}
  </div>;
}
