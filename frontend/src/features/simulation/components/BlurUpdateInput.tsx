import { useState } from "react";

type CommonProps = { value: unknown; min?: number; max?: number };
type InputProps = CommonProps & (
  { type: "number"; on_save: (value: number) => void } |
  { type?: "text" | "datetime-local"; on_save: (value: string) => void }
);
function InputEditor(props: InputProps) {
  const initial = typeof props.value === "string" || typeof props.value === "number" ? String(props.value) : "";
  const [local_value, set_local_value] = useState(props.type === "datetime-local" ? initial.slice(0, 16) : initial);
  return <input type={props.type ?? "text"} value={local_value} min={props.min} max={props.max}
    onChange={(event) => set_local_value(event.target.value)}
    onBlur={(event) => {
      if (!event.currentTarget.checkValidity()) { event.currentTarget.reportValidity(); return; }
      if (props.type === "number") {
        if (local_value.trim() && Number.isFinite(Number(local_value))) props.on_save(Number(local_value));
      } else props.on_save(local_value);
    }} className="w-full rounded-lg bg-white/20 px-2 py-1 text-white text-sm" />;
}
export function BlurUpdateInput(props: InputProps) {
  return <InputEditor key={`${props.type}:${String(props.value)}`} {...props} />;
}
