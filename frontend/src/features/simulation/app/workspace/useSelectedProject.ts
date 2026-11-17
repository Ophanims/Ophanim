// features/workspace/hooks/useProjects.ts
import { Project } from "@/features/simulation/types";
import { useState } from "react";

export function useSelectedProject
  (selected: Project | null) {
  const [selected_project, set_selected_project] = useState<Project | null>(selected);
  const [search_content, set_search_content] = useState("");

  const update_project = (updated: Project) => {
    set_selected_project(updated);
  };

  return {
    selected_project,
    set_selected_project,
    search_content,
    set_search_content,
    update_project,
  };
}
