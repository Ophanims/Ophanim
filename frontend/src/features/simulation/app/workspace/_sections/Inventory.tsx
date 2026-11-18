import { useId, useRef, useState } from "react";
import { CubeIcon, SignalIcon, LinkIcon, ClockIcon, MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import type { Project } from "../../../contracts/generated";
import { useFrames } from "../useFramesContext";
import SatellitePanel from "./SatellitePanel";
import GroundStationPanel from "./GroundStationPanel";
import NetworkPanel from "./NetworkPanel";
import TasksPanel from "./TasksPanel";

const TABS = [
  { id: "satellites", label: "Satellites", icon: CubeIcon },
  { id: "ground_stations", label: "Ground Stations", icon: SignalIcon },
  { id: "network", label: "Network", icon: LinkIcon },
  { id: "tasks", label: "Tasks", icon: ClockIcon },
] as const;
type InventoryTab = typeof TABS[number]["id"];

export const Inventory = ({ project, is_editable, on_project_change }: {
  project: Project; is_editable: boolean; on_project_change: (project: Project) => void;
}) => {
  const { frames, selected_frame_index } = useFrames();
  const [search_content, set_search_content] = useState("");
  const [tab, set_tab] = useState<InventoryTab>("satellites");
  const id = useId();
  const rail_ref = useRef<HTMLDivElement>(null);
  const frame = frames[selected_frame_index];
  const current = TABS.find((item) => item.id === tab)!;
  const select_tab = (tab: InventoryTab) => { set_tab(tab); set_search_content(""); };
  return <div className="flex h-full min-w-0 w-full">
    <div ref={rail_ref} role="tablist" aria-label="Workspace panels" aria-orientation="vertical"
      className="flex h-full w-12 shrink-0 flex-col items-center border-r border-white/10"
      onKeyDown={(event) => {
        const keys = ["ArrowUp", "ArrowDown", "Home", "End"];
        if (!keys.includes(event.key)) return;
        event.preventDefault();
        const index = TABS.findIndex((item) => item.id === tab);
        const next = event.key === "Home" ? 0 : event.key === "End" ? TABS.length - 1
          : (index + (event.key === "ArrowDown" ? 1 : -1) + TABS.length) % TABS.length;
        select_tab(TABS[next].id);
        rail_ref.current?.querySelectorAll<HTMLButtonElement>('button[role="tab"]')[next]?.focus();
      }}>
      {TABS.map(({ id: tab_id, label, icon: Icon }) => <button key={tab_id} type="button" role="tab"
        id={`${id}-${tab_id}`} aria-label={label} title={label} aria-selected={tab === tab_id}
        aria-controls={`${id}-panel`} tabIndex={tab === tab_id ? 0 : -1} onClick={() => select_tab(tab_id)}
        className={`flex h-12 w-full shrink-0 items-center justify-center border-l-2 transition-colors hover:bg-white/5 hover:text-white ${tab === tab_id ? "border-white bg-white/10 text-white" : "border-transparent text-white/50"}`}>
        <Icon className="h-6 w-6" />
      </button>)}
    </div>
    <section id={`${id}-panel`} role="tabpanel" aria-labelledby={`${id}-${tab}`} className="flex min-w-0 flex-1 flex-col">
      <h2 className="px-3 pt-4 pb-3 text-xs font-semibold uppercase tracking-wide text-white">{current.label}</h2>
      <div className="relative mx-3 mb-4">
        <input aria-label={`Search ${current.label}`} value={search_content} onChange={(event) => set_search_content(event.target.value)}
          placeholder="Search…" className="w-full rounded border border-white/15 bg-transparent py-1.5 pr-7 pl-2 text-xs outline-none focus:border-white/50" />
        <MagnifyingGlassIcon className="pointer-events-none absolute top-2 right-2 h-3.5 w-3.5 text-white/35" />
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-3 text-xs text-white/80">
        {tab === "satellites" && <SatellitePanel title={project.constellation.name || "Satellites"}
          satellites={project.satellites.filter((satellite) => `${satellite.id} ${satellite.name}`.toLowerCase().includes(search_content.toLowerCase()))} sat_states={frame?.satellites ?? []} />}
        {tab === "ground_stations" && <GroundStationPanel project={project} station_states={frame?.stations ?? []}
          search_content={search_content} is_editable={is_editable} on_project_change={on_project_change} />}
        {tab === "network" && <NetworkPanel links={frame?.links ?? []} has_frame={!!frame} search_content={search_content} />}
        {tab === "tasks" && <TasksPanel frame={frame} search_content={search_content} />}
      </div>
    </section>
  </div>;
};
