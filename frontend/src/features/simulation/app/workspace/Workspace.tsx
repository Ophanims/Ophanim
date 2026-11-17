"use client";
import { clear_cache,initial_cache,start_job } from "../../communication/cache";
import { save_project } from "../../communication/projects";
import JobPanel from "../../components/JobPanel";
import type { JobSnapshot } from "../../contracts/generated";
import { export_project,select_project_file } from "../../lib/project_files";


import MenuBar from "@/features/simulation/app/workspace/_sections/MenuBar";
import WindowTabs from "@/features/simulation/app/workspace/_sections/WindowTabs";
import { Project } from "@/features/simulation/types";
import { useRouter } from "next/navigation";
import { Suspense,useEffect,useState } from "react";
import { useWindowTabsStore } from "../../store/windowsStore";
import DataFlowPanel from "../_flow_panel/DataFlowPanel";
import GeometryView from "../_geometry_view/GeometryView";
import MapViewPage from "../_map_view/MapView";
import ObjectView from "../_object_view/ObjectView";
import ParameterPanel from "../_parameter_panel/ParameterPanel";
import ProjectEditorDialog from "../_project_config/ProjectEditorDialog";
import UniverseView from "../_universe_view/UniverseView";
import Player from "./_sections/Controller";
import { Inventory } from "./_sections/Inventory";
import { useFrames } from "./useFramesContext";
import { useSelectedProject } from "./useSelectedProject";

interface WorkspaceProps {
  selected: Project | null;
}

export default function Workspace({ selected }: WorkspaceProps) {
  const { selected_project, set_selected_project } = useSelectedProject(selected);
  const add_tab = useWindowTabsStore((s) => s.add_tab);
  useEffect(() => {
    add_tab({ id: "scene", title: "Universe View", content: <UniverseView /> });
    return () => useWindowTabsStore.getState().initialize([]);
  }, [add_tab]);
  const {
    algorithm, set_algorithm, error,
    is_loading,
    is_connected,
    is_running,
    connect,
    stop_simulation,
    run_simulation,
    pause_simulation,
  } = useFrames();

  const [is_parameters_open, set_is_parameters_open] = useState(false);
  const [show_sidebar, set_show_sidebar] = useState(true);
  const [show_terminal, set_show_terminal] = useState(false);
  const [show_player, set_show_player] = useState(false);
  const [is_cache_loading, set_is_cache_loading] = useState(false);

  const router = useRouter();
  const [job, set_job] = useState<JobSnapshot | null>(null);
  const [operation_error, set_operation_error] = useState("");

  const handle_menu_click = async (parent: string, child: string) => {
    if (!selected_project) return;

    if (parent === "Visualization") {
      if (child === "Universe View") {
        add_tab({
          id: "scene",
          title: "Universe View",
          content: <UniverseView />,
        });
      }
      if (child === "Geometry View") {
        add_tab({
          id: "geometryView",
          title: "Geometry View",
          content: <GeometryView />,
        });
      }
      if (child === "Object View") {
        add_tab({
          id: "objectView",
          title: "Object View",
          content: <ObjectView />,
        });
      }
      if (child === "Map View") {
        add_tab({
          id: "mapView",
          title: "Map View",
          content: <MapViewPage />,
        });
      }
      if (child === "Satellite Panel") {
        add_tab({
          id: "satPanel",
          title: "Satellite Panel",
          content: <ParameterPanel />,
        });
      }
      if (child === "Data Flow Panel") {
        add_tab({
          id: "dataFlowPanel",
          title: "Data Flow Panel",
          content: <DataFlowPanel />,
        });
      }
    }
    if (parent === "Simulation") {
      if (child === "Launch Simulation" && !is_connected && !is_loading) {
        connect(selected_project);
        set_show_player(true);
      }
      if (child === "Shutdown") stop_simulation();
      if (child === "Initialization") {
        set_is_cache_loading(true);
        initial_cache(selected_project).then(() => {
          set_is_cache_loading(false);
        }).catch((error: Error) => { set_operation_error(error.message); set_is_cache_loading(false); });
      }
      if (child === "Train Model") {
        set_is_cache_loading(true);
        start_job(selected_project, "train").then((job) => {
          set_job(job);
          set_is_cache_loading(false);
        }).catch((error: Error) => { set_operation_error(error.message); set_is_cache_loading(false); });
      }
      if (child === "Auto Testing") {
        set_is_cache_loading(true);
        start_job(selected_project, "auto_test").then((job) => {
          set_job(job);
          set_is_cache_loading(false);
        }).catch((error: Error) => { set_operation_error(error.message); set_is_cache_loading(false); });
      }
      if (child === "Clear Datasets") void clear_cache().catch((error: Error) => set_operation_error(error.message));
    }
    if (parent === "Project") {
      if (child === "Config") {
        if (!is_connected && !is_loading) set_is_parameters_open(true);
        else set_operation_error("Stop the simulation before editing project parameters.");
      }
      if (child === "Import") {
        try {
          const imported_project = await select_project_file();
          if (imported_project) {
            const project = await save_project(imported_project);
            router.push(`/workspace/${encodeURIComponent(project.project_id)}`);
            set_selected_project(project);
          }
        } catch (error) { set_operation_error(error instanceof Error ? error.message : "Import failed"); }
      }
      if (child === "Export") {
        export_project(selected_project);
      }
      if (child === "Save") {
        try { set_selected_project(await save_project(selected_project)); }
        catch (error) { set_operation_error(error instanceof Error ? error.message : "Save failed"); }
      }
      if (child === "Exit") {
        router.back();
      }
    }
    if (parent === "View") {
      // if (child === "Terminal") {
      //   setShowTerminal((v) => !v);
      // }
      if (child === "Inventory") {
        set_show_sidebar((v) => !v);
      }
      if (child === "Controller") {
        set_show_player((v) => !v);
      }
    }
  };

  // 监听 Ctrl+B 快捷键
  useEffect(() => {
    const handle_key_down = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
        set_show_sidebar((v) => !v);
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "t") {
        set_show_terminal((v) => !v);
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "p") {
        set_show_player((v) => !v);
      }
    };
    window.addEventListener("keydown", handle_key_down);
    return () => window.removeEventListener("keydown", handle_key_down);
  }, []);

  if (!selected_project) {
    return <div className="text-gray-400 p-4">No project selected</div>;
  }

  return (
    <div className="h-full w-full text-gray-300 font-sans flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-gray-08 backdrop-blur-sm border-b border-white/10 px-4 py-3 flex justify-between items-center z-10">
        <h1 className="text-xl font-semibold text-white">
          {selected_project.title}
        </h1>
        <span className="text-xs text-white/40">Latest 600 frames buffered</span>
      </div>

      {(error || operation_error) && <p role="alert" className="px-4 py-2 text-sm text-red-300">{error || operation_error}</p>}
      {job && <JobPanel job={job} on_change={set_job} />}
      {/* Menu Bar */}
      <MenuBar
        on_open_parameters={() => set_is_parameters_open(true)}
        algorithm={algorithm}
        on_algorithm_change={(algorithm) => { set_algorithm(algorithm); set_selected_project({ ...selected_project, algorithm }); }}
        disabled={is_running}
        is_connected={is_connected}
        is_running={is_running}
        is_loading={is_cache_loading || is_loading}
        project={selected_project}
        on_menu_click={handle_menu_click}
        on_run_simulation={run_simulation}
        on_pause_simulation={pause_simulation}
        on_stop_simulation={stop_simulation}
      />

      {/* Main */}
      <div className="flex min-h-0 w-full flex-1 overflow-hidden">
        {/* Sidebar */}
        {show_sidebar && (
          <aside className="w-1/5 bg-gray-08 backdrop-blur-sm border-r border-white/10 flex flex-col">
            <Inventory project={selected_project} />
          </aside>
        )}

        {/* Main Tabs + Canvas */}
        <main
          className={
            show_sidebar
              ? "flex w-4/5 h-full relative"
              : "flex w-full h-full relative"
          }
        >
          <Suspense fallback={<p className="p-6">Loading view…</p>}><WindowTabs /></Suspense>
          {show_terminal && (
            <div className="absolute bottom-0 left-0 w-full h-1/5 bg-gray-09 border-t border-white/10 z-50">
              <div className="bg-black">terminal</div>
            </div>
          )}
          {show_player && <Player />}
        </main>
      </div>
      {is_parameters_open && <ProjectEditorDialog project={selected_project}
        on_close={() => set_is_parameters_open(false)}
        on_save={(project) => {
          set_selected_project(project);
          set_algorithm(project.algorithm ?? algorithm);
          set_is_parameters_open(false);
        }} />}
    </div>
  );
}
