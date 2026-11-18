import MissionDataCard from "../../../components/MissionDataCard";
import ProcessBar from "../../../components/ProcessBar";
import type { SimulationSnapshot } from "../../../contracts/generated";
import { InventorySection, InfoItem } from "./InventorySection";

export default function TasksPanel({ frame, search_content }: { frame?: SimulationSnapshot; search_content: string }) {
  const tasks = (frame?.tasks ?? []).filter((task) => String(task.id).includes(search_content));
  const missions = (frame?.missions ?? []).filter((mission) => `${mission.id} ${mission.status} ${mission.position}`.toLowerCase().includes(search_content.toLowerCase()));
  return <>
    <div className="mb-4 space-y-1">
      <InfoItem label="Reward" value={frame?.info.reward.toFixed(2) ?? "0.00"} />
      <InfoItem label="Tasks" value={tasks.length + missions.length} />
      <InfoItem label="Completed" value={tasks.filter((task) => task.is_done).length + missions.filter((mission) => mission.status === "completed").length} />
      {!!tasks.length && <ProcessBar name="Total Completion" progress={tasks.reduce((sum, task) => sum + task.completion, 0) / tasks.length} />}
    </div>
    {!tasks.length && !missions.length && <p className="py-4 text-white/40">{frame ? "No matching tasks." : "Start a simulation to inspect tasks."}</p>}
    {tasks.map((task) => <InventorySection key={task.id} title={`Task ${task.id}`}><MissionDataCard mission={task} /></InventorySection>)}
    {missions.map((mission) => <InventorySection key={`physical:${mission.id}`} title={`Mission ${mission.id}`}>
      <InfoItem label="Status" value={mission.status} /><InfoItem label="Position" value={mission.position} />
      <InfoItem label="Inference layer" value={mission.inference_layer} /><InfoItem label="Data size" value={mission.data_size.toFixed(2)} />
      <InfoItem label="Deadline" value={mission.deadline} />
    </InventorySection>)}
  </>;
}
