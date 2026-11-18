import { useState } from "react";
import ProcessBar from "../../../components/ProcessBar";
import type { SatelliteConfig, SatelliteSnapshot } from "../../../contracts/generated";
import { ChevronRightIcon } from "@heroicons/react/24/outline";
import { SunIcon, ArrowsRightLeftIcon, ArrowsUpDownIcon, BoltIcon } from "@heroicons/react/24/solid";
import { InventorySection, InfoItem } from "./InventorySection";

export default function SatellitePanel({ satellites, sat_states, title }: {
  satellites: SatelliteConfig[]; sat_states: SatelliteSnapshot[]; title: string;
}) {
  return <InventorySection title={title}>
    {!satellites.length && <p className="py-4 text-white/40">No matching satellites.</p>}
    {satellites.map((sat) => <SatelliteItem key={sat.id} sat={sat} sat_frame={sat_states.find((state) => state.id === sat.id)} />)}
  </InventorySection>;
}

function SatelliteItem({
  sat,
  sat_frame,
}: {
  sat: SatelliteConfig;
  sat_frame: SatelliteSnapshot | undefined;
}) {
  // const [expanded, setExpanded] = useState(false);
  const [folded, set_folded] = useState(true);
  // Remove useState for satStates, just use satFrame directly
  return (
    <div className="select-none relative ml-4 cursor-pointer">
      <div
        className="flex items-center justify-between text-white/80 hover:text-white transition-colors"
        onClick={() => set_folded(!folded)}
      >
        <div className="flex items-center">
          <ChevronRightIcon
            className={`w-4 h-4 inline-block mr-1 transition-transform ${
              folded ? "rotate-90" : ""
            }`}
            aria-hidden="true"
          />
          <span>{sat.name}</span>
        </div>
        {/* <div
          onMouseOver={() => setExpanded(true)}
          onMouseLeave={() => setExpanded(false)}
        >
          <EllipsisHorizontalIcon className="w-4 h-4 inline-block mx-1 text-gray-400" />

          {expanded && (
            <div className="absolute right-0 z-10 w-32 bg-gray-07 p-2 rounded-md">
              <InfoItem label="ID" value={sat.id.slice(-6)} />
              <InfoItem label="Name" value={sat.name} />
              <InfoItem label="Plane" value={sat.plane} />
              <InfoItem label="Order" value={sat.order} />
            </div>
          )}
        </div> */}
      </div>
      {folded && (
        <>
          <div className="mt-1 mb-2 px-2">
            <div className="flex items-center justify-between my-1">
              <SunIcon
                className={`w-4 h-4 inline-block mr-1 transition-transform ${
                  sat_frame?.is_charging ? "text-yellow-400" : "text-gray-600"
                }`}
                aria-hidden="true"
              />
              <ArrowsRightLeftIcon
                className={`w-4 h-4 inline-block mr-1 transition-transform ${
                  sat_frame?.is_communicating_isl ? "text-purple-400" : "text-gray-600"
                }`}
                aria-hidden="true"
              />
              <ArrowsUpDownIcon
                className={`w-4 h-4 inline-block mr-1 transition-transform ${
                  sat_frame?.is_communicating_sgl ? "text-orange-400" : "text-gray-600"
                }`}
                aria-hidden="true"
              />
              <BoltIcon
                className={`w-4 h-4 inline-block mr-1 transition-transform ${
                  sat_frame?.is_processing ? "text-white" : "text-gray-600"
                }`}
                aria-hidden="true"
              />
            </div>
            <InfoItem
              label="Gain"
              value={sat_frame ? sat_frame.gain_percent.toFixed(2) + "%" : "0.00"}
            />
            <InfoItem
              label="Cost"
              value={sat_frame ? sat_frame.cost_percent.toFixed(2) + "%" : "0.00"}
            />
            {/* <SatDataPercentageCard key={sat.id} sat={satFrame} /> */}

            <ProcessBar
              progress={sat_frame ? sat_frame.battery_percent / 100 : 0}
              name={"Battery Level"}
            />
          </div>
        </>
      )}
    </div>
  );
}

