import LinkDataCard from "@/features/simulation/components/LinkDataCard";
import MissionDataCard from "@/features/simulation/components/MissionDataCard";
import ProcessBar from "@/features/simulation/components/ProcessBar";
import { ShakingIcon } from "@/features/simulation/components/ShakingIcon";
import StationStatusCard from "@/features/simulation/components/StationStatusCard";
import { GroundStation,Project,ROI,SatelliteConfig } from "@/features/simulation/types";
import {
SatelliteSnapshot,
StationSnapshot
} from "@/features/simulation/types/simulation";
import {
ChevronRightIcon,
ClockIcon,
Cog6ToothIcon,
CubeIcon,
EllipsisHorizontalIcon,
LinkIcon,
MagnifyingGlassIcon,
} from "@heroicons/react/24/outline";
import { useState } from "react";
import { useFrames } from "../useFramesContext";

import {
ArrowsRightLeftIcon,
ArrowsUpDownIcon,
BoltIcon,
SunIcon,
} from "@heroicons/react/24/solid";

interface InventoryProps {
  project: Project;
}

export const Inventory = ({ project }: InventoryProps) => {
  const { frames, selected_frame_index } = useFrames();
  const [search, set_search] = useState("");
  const [tab, set_tab] = useState("Entities");
  const frame = frames[selected_frame_index];
  const sat_states = frame?.satellites ?? [];
  const link_states = frame?.links ?? [];
  const mission_states = frame?.tasks ?? [];
  const station_states = frame?.stations ?? [];
  const reward = frame?.info.reward ?? 0;

  // 搜索过滤函数
  const filter_by_search = <T extends { id: string; name?: string | null }>(items: T[], keys: (keyof T)[]) =>
    items.filter((item) =>
      keys.some((key) =>
        String(item[key] ?? "")
          .toLowerCase()
          .includes(search.toLowerCase())
      )
    );

  const filtered_sats = filter_by_search(project.satellites ?? [], ["id", "name"]);
  const filtered_gs = filter_by_search(project.ground_stations ?? [], [
    "id",
    "name",
  ]);
  const filtered_ro_is = filter_by_search(project.rois ?? [], ["id", "name"]);
  return (
    <div className="flex h-full w-full">
      <div className="h-full flex flex-col items-center justify-between border border-white/10">
        <div>
          <ShakingIcon
            className={`p-2 hover:text-white hover:cursor-pointer 
            ${
              tab === "Entities"
                ? "text-yellow-600 border-l-2"
                : "text-white/60"
            }`}
            onClick={() => set_tab("Entities")}
          >
            <CubeIcon className="h-7 w-7" />
          </ShakingIcon>
          <ShakingIcon
            className={`p-2 hover:text-white hover:cursor-pointer
            ${
              tab === "Search" ? "text-yellow-600 border-l-2" : "text-white/60"
            }`}
            onClick={() => set_tab("Search")}
          >
            <MagnifyingGlassIcon className="h-7 w-7" />
          </ShakingIcon>
          <ShakingIcon
            className={`p-2 hover:text-white hover:cursor-pointer 
            ${
              tab === "Timeline"
                ? "text-yellow-600 border-l-2"
                : "text-white/60"
            }`}
            onClick={() => set_tab("Timeline")}
          >
            <ClockIcon className="h-7 w-7" />
          </ShakingIcon>
          <ShakingIcon
            className={`p-2 hover:text-white hover:cursor-pointer 
            ${
              tab === "Links" ? "text-yellow-600 border-l-2" : "text-white/60"
            }`}
            onClick={() => set_tab("Links")}
          >
            <LinkIcon className="h-7 w-7" />
          </ShakingIcon>
        </div>
        <ShakingIcon className="p-2">
          <Cog6ToothIcon className="h-7 w-7 text-gray-500" />
        </ShakingIcon>
      </div>
      <div className="w-full h-full flex flex-col px-3 py-2">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xs font-semibold">EXPLORER</h2>
        </div>
        {tab === "Links" && (
          <div className="flex flex-col h-full text-xs text-white/80">
            <div className="overflow-y-auto [&::-webkit-scrollbar]:hidden [scrollbar-width:none]">
              <CollapsibleSection title="Inter-Satellite Links">
                {link_states.length === 0 ? (
                  <div className="flex items-center justify-center py-4">
                    <p className="text-gray-04">Simulation has not started</p>
                  </div>
                ) : (
                  link_states
                    .filter((link) => link.type === "ISL")
                    .map((link, i) => <LinkDataCard key={i} link={link} />)
                )}
              </CollapsibleSection>
              <CollapsibleSection title="Uplink">
                {link_states.length === 0 ? (
                  <div className="flex items-center justify-center py-4">
                    <p className="text-gray-04">Simulation has not started</p>
                  </div>
                ) : (
                  link_states
                    .filter((link) => link.type === "UL")
                    .map((link, i) => <LinkDataCard key={i} link={link} />)
                )}
              </CollapsibleSection>
              <CollapsibleSection title="Downlink">
                {link_states.length === 0 ? (
                  <div className="flex items-center justify-center py-4">
                    <p className="text-gray-04">Simulation has not started</p>
                  </div>
                ) : (
                  link_states
                    .filter((link) => link.type === "DL")
                    .map((link, i) => <LinkDataCard key={i} link={link} />)
                )}
              </CollapsibleSection>
            </div>
          </div>
        )}
        {tab === "Timeline" && (
          <div className="flex flex-col h-full text-xs text-white/80">
            <div className="py-2">
              <p className="mb-1">Reward: {reward.toFixed(2)}</p>
              <p className="mb-1">Total Missions: {mission_states.length}</p>
              <p className="mb-1">
                Completed: {mission_states.filter((m) => m.is_done).length}
              </p>
              <ProcessBar
                progress={
                  mission_states.reduce((sum, m) => sum + m.completion, 0) /
                  mission_states.length
                }
                name={"Total Completion"}
              />
            </div>
            {mission_states.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-04">Simulation has not started</p>
              </div>
            ) : (
              <div className="overflow-y-auto [&::-webkit-scrollbar]:hidden [scrollbar-width:none]">
                {mission_states.map((mission, i) => (
                  <CollapsibleSection
                    title={"Mission NO." + mission.id.toString()}
                    key={i}
                  >
                    <MissionDataCard mission={mission} />
                  </CollapsibleSection>
                ))}
              </div>
            )}
          </div>
        )}
        {tab === "Search" && (
          <div className="flex flex-col h-full text-xs text-white/80">
            <div className="relative text-gray-400 mb-4">
              <input
                type="text"
                placeholder="Search items..."
                value={search}
                onChange={(e) => set_search(e.target.value)}
                className="w-full rounded text-sm bg-gray-07 px-2 py-1 text-gray-02 placeholder-gray-02 focus:outline-none focus:ring-2 focus:ring-gray-300"
              />
              <MagnifyingGlassIcon className="w-4 h-4 absolute right-3 top-1.5 text-gray-04 pointer-events-none" />
            </div>
            <div className="overflow-y-auto [&::-webkit-scrollbar]:hidden [scrollbar-width:none]">
              <CollapsibleSection title={project.constellation.name}>
                {filtered_sats.map((sat) => (
                  <SatelliteItem
                    key={sat.id}
                    sat={sat}
                    sat_frame={(sat_states ?? []).find((s) => s.id === sat.id)}
                  />
                ))}
              </CollapsibleSection>
              <CollapsibleSection title="Ground Stations">
                {filtered_gs.map((gs) => (
                  <GroundStationItem
                    key={gs.id}
                    gs={gs}
                    gs_frame={(station_states ?? []).find((g) => g.id === gs.id)}
                  />
                ))}
              </CollapsibleSection>
              <CollapsibleSection title="ROIs">
                {filtered_ro_is.map((roi) => (
                  <RoiItem key={roi.id} roi={roi} />
                ))}
              </CollapsibleSection>
            </div>
          </div>
        )}
        {tab === "Entities" && (
          <div className="flex flex-col h-full text-xs text-white/80">
            <div className="flex-1 overflow-y-auto [&::-webkit-scrollbar]:hidden [scrollbar-width:none]">
              <CollapsibleSection title={project.constellation.name}>
                {project.satellites.map((sat) => (
                  <SatelliteItem
                    key={sat.id}
                    sat={sat}
                    sat_frame={(sat_states ?? []).find((s) => s.id === sat.id)}
                  />
                ))}
              </CollapsibleSection>
              <CollapsibleSection title="Ground Stations">
                {project.ground_stations.map((gs) => (
                  <GroundStationItem
                    key={gs.id}
                    gs={gs}
                    gs_frame={(station_states ?? []).find((g) => g.id === gs.id)}
                  />
                ))}
              </CollapsibleSection>
              <CollapsibleSection title="ROIs">
                {project.rois.map((roi) => (
                  <RoiItem key={roi.id} roi={roi} />
                ))}
              </CollapsibleSection>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// 折叠 Section 组件
function CollapsibleSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  const [open, set_open] = useState(true);

  return (
    <div className="mb-4">
      <div
        className="flex items-center cursor-pointer select-none mb-2"
        onClick={() => set_open(!open)}
      >
        <ChevronRightIcon
          className={`w-4 h-4 inline-block mr-1 transition-transform ${
            open ? "rotate-90" : ""
          }`}
          aria-hidden="true"
        />
        <span className="text-white text-xs cursor-pointer select-none">
          {title.toUpperCase()}
        </span>
      </div>
      <div className="space-y-2">{open && children}</div>
    </div>
  );
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

function GroundStationItem({
  gs,
  gs_frame,
}: {
  gs: GroundStation;
  gs_frame: StationSnapshot | undefined;
}) {
  const [expanded, set_expanded] = useState(false);
  const [folded, set_folded] = useState(false);
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
            onMouseOver={() => set_expanded(true)}
            onMouseLeave={() => set_expanded(false)}
          />
          <span>{gs.name}</span>
        </div>
        <EllipsisHorizontalIcon
          className="w-4 h-4 inline-block mx-1 text-gray-400"
          onMouseOver={() => set_expanded(true)}
          onMouseLeave={() => set_expanded(false)}
        />
        {expanded && (
          <div className="absolute right-0 z-10 w-48 bg-gray-07 p-2 rounded-md">
            <InfoItem label="ID" value={gs.id.slice(-6)} />
            <InfoItem label="Name" value={gs.name} />
            <InfoItem label="Lat" value={gs.location.lat} />
            <InfoItem label="Lon" value={gs.location.lon} />
          </div>
        )}
      </div>
      {folded && gs_frame && (
        <div className="mt-1 mb-4">
          <StationStatusCard key={gs.id} gs={gs_frame} />
        </div>
      )}
    </div>
  );
}

function RoiItem({ roi }: { roi: ROI }) {
  const [expanded, set_expanded] = useState(false);
  return (
    <div className="select-none relative ml-4 cursor-pointer">
      <div
        className="text-white/80 hover:text-white transition-colors"
        onMouseOver={() => set_expanded(true)}
        onMouseLeave={() => set_expanded(false)}
      >
        {roi.name}
        {expanded && (
          <div className="absolute right-0 bottom-0 z-10 w-48 bg-gray-07 p-2 rounded-md">
            <InfoItem label="ID" value={roi.id.slice(-6)} />
            <InfoItem label="Name" value={roi.name} />
            <InfoItem label="Length" value={roi.length} />
            <InfoItem label="Width" value={roi.width} />
            <InfoItem label="Lat" value={roi.location.lat} />
            <InfoItem label="Lon" value={roi.location.lon} />
          </div>
        )}
      </div>
    </div>
  );
}

// 单项信息组件
function InfoItem({ label, value }: { label: string; value: string | number | boolean | null | undefined }) {
  return (
    <div className="flex justify-between gap-2 text-white/70 text-xs">
      <span>{label}</span>
      <span className="text-right break-all">{value ?? "-"}</span>
    </div>
  );
}
