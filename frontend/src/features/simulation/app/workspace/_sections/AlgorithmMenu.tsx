import { useId, useRef } from "react";
import type { Project } from "../../../contracts/generated";

type Algorithm = NonNullable<Project["algorithm"]>;
const ALGORITHMS: Array<{ algorithm: Algorithm; label: string }> = [
  { algorithm: "ophanim", label: "Ophanim Physics" },
  { algorithm: "geometry", label: "Geometry" },
  { algorithm: "l2d2", label: "L2D2" },
  { algorithm: "phoenix", label: "PHOENIX" },
  { algorithm: "mhspo", label: "MHSPO" },
  { algorithm: "ppo", label: "PPO" },
];

export default function AlgorithmMenu({ algorithm, on_algorithm_change, disabled, is_open, on_open, on_close }: {
  algorithm: Algorithm;
  on_algorithm_change: (algorithm: Algorithm) => void;
  disabled: boolean;
  is_open: boolean;
  on_open: () => void;
  on_close: () => void;
}) {
  const menu_id = useId();
  const button_ref = useRef<HTMLButtonElement>(null);
  return <div className="relative" onKeyDown={(event) => {
    if (event.key === "Escape") { button_ref.current?.focus(); on_close(); }
  }}>
    <button ref={button_ref} type="button" aria-haspopup="menu" aria-expanded={is_open && !disabled}
      aria-controls={is_open ? menu_id : undefined} disabled={disabled}
      onMouseEnter={on_open} onFocus={on_open} onClick={on_open}
      className="px-3 py-1 text-white/80 transition-colors hover:cursor-pointer hover:bg-white/10 disabled:cursor-default disabled:text-white/30">
      Algorithm
    </button>
    {is_open && !disabled && <div id={menu_id} role="menu" aria-label="Algorithm" className="absolute left-0 top-full z-20 w-52 bg-gray-08 py-1">
      {ALGORITHMS.map((option) => <button key={option.algorithm} type="button" role="menuitemradio"
        aria-checked={algorithm === option.algorithm}
        onClick={() => { on_algorithm_change(option.algorithm); on_close(); }}
        className="flex w-full items-center justify-between px-2 py-1 text-left text-sm text-white/80 transition-colors hover:bg-white/10 hover:text-white">
        {option.label}<span aria-hidden="true">{algorithm === option.algorithm ? "✓" : ""}</span>
      </button>)}
    </div>}
  </div>;
}
