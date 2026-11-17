"use client";
import { useEffect,useState } from "react";
import { list_projects } from "../../communication/projects";
import type { Project } from "../../contracts/generated";
import Dashboard from "./Dashboard";

export default function DashboardLoader() {
  const [projects, set_projects] = useState<Project[] | null>(null);
  const [error, set_error] = useState("");
  const [attempt, set_attempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    list_projects(controller.signal).then(set_projects).catch((error: Error) => {
      if (!controller.signal.aborted) set_error(error.message);
    });
    return () => controller.abort();
  }, [attempt]);
  if (error) return <div className="text-sm">
    <p role="alert" className="mb-4 text-red-200">{error}</p>
    <button type="button" className="rounded border border-white/30 px-4 py-2" onClick={() => {
      set_error(""); set_attempt((previous) => previous + 1);
    }}>Retry projects</button>
  </div>;
  if (!projects) return <p role="status" className="text-sm text-white/60">Loading projects…</p>;
  return <Dashboard project_list={projects} />;
}
