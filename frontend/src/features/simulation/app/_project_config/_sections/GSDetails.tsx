"use client";
import { MapPinIcon,PlusIcon,TrashIcon } from "@heroicons/react/24/outline";
import { useState } from "react";
import { GroundStation } from "../../../types";

interface GSDetailsProps {
  ground_stations: GroundStation[];
  update_list_item: (
    list_name: "ground_stations" | "rois",
    index: number,
    field: string,
    value: unknown
  ) => void;
  add_list_item: (list_name: "ground_stations" | "rois") => void;
  delete_list_item: (list_name: "ground_stations" | "rois", index: number) => void;
  select_location: (
    list_name: "ground_stations" | "rois",
    index: number
  ) => Promise<void>;
}

export const GSDetails = ({
  ground_stations,
  update_list_item,
  add_list_item,
  delete_list_item,
  select_location,
}: GSDetailsProps) => {
  const [import_open, set_import_open] = useState(false);
  const [import_text, set_import_text] = useState("");

  const handle_import = () => {
    try {
      // 支持两种格式：
      // 1) 直接 JSON 数组
      // 2) 包含变量名的文本，如 "ground_stations = [ ... ]"
      const last_index = ground_stations.length;
      let text = import_text.trim();
      const eq_idx = text.indexOf("=");
      if (eq_idx !== -1) {
        text = text.slice(eq_idx + 1).trim();
      }
      const arr = JSON.parse(text);
      if (!Array.isArray(arr)) throw new Error("JSON 需为数组");
      arr.forEach((value: unknown, i: number) => {
        if (!value || typeof value !== "object" || !("lat" in value) || !("lon" in value)) throw new Error("Each station requires lat and lon");
        const gs = value as { lat: unknown; lon: unknown; name?: unknown };
        if (typeof gs.lat !== "number" || typeof gs.lon !== "number" || !Number.isFinite(gs.lat) || !Number.isFinite(gs.lon) || Math.abs(gs.lat) > 90 || Math.abs(gs.lon) > 180) throw new Error("Invalid station coordinates");
        add_list_item("ground_stations");
        update_list_item("ground_stations", last_index + i, "name", typeof gs.name === "string" ? gs.name : "");
        update_list_item("ground_stations", last_index + i, "location", {
          lat: gs.lat,
          lon: gs.lon,
        });
      });
      set_import_open(false);
      set_import_text("");
    } catch (e) {
      alert(`导入失败: ${(e as Error).message}`);
    }
  };
  return (
    <div>
      <h3 className="text-lg text-sm text-white mb-3 flex justify-between items-center">
        Ground Stations
        <div className="flex gap-4">
          <button
            onClick={() => add_list_item("ground_stations")}
            className="text-white/80 hover:text-white flex items-center gap-1 transition-colors"
            type="button"
          >
            <PlusIcon className="w-5 h-5" />
            Add
          </button>
          <button
            onClick={() => set_import_open(true)}
            className="text-white/80 hover:text-white flex items-center gap-1 transition-colors"
            type="button"
          >
            <PlusIcon className="w-5 h-5" />
            Import
          </button>
        </div>
      </h3>
      {import_open && (
        <div className="mb-3">
          <textarea
            value={import_text}
            onChange={(e) => set_import_text(e.target.value)}
            className="w-full h-28 rounded-lg bg-white/20 px-2 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-gray-300"
            placeholder='e.g.: ground_stations = [{"name":"Goldstone","lat":35.2472,"lon":-116.7933}]'
          />
          <div className="mt-2 flex gap-2 items-center justify-end">
            <button
              type="button"
              onClick={handle_import}
              className="px-3 py-1 rounded bg-white/80 text-black text-sm hover:bg-white"
            >
              Confirm
            </button>
            <button
              type="button"
              onClick={() => { set_import_open(false); set_import_text(""); }}
              className="px-3 py-1 rounded border border-white text-white text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      {ground_stations.length === 0 && (
        <p className="text-gray-400 italic text-sm mb-2">No ground stations</p>
      )}
      {ground_stations.map((gs, i) => (
        <div key={i} className="mb-2">
          <div className="flex gap-4 mb-2 items-center justify-between">
            <div className="w-1/2 gap-2">
              <label className="block mb-1 text-xs">
                Name (ID: {gs.id ? gs.id.slice(-12): "N/A"})
              </label>
              <input
                type="text"
                value={typeof gs.name === "string" ? gs.name : ""}
                onChange={(e) =>
                  update_list_item("ground_stations", i, "name", e.target.value)
                }
                className="w-full rounded-lg bg-white/20 px-2 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-gray-300"
                placeholder="Ground station name"
              />
            </div>
            <div className="w-1/2 flex justify-between">
              <div>
                <label className="block mb-1 text-xs">Location</label>
                <p className="py-1 text-sm text-gray-400">
                  Lat {(gs.location?.lat ?? 0).toFixed(4)}°, Lon{" "}
                  {(gs.location?.lon ?? 0).toFixed(4)}°
                </p>
              </div>
              <label className="text-xs">altitude_m<input type="number" value={gs.altitude_m} onChange={(event) => update_list_item("ground_stations", i, "altitude_m", event.target.valueAsNumber)} className="w-24 bg-white/20 p-1" /></label>
              <div className="flex gap-2">
                <button
                  onClick={() => select_location("ground_stations", i)}
                  className="text-white/80 hover:text-blue-400 transition-colors"
                  title="Pick location"
                >
                  <MapPinIcon className="w-5 h-5 hover:cursor-pointer" />
                </button>
                <button
                  type="button"
                  onClick={() => delete_list_item("ground_stations", i)}
                  className="text-white/80 hover:text-red-400 transition-colors"
                  title="Delete station"
                >
                  <TrashIcon className="w-5 h-5 hover:cursor-pointer" />
                </button>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
