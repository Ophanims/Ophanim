"use client";
import { useState } from "react";
import { PlusIcon } from "@heroicons/react/24/outline";
import type { Project } from "../../contracts/generated";
import ProjectEditorDialog from "../_project_config/ProjectEditorDialog";
import ProjectList from "./ProjectList";
import { useProjects } from "./useProjects";

/** Project management panel inside the application's single home page. */
export default function Dashboard({ project_list }: { project_list: Project[] }) {
  const { error, selected_project, set_selected_project, search_content, set_search_content,
    filtered_projects, update_project, delete_project } = useProjects(project_list);
  const [is_editor_open, set_is_editor_open] = useState(false);
  const open_editor = (project: Project | null) => {
    set_selected_project(project);
    set_is_editor_open(true);
  };

  return <>
    <div inert={is_editor_open}>
      <section aria-labelledby="start-heading">
        <h2 id="start-heading" className="mb-4 text-lg font-semibold">Start</h2>
        <div className="flex flex-col items-start gap-3 text-sm">
          <button type="button" onClick={() => open_editor(null)}
            className="inline-flex items-center gap-2 text-white/85 transition-colors hover:text-white focus-visible:outline-1 focus-visible:outline-offset-4">
            <PlusIcon className="h-5 w-5" /><span>Create Project</span>
          </button>
        </div>
      </section>
      {error && <p role="alert" className="mt-5 text-sm text-red-200">{error}</p>}
      <ProjectList projects={filtered_projects} search_content={search_content} set_search_content={set_search_content}
        on_edit={open_editor} delete_project={delete_project} />
    </div>
    {is_editor_open && <ProjectEditorDialog project={selected_project} on_close={() => set_is_editor_open(false)}
      on_save={(project) => { update_project(project); set_is_editor_open(false); }} />}
  </>;
}
