import { SpinnerWidget } from "@/features/simulation/components/SpinnerWidget";
import { Project } from "@/features/simulation/types";
import {
ArrowPathIcon,
PlayIcon,
PowerIcon
} from "@heroicons/react/24/outline";
import { useState } from "react";
import AlgorithmMenu from "./AlgorithmMenu";

type MenuItem = {
  label: string;
  children: string[];
};

type MenuBarProps = {
  className?: string;
  project: Project;
  algorithm: NonNullable<Project["algorithm"]>;
  on_algorithm_change: (algorithm: NonNullable<Project["algorithm"]>) => void;
  disabled: boolean;
  is_connected: boolean;
  is_running: boolean;
  is_loading: boolean;
  on_open_parameters: () => void;
  on_menu_click?: (parent: string, child: string) => void;
  on_run_simulation?: () => void;
  on_pause_simulation?: () => void;
  on_stop_simulation?: () => void;
};

const menu_items: MenuItem[] = [
  {
    label: "Project",
    children: ["Config", "Import", "Export", "Save", "Exit"],
  },
  { label: "Parameters", children: [] },
  {
    label: "View",
    children: [
      // "Terminal",
      "Inventory",
      "Controller",
    ],
  },
  {
    label: "Visualization",
    children: [
      "Universe View",
      "Geometry View",
      "Object View",
      "Map View",
      "Satellite Panel",
      "Data Flow Panel",
    ],
  },
  {
    label: "Simulation",
    children: [
      "Train Model",
      "Launch Simulation",
      "Shutdown",
      "Auto Testing",
    ],
  },
];

const button_base = "px-3 py-1 transition-colors";
const button_active = "text-white/80 hover:bg-white/10 hover:cursor-pointer";
const button_disabled = "text-white/30";

const child_button_base =
  "block text-left px-2 py-1 text-sm w-full transition-colors";

const MenuBar = ({
  className = "",
  algorithm, on_algorithm_change,
  disabled, is_connected, is_running,
  is_loading,
  on_menu_click, on_open_parameters,
  on_run_simulation,
  on_pause_simulation,
  on_stop_simulation,
}: MenuBarProps) => {
  const [open_menu, set_open_menu] = useState<number | null>(null);


  const is_menu_disabled = (label: string) => label === "Parameters"
    ? is_connected || is_loading
    : disabled && label !== "Visualization" && label !== "Simulation";

  return (
    <div
      className={`flex items-center justify-between bg-gray-08 backdrop-blur-sm border-b border-white/10 px-2 space-x-6 text-sm font-medium z-10 relative ${className}`}
      onMouseLeave={() => set_open_menu(null)}
    >
      <div className="flex">
        {menu_items.map((menu, idx) => (
          <div key={menu.label} className="relative">
            <button
              className={`${button_base} ${
                is_menu_disabled(menu.label)
                  ? button_disabled
                  : button_active
              }`}
              onMouseEnter={() => set_open_menu(idx)}
              onFocus={() => set_open_menu(idx)}
              onClick={() => {
                if (menu.label === "Parameters") { set_open_menu(null); on_open_parameters(); }
                else set_open_menu(idx);
              }}
              type="button"
              disabled={
                is_menu_disabled(menu.label)
              }
            >
              {menu.label}
            </button>
            {open_menu === idx && menu.children.length > 0 && (
              <div className="absolute left-0 top-full z-20 w-52 rounded-md border border-white/25 bg-neutral-800 py-1 shadow-xl shadow-black/50 animate-fade-in">
                {menu.children.map((child) => (
                  <button
                    key={child}
                    className={`${child_button_base} ${
                      (is_menu_disabled(menu.label))
                        ? button_disabled
                        : button_active
                    }`}
                    type="button"
                    onClick={() => {
                      on_menu_click?.(menu.label, child);
                      set_open_menu(null);
                    }}
                    disabled={
                      (is_menu_disabled(menu.label))
                    }
                  >
                    {child}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        <AlgorithmMenu algorithm={algorithm} on_algorithm_change={on_algorithm_change}
          disabled={is_connected || is_loading} is_open={open_menu === menu_items.length}
          on_open={() => set_open_menu(menu_items.length)} on_close={() => set_open_menu(null)} />
      </div>
      <div className="flex items-center">
        {is_connected && (
          <>
            <div className="flex items-center mr-3">
              <span className="px-3 py-1 text-xs text-white rounded-full bg-gray-07">
                Live simulation
              </span>
              <button aria-label={is_running ? "Pause simulation" : "Play simulation"}
                className="px-3 py-1 flex items-center hover:cursor-pointer"
                onClick={() => {
                  if (is_running) on_pause_simulation?.(); else on_run_simulation?.();
                }}
              >
                {is_running ? (
                  <ArrowPathIcon className="w-5 h-5 text-green-500 animate-spin hover:text-green-800" />
                ) : (
                  <PlayIcon className="w-5 h-5 text-green-700 hover:text-green-500" />
                )}
              </button>
              <button aria-label="Stop simulation"
                className="py-1 disabled:opacity-30 flex items-center hover:cursor-pointer"
                onClick={() => {
                  on_stop_simulation?.();
                }}
              >
                <PowerIcon className="w-5 h-5 text-red-500 hover:text-red-700" />
              </button>
            </div>
          </>
        )}
        {is_loading && (
          <div className="flex px-3 items-center justify-center text-white/70 animate-pulse">
            <span className="mr-2">Starting...</span>
            <SpinnerWidget className={"w-4 h-4 border-2 border-white"} />{" "}
          </div>
        )}
      </div>
    </div>
  );
};

export default MenuBar;
