import { useState } from "react";
import { PlusIcon, PencilSquareIcon, TrashIcon } from "@heroicons/react/24/outline";
import type { GroundStation, Project, StationSnapshot } from "../../../contracts/generated";
import { save_project } from "../../../communication/projects";
import StationStatusCard from "../../../components/StationStatusCard";
import GroundStationEditor from "./GroundStationEditor";
import { InfoItem } from "./InventorySection";

export default function GroundStationPanel({ project, station_states, search_content, is_editable, on_project_change }: {
  project: Project; station_states: StationSnapshot[]; search_content: string; is_editable: boolean;
  on_project_change: (project: Project) => void;
}) {
  const [editor, set_editor] = useState<{ ground_station: GroundStation; is_new: boolean } | null>(null);
  const [is_saving, set_is_saving] = useState(false);
  const [error, set_error] = useState("");
  const stations = project.ground_stations.filter((station) => `${station.id} ${station.name}`.toLowerCase().includes(search_content.toLowerCase()));
  const commit = async (ground_stations: GroundStation[]) => {
    set_is_saving(true); set_error("");
    try { on_project_change(await save_project({ ...project, ground_stations })); }
    finally { set_is_saving(false); }
  };
  const save_station = async (ground_station: GroundStation) => {
    if (!is_editable) throw new Error("Stop the simulation before editing stations.");
    const exists = project.ground_stations.some((station) => station.id === ground_station.id);
    await commit(exists ? project.ground_stations.map((station) => station.id === ground_station.id ? ground_station : station)
      : [...project.ground_stations, ground_station]);
    set_editor(null);
  };
  const delete_station = async (ground_station: GroundStation) => {
    if (!is_editable) return;
    if (project.experiment.missions.some((mission) => mission.source_node_id === ground_station.id || mission.end_node_id === ground_station.id)) {
      set_error("This station is referenced by a configured mission."); return;
    }
    if (!window.confirm(`Delete ground station “${ground_station.name}”?`)) return;
    try { await commit(project.ground_stations.filter((station) => station.id !== ground_station.id)); }
    catch (error) { set_error(error instanceof Error ? error.message : "Delete failed"); }
  };
  return <>
    <div className="mb-4 flex items-center justify-between gap-2">
      <span>{project.ground_stations.length} stations</span>
      <button type="button" disabled={!is_editable || is_saving} onClick={() => set_editor({ is_new: true, ground_station: {
        id: crypto.randomUUID(), project_id: project.project_id, name: "", location: { lat: 0, lon: 0 }, altitude_m: 0,
      } })} className="inline-flex items-center gap-1 rounded px-2 py-1 hover:bg-white/10 disabled:opacity-30">
        <PlusIcon className="h-4 w-4" />Add
      </button>
    </div>
    {!is_editable && <p className="mb-4 text-white/45">Stop the simulation to edit ground stations.</p>}
    {error && <p role="alert" className="mb-3 text-red-200">{error}</p>}
    {!stations.length && <p className="py-4 text-white/40">{search_content ? "No matching stations." : "No ground stations. Add one to get started."}</p>}
    {stations.map((station) => {
      const state = station_states.find((state) => state.id === station.id);
      return <div key={station.id} className="mb-3 rounded border border-white/15 p-3">
        <div className="mb-2 flex items-center justify-between gap-1">
          <span className="min-w-0 truncate font-medium text-white">{station.name}</span>
          <div className="flex shrink-0">
            <button type="button" aria-label={`Edit ${station.name}`} disabled={!is_editable || is_saving}
              onClick={() => set_editor({ ground_station: station, is_new: false })} className="p-1 hover:text-white disabled:opacity-30"><PencilSquareIcon className="h-4 w-4" /></button>
            <button type="button" aria-label={`Delete ${station.name}`} disabled={!is_editable || is_saving}
              onClick={() => void delete_station(station)} className="p-1 hover:text-white disabled:opacity-30"><TrashIcon className="h-4 w-4" /></button>
          </div>
        </div>
        <InfoItem label="Latitude" value={station.location.lat.toFixed(4)} />
        <InfoItem label="Longitude" value={station.location.lon.toFixed(4)} />
        <InfoItem label="Altitude (m)" value={station.altitude_m ?? 0} />
        <details className="mt-2"><summary className="cursor-pointer text-white/45">Details</summary>
          <InfoItem label="ID" value={station.id} />
          {state && <StationStatusCard gs={state} />}
        </details>
      </div>;
    })}
    {editor && <GroundStationEditor {...editor} is_saving={is_saving} on_save={save_station} on_close={() => set_editor(null)} />}
  </>;
}
