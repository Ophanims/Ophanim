"use client";
import {
local_to_utciso_string,
to_input_local,
} from "@/features/simulation/services/date_time/time_convert";
import { Experiment,GroundStation,ROI } from "@/features/simulation/types";
import { PlusIcon,TrashIcon } from "@heroicons/react/24/outline";
import { BlurUpdateInput } from "../../../components/BlurUpdateInput";

interface ExperimentDetailsProps {
  show_time?: boolean;
  experiment: Experiment;
  ground_stations: GroundStation[];
  rois: ROI[];
  update_field: (path: string[], value: unknown) => void;
  add_list_item: (list_name: "ground_stations" | "rois" | "missions") => void;
  delete_list_item: (
    list_name: "ground_stations" | "rois" | "missions",
    index: number
  ) => void;
  update_list_item: (
    list_name: "missions",
    index: number,
    field: string,
    value: unknown
  ) => void;
}

export const ExperimentDetails = ({
  show_time = true,
  experiment,
  ground_stations,
  rois,
  update_field,
  update_list_item,
  add_list_item,
  delete_list_item,
}: ExperimentDetailsProps) => {

  return (
    <div className="mt-4 mb-8 mx-20">
      {show_time && <>
      <div className="mt-8 mb-2">
        <span className="text-xl">Time & Duration</span>
      </div>

      {/* Editable Inputs */}
      <div className="mb-4">
        <label className="block mb-1 text-xs">Time Slot (s)</label>
        <BlurUpdateInput
          type="number"
          value={experiment.time_slot ?? ""}
          on_save={(val) => update_field(["experiment", "time_slot"], val)}
        />
      </div>

      <div className="mb-4">
        <label className="block mb-1 text-xs">Start Time</label>
        <BlurUpdateInput
          type="datetime-local"
          value={experiment.start_time ? to_input_local(experiment.start_time) : ""}
          on_save={(val) => {
            // val 是本地时间字符串 '2025-06-25T09:04'
            const iso = local_to_utciso_string(val); // 转为 '2025-06-25T01:04:00.000Z'
            update_field(["experiment", "start_time"], iso);
          }}
        />
      </div>

      <div className="mb-4">
        <label className="block mb-1 text-xs">End Time</label>
        <BlurUpdateInput
          type="datetime-local"
          value={experiment.end_time ? to_input_local(experiment.end_time) : ""}
          on_save={(val) => {
            const iso = local_to_utciso_string(val);
            update_field(["experiment", "end_time"], iso);
          }}
        />
      </div>
      </>}
      <div className="mt-8 mb-2">
        <span className="text-xl">Missions</span>
      </div>
      <button
        className="flex items-center justify-center w-full p-4 mb-4
        text-white hover:bg-yellow-600 hover:cursor-pointer 
        rounded border border-white/10 transition-colors"
        onClick={() => add_list_item("missions")}
      >
        <PlusIcon className="h-5 w-5" />
      </button>
      <div className="space-y-4">
        {(experiment.missions ?? []).map((mission, i) => (
          <div key={i} className="flex border border-white/10 rounded-lg">
            <div className="w-full p-3">
              <div className="flex w-full gap-4">
                <div className="mb-2 w-1/2">
                  <label className="block mb-1 text-xs">Name</label>
                  <BlurUpdateInput
                    type="text"
                    value={mission.name ?? ""}
                    on_save={(val) => update_list_item("missions", i, "name", val)}
                  />
                </div>
                <div className="mb-2 w-1/2">
                  <label className="block mb-1 text-xs">Target ROI</label>
                  <select
                    className="w-full bg-gray-06 text-sm text-white rounded-lg px-2 py-1"
                    value={mission.target_id ?? ""}
                    onChange={(e) =>
                      update_list_item("missions", i, "target_id", e.target.value)
                    }
                  >
                    <option value="">Please select target ROI</option>
                    {rois.map((roi) => (
                      <option key={roi.id} value={roi.id}>
                        {roi.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex w-full gap-4">
                <div className="mb-2 w-1/2">
                  <label className="block mb-1 text-xs">Source Node</label>
                  <select
                    className="w-full bg-gray-06 text-sm text-white rounded-lg px-2 py-1"
                    value={mission.source_node_id ?? ""}
                    onChange={(e) =>
                      update_list_item(
                        "missions",
                        i,
                        "source_node_id",
                        e.target.value
                      )
                    }
                  >
                    <option value="">Please select source node</option>
                    {ground_stations.map((gs) => (
                      <option key={gs.id} value={gs.id}>
                        {gs.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="mb-2 w-1/2">
                  <label className="block mb-1 text-xs">End Node</label>
                  <select
                    className="w-full bg-gray-06 text-sm text-white rounded-lg px-2 py-1"
                    value={mission.end_node_id ?? ""}
                    onChange={(e) =>
                      update_list_item("missions", i, "end_node_id", e.target.value)
                    }
                  >
                    <option value="">Please select end node</option>
                    {ground_stations.map((gs) => (
                      <option key={gs.id} value={gs.id}>
                        {gs.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex w-full gap-4">
                <div className="mb-2 w-1/3">
                  <label className="block mb-1 text-xs">Start Time</label>
                  <BlurUpdateInput
                    type="datetime-local"
                    value={
                      mission.start_time ? to_input_local(mission.start_time) : ""
                    }
                    on_save={(val) =>
                      update_list_item(
                        "missions",
                        i,
                        "start_time",
                        local_to_utciso_string(val)
                      )
                    }
                  />
                </div>
                <div className="mb-2 w-1/3">
                  <label className="block mb-1 text-xs">End Time</label>
                  <div className="w-full flex items-center px-2 py-1 text-sm rounded-lg bg-gray-06">
                    <span className={`font-semibold text-white`}>
                      {mission.end_time ?? "Not calculated"}
                    </span>
                    {!mission.end_time && (
                      <span className="ml-2 text-gray-04">
                        (Not calculated)
                      </span>
                    )}
                  </div>
                </div>
                <div className="mb-2 w-1/3">
                  <label className="block mb-1 text-xs">Duration (s)</label>
                  <div className="w-full flex items-center px-2 py-1 text-sm rounded-lg bg-gray-06">
                    <span className={`font-semibold text-white`}>
                      {mission.duration === -1
                        ? "Not calculated"
                        : mission.duration}
                    </span>
                    {!mission.duration && (
                      <span className="ml-2 text-gray-04">
                        (Not calculated)
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div
              className="w-12 flex items-center justify-center 
              rounded-r-lg bg-red-800/20 text-red-400
              hover:text-white hover:cursor-pointer hover:bg-red-700 transition-colors"
              onClick={() => delete_list_item("missions", i)}
            >
              <TrashIcon className="h-6 w-6 " />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
