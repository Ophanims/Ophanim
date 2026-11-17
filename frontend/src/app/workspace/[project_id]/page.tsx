"use client";
import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
const WorkspaceLoader = dynamic(() => import("@/features/simulation/app/workspace/loader"), {
  ssr: false, loading: () => <p className="p-8">Loading workspace…</p>,
});
export default function WorkspacePage() {
  const { project_id } = useParams<{ project_id: string }>();
  return <WorkspaceLoader key={project_id} project_id={project_id} />;
}
