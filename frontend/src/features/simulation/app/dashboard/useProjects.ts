import { useMemo,useState } from "react";
import { delete_project as request_delete_project } from "../../communication/projects";
import type { Project } from "../../contracts/generated";

export function useProjects(initial_projects: Project[]) {
  const [projects, set_projects] = useState(initial_projects);
  const [selected_project, set_selected_project] = useState<Project | null>(null);
  const [search_content, set_search_content] = useState("");
  const [error, set_error] = useState("");
  const filtered_projects = useMemo(() => projects.filter((project) =>
    `${project.title} ${project.constellation.name}`.toLowerCase().includes(search_content.toLowerCase())), [projects, search_content]);
  const update_project = (project: Project) => {
    set_projects((previous) => previous.some((entry) => entry.project_id === project.project_id)
      ? previous.map((entry) => entry.project_id === project.project_id ? project : entry) : [...previous, project]);
    set_selected_project(project);
  };
  const delete_project = async (project_id: string) => {
    if (!window.confirm("Delete this project?")) return;
    set_error("");
    try {
      await request_delete_project(project_id);
      set_projects((previous) => previous.filter((project) => project.project_id !== project_id));
      set_selected_project((previous) => previous?.project_id === project_id ? null : previous);
    } catch (error) { set_error(error instanceof Error ? error.message : "Delete failed"); }
  };
  return { projects, set_projects, selected_project, set_selected_project, search_content,
    set_search_content, filtered_projects, create_project: update_project, update_project, delete_project, error };
}
