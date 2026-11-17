// components/SatDataPercentageCard.tsx

import { SatelliteSnapshot } from "@/features/simulation/types/simulation";
import React from "react";
import ProcessBar from "./ProcessBar";

interface SatDataPercentageCardProps {
  sat: SatelliteSnapshot | undefined;
}

const SatDataPercentageCard: React.FC<SatDataPercentageCardProps> = ({
  sat,
}) => {
  const is_undefined = sat === undefined;

  const battery_percent = is_undefined ? 0.0 : sat.battery_percent / 100;
  // const procBuffDataRatio = isUndefined ? 0.0 : sat.procBuffDataRatio;
  // const storageDataRatio = isUndefined ? 0.0 : sat.storageDataRatio;

  // let BatteryIcon = Battery0Icon;
  // let batteryColor = "text-red-600";
  // if (batteryPercent >= 0.9) {
  //   BatteryIcon = Battery100Icon;
  //   batteryColor = "text-green-600";
  // } else if (batteryPercent >= 0.6) {
  //   BatteryIcon = Battery50Icon;
  //   batteryColor = "text-lime-600";
  // } else if (batteryPercent >= 0.3) {
  //   BatteryIcon = Battery50Icon;
  //   batteryColor = "text-yellow-600";
  // } else if (isUndefined) {
  //   BatteryIcon = SignalIcon;
  //   batteryColor = "text-gray-04";
  // }

  return (
    <div className={`w-full ${is_undefined ? "opacity-50" : ""} `}>
      <ProcessBar progress={battery_percent} name="Battery" />
    </div>
  );
};

export default SatDataPercentageCard;
