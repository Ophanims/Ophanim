import { to_input_local } from "@/features/simulation/services/date_time/time_convert";

interface ClockWidgetProps {
  frame_counter: number; // 外部传入的 timeslot 编号
  time: string;
}

export default function ClockWidget({ frame_counter, time }: ClockWidgetProps) {
  // console.log("ClockWidget", timeSlot, time);
  return (
    <div className="select-none text-white/30 text-xs px-4 py-2 text-right">
      <div>{to_input_local(time)}</div>
      <div>
        Frame: <span className="text-white/80">{frame_counter}</span>
      </div>
    </div>
  );
}