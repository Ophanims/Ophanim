"use client";
import { useEffect,useState } from "react";
import Link from "next/link";
import { useRouter,useSearchParams } from "next/navigation";
import { get_record } from "../../communication/records";
import { get_project } from "../../communication/projects";
import type { Project,RecordWindow } from "../../contracts/generated";
import Workspace from "./Workspace";
import { RealtimeFramesProvider } from "./useFramesContext";

export default function WorkspaceLoader({ project_id }: { project_id: string }) {
  const router = useRouter();
  const record_id = useSearchParams().get("record_id");
  const request_key = JSON.stringify([project_id, record_id]);
  const [request_index, set_request_index] = useState(0);
  const [loaded, set_loaded] = useState<{ request_key: string; project: Project; record_window: RecordWindow | null } | null>(null);
  const [error, set_error] = useState<{ request_key: string; message: string } | null>(null);
  const loaded_key = loaded?.request_key;
  useEffect(() => {
    if (loaded_key === request_key) return;
    const controller = new AbortController();
    const request = record_id
      ? get_record(record_id, 0, controller.signal).then((record_window) => ({ project: record_window.record.project, record_window }))
      : get_project(project_id, controller.signal).then((project) => ({ project, record_window: null }));
    request.then((result) => {
      if (!controller.signal.aborted) { set_loaded({ request_key, ...result }); set_error(null); }
    }).catch((error: Error) => {
      if (!controller.signal.aborted) set_error({ request_key, message: error.message });
    });
    return () => controller.abort();
  }, [project_id, record_id, request_key, request_index, loaded_key]);
  const message = error?.request_key === request_key ? error.message : null;
  const retry = () => { set_error(null); set_request_index((previous) => previous + 1); };
  if (!loaded) return <div className="flex h-full flex-col items-center justify-center gap-4 bg-black p-8 text-white">
    {message ? <><p role="alert" className="text-red-300">{message}</p><button onClick={retry}>Retry</button><Link href="/">Projects</Link></>
      : <p role="status">Loading workspace…</p>}
  </div>;
  const { project, record_window } = loaded;
  const is_loading = loaded.request_key !== request_key && !message;
  const current_url = `/workspace/${encodeURIComponent(project.project_id)}${record_window ? `?record_id=${encodeURIComponent(record_window.record.record_id)}` : ""}`;
  return <div className="relative h-full bg-black" aria-busy={is_loading}>
    <div className="relative z-0 h-full" inert={is_loading || !!message}>
      <RealtimeFramesProvider session_key={loaded.request_key} initial_algorithm={project.algorithm} initial_frames={record_window?.frames}>
        <Workspace selected={project} is_replay={!!record_window} record_window={record_window} is_loading_session={is_loading} />
      </RealtimeFramesProvider>
    </div>
    {(is_loading || message) && <div className="absolute inset-0 z-40 flex items-center justify-center bg-black/45 p-6">
      <div className="max-w-lg rounded-lg border border-white/20 bg-neutral-950 px-6 py-5 text-sm text-white shadow-2xl">
        {message ? <><p role="alert" className="mb-4 text-red-300">{message}</p>
          <button onClick={retry} className="mr-4 rounded border border-white/25 px-3 py-1.5 hover:bg-white/10">Retry</button></>
          : <p role="status" className="mb-4">{record_id ? "Loading recording…" : "Loading live workspace…"}</p>}
        <button onClick={() => router.replace(current_url)} className="rounded border border-white/25 px-3 py-1.5 hover:bg-white/10">
          {message ? "Keep current workspace" : "Cancel"}
        </button>
      </div>
    </div>}
  </div>;
}
