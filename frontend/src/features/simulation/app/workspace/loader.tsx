"use client";
import { useEffect,useState } from "react";
import { useSearchParams } from "next/navigation";
import { get_record } from "../../communication/records";
import { get_project } from "../../communication/projects";
import RecordPlayback from "../../components/RecordPlayback";
import type { Project,RecordWindow } from "../../contracts/generated";
import Workspace from "./Workspace";
import { RealtimeFramesProvider } from "./useFramesContext";

export default function WorkspaceLoader({ project_id }: { project_id: string }) {
  const record_id = useSearchParams().get("record_id");
  const request_key = JSON.stringify([project_id, record_id]);
  const [loaded, set_loaded] = useState<{ request_key: string; project: Project; record_window: RecordWindow | null } | null>(null);
  const [error, set_error] = useState<{ request_key: string; message: string } | null>(null);
  useEffect(() => {
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
  }, [project_id, record_id, request_key]);
  if (error?.request_key === request_key) return <p role="alert" className="p-8 text-red-300">{error.message}</p>;
  if (loaded?.request_key !== request_key) return <p className="p-8 text-white">Loading workspace…</p>;
  const { project, record_window } = loaded;
  return <RealtimeFramesProvider key={request_key} initial_algorithm={project.algorithm}>
    <div className="flex h-full flex-col">
      {record_id && record_window && <RecordPlayback record_id={record_id} initial_window={record_window} />}
      <div className="min-h-0 flex-1"><Workspace selected={project} is_replay={!!record_id} /></div>
    </div>
  </RealtimeFramesProvider>;
}
