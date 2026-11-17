"use client";
import {
MapPinIcon,
PlusIcon,
TrashIcon
} from "@heroicons/react/24/outline";
import { ROI } from "../../../types";

interface ROIDetailsProps {
  rois: ROI[];
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

export const ROIDetails = ({
  rois,
  update_list_item,
  add_list_item,
  delete_list_item,
  select_location,
}: ROIDetailsProps) => {
  return (
    <div>
      <h3 className="text-lg text-sm text-white mb-3 flex justify-between items-center">
        Regions of Interest (ROIs)
        <button
          onClick={() => add_list_item("rois")}
          className="text-white/80 hover:text-white flex items-center gap-1 transition-colors"
          type="button"
        >
          <PlusIcon className="w-5 h-5" />
          Add
        </button>
      </h3>
      {rois.length === 0 && (
        <p className="text-gray-400 italic text-sm mb-2">No ROIs</p>
      )}
      {rois.map((roi, i) => (
        <div key={i} className="mb-2">
          <div className="flex gap-4 mb-1 items-center justify-between">
            <div className="w-1/2 flex gap-2">
              <div className="flex-col">
                <label className="block mb-1 text-xs">
                  Name (ID: {roi.id.slice(-12)})
                </label>
                <input
                  type="text"
                  value={roi.name}
                  onChange={(e) =>
                    update_list_item("rois", i, "name", e.target.value)
                  }
                  className="rounded-lg bg-white/20 px-2 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-gray-300"
                  placeholder="ROI name"
                />
              </div>
              <div className="flex-col">
                <label className="block mb-1 text-xs text-sm">
                  Len * Wid (m)
                </label>
                <div className="flex items-center justify-center gap-1">
                  <input
                    type="number"
                    value={roi.length}
                    onChange={(e) =>
                      update_list_item(
                        "rois",
                        i,
                        "length",
                        parseFloat(e.target.value)
                      )
                    }
                    min={0}
                    className="w-full rounded-lg bg-white/20 px-2 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-gray-300"
                    placeholder="Enter length"
                  />
                  ·
                  <input
                    type="number"
                    value={roi.width || ""}
                    onChange={(e) =>
                      update_list_item(
                        "rois",
                        i,
                        "width",
                        e.target.value ? parseFloat(e.target.value) : roi.length
                      )
                    }
                    min={0}
                    className="w-full rounded-lg bg-white/20 px-2 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-gray-300"
                    placeholder="Enter width (optional)"
                  />
                </div>
              </div>
            </div>
            <div className="w-1/2 flex justify-between">
              <div>
                <label className="block mb-1 text-xs text-sm">Location</label>
                <p className="py-1 text-sm text-gray-400">
                  Lat {roi.location.lat.toFixed(4)}°, Lon{" "}
                  {roi.location.lon.toFixed(4)}°
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => select_location("rois", i)}
                  className="text-white/80 hover:text-blue-400 transition-colors"
                >
                  <MapPinIcon className="w-5 h-5 hover:cursor-pointer" />
                </button>
                <button
                  type="button"
                  onClick={() => delete_list_item("rois", i)}
                  className="text-white/80 hover:text-red-400 transition-colors"
                >
                  <TrashIcon className="w-5 h-5 hover:cursor-pointer" />
                </button>
              </div>
            </div>
          </div>
          <div className="flex gap-2 mb-4 items-center justify-between"></div>
        </div>
      ))}
    </div>
  );
};
