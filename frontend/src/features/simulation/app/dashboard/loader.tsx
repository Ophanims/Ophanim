"use client";
import { useEffect,useState } from "react";
import { list_projects } from "../../communication/projects";
import type { Project } from "../../contracts/generated";
import Dashboard from "./Dashboard";
import styles from "./ProjectReveal.module.css";

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
  if (!projects) return <div role="status" aria-label="Loading projects" aria-busy="true"
    className="flex min-h-32 items-center justify-center">
    <span aria-hidden="true" className="h-6 w-6 animate-spin rounded-full border border-white/20 border-t-white" />
  </div>;
  return <div className={styles.ready} aria-busy="false"><Dashboard project_list={projects} /></div>;
}
