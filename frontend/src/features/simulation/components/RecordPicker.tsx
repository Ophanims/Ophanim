import { useEffect, useId, useRef, useState } from "react";
import { list_records } from "../communication/records";
import type { RecordSnapshot } from "../contracts/generated";

export default function RecordPicker({ project_id, on_close, on_select }: {
  project_id: string; on_close: () => void; on_select: (record: RecordSnapshot) => void;
}) {
  const dialog_ref = useRef<HTMLDialogElement>(null);
  const title_id = useId();
  const [request_index, set_request_index] = useState(0);
  const [result, set_result] = useState<{ records: RecordSnapshot[]; is_loading: boolean; error: string }>({
    records: [], is_loading: true, error: "",
  });

  useEffect(() => {
    const previous_focus = document.activeElement;
    const dialog = dialog_ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
      if (previous_focus instanceof HTMLElement && previous_focus.isConnected) previous_focus.focus();
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    list_records(controller.signal, project_id).then((records) => {
      if (!controller.signal.aborted) set_result({ records, is_loading: false, error: "" });
    }).catch((error: Error) => {
      if (!controller.signal.aborted) set_result({ records: [], is_loading: false, error: error.message });
    });
    return () => controller.abort();
  }, [project_id, request_index]);

  return <dialog ref={dialog_ref} aria-labelledby={title_id}
    onCancel={(event) => { event.preventDefault(); on_close(); }}
    className="m-auto max-h-[85dvh] w-[min(56rem,calc(100%-2rem))] rounded-xl border border-white/25 bg-neutral-950 p-0 text-white shadow-2xl backdrop:bg-black/60 backdrop:backdrop-blur-sm">
    <header className="flex items-center justify-between gap-4 border-b border-white/15 px-5 py-4">
      <div><h2 id={title_id} className="text-base font-semibold">Record</h2>
        <p className="mt-1 text-xs text-white/50">Select a recording to replay in this workspace.</p></div>
      <button type="button" onClick={on_close} className="rounded border border-white/25 px-3 py-1.5 text-sm hover:bg-white/10">Close</button>
    </header>
    <div className="max-h-[60dvh] overflow-auto p-5 text-sm" aria-busy={result.is_loading}>
      {result.is_loading && <p role="status" className="text-white/60">Loading records…</p>}
      {result.error && <p role="alert" className="text-red-300">{result.error}</p>}
      {!result.is_loading && !result.error && !result.records.length &&
        <p className="text-white/60">No records for this project yet. Run a simulation to create one.</p>}
      {!!result.records.length && <table className="w-full text-left text-xs">
        <thead className="text-white/50"><tr><th className="pb-3 font-normal">Simulation start</th>
          <th className="pb-3 font-normal">Algorithm</th><th className="pb-3 font-normal">Status</th>
          <th className="pb-3 font-normal">Frames</th><th className="pb-3 font-normal"><span className="sr-only">Actions</span></th></tr></thead>
        <tbody>{result.records.map((record) => <tr key={record.record_id} className="border-t border-white/10">
          <td className="py-3 pr-4"><time dateTime={record.project.experiment.start_time}>{new Date(record.project.experiment.start_time).toLocaleString()}</time>
            <div className="mt-1 font-mono text-[10px] text-white/40">{record.record_id}</div></td>
          <td className="pr-4">{record.algorithm}</td><td className="pr-4">{record.status}</td><td className="pr-4">{record.frame_count}</td>
          <td><button type="button" disabled={record.frame_count === 0} onClick={() => on_select(record)}
            className="rounded border border-white/25 px-3 py-1.5 hover:bg-white/10 disabled:opacity-30">Replay</button></td>
        </tr>)}</tbody>
      </table>}
    </div>
    <footer className="flex items-center justify-between gap-4 border-t border-white/15 px-5 py-3 text-xs text-white/50">
      <span>Latest 200 records for this project</span>
      <button type="button" disabled={result.is_loading} className="rounded px-3 py-1.5 text-white/80 hover:bg-white/10 disabled:opacity-30"
        onClick={() => { set_result({ records: [], is_loading: true, error: "" }); set_request_index((previous) => previous + 1); }}>Refresh</button>
    </footer>
  </dialog>;
}
