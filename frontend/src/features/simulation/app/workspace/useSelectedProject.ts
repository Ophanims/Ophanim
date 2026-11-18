// features/workspace/hooks/useProjects.ts
import { Project } from "@/features/simulation/types";
import { useCallback,useState,type SetStateAction } from "react";

export function useSelectedProject
  (selected: Project | null) {
  const [selection, set_selection] = useState({ source: selected, selected_project: selected });
  if (selection.source !== selected) set_selection({ source: selected, selected_project: selected });
  const selected_project = selection.source === selected ? selection.selected_project : selected;
  const set_selected_project = useCallback((update: SetStateAction<Project | null>) => {
    set_selection((previous) => ({ ...previous,
      selected_project: typeof update === "function" ? update(previous.selected_project) : update }));
  }, []);
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
