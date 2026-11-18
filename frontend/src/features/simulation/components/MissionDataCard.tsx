import ProcessBar from "@/features/simulation/components/ProcessBar";
import { TaskSnapshot } from "@/features/simulation/types/simulation";
import React from "react";

interface MissionDataCardProps {
  mission: TaskSnapshot;
}

const MissionDataCard: React.FC<MissionDataCardProps> = ({ mission }) => {
  const get_status = (mission: TaskSnapshot): string => {
    if (mission.is_done) {
      return "done";
    } else if (
      Number(mission.acted) === 5 &&
      (mission.workload_done ?? 0) > 0
    ) {
      return "comp";
    } else if (
      [1, 2, 3, 4].includes(Number(mission.acted)) &&
      (mission.data_sent ?? 0) > 0
    ) {
      return "tran";
    } else {
      return "idle";
    }
  };

  const status = get_status(mission);
  const status_color = ((s: string) => {
    switch (s) {
      case "idle":
        return "text-gray-600 border-gray-600 bg-gray-600/20";
      case "done":
        return "text-green-600 border-green-600 bg-green-600/20";
      case "comp":
        return "text-yellow-600 border-yellow-600 bg-yellow-600/20";
      case "tran":
        return "text-blue-600 border-blue-600 bg-blue-600/20";
      default:
        return "text-white border-white bg-white/20";
    }
  })(status);

  return (
    <div className="w-full p-2">
      <div className="flex justify-between mb-1">
        Task Status:
        <span
          className={`${status_color} px-3 rounded-full border text-xs`}
        >
          {status.toUpperCase()}
        </span>
      </div>
      <div className="mb-1">
        Location: Plane {mission.plane_at}, Order {mission.order_at}
      </div>
      <div className="mb-1">
        Latency: {mission.t_end - mission.t_start} slots
      </div>
      <div className="mb-1">
        {!mission.is_done && (
          <ProcessBar progress={mission.completion} name={"Completion"} />
        )}
        {mission.workload_percent != 0 && (
          <ProcessBar
            progress={mission.workload_percent}
            name={"Temp. Processing"}
          />
        )}
        {/* {mission.data_percent != 0 && ( */}
        <ProcessBar
          progress={mission.data_percent}
          name={"Temp. Transferring"}
        />
        {/* )} */}
      </div>
    </div>
  );
};

export default MissionDataCard;
