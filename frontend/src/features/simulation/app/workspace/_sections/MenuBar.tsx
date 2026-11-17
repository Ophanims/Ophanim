import { SpinnerWidget } from "@/features/simulation/components/SpinnerWidget";
import { Project } from "@/features/simulation/types";
import {
ArrowPathIcon,
PlayIcon,
PowerIcon
} from "@heroicons/react/24/outline";
import { useEffect,useState } from "react";
import { check_cache,get_cache_size } from "../../../communication/cache";

type MenuItem = {
  label: string;
  children: string[];
};

type MenuBarProps = {
  className?: string;
  project: Project;
  disabled: boolean;
  is_connected: boolean;
  is_running: boolean;
  is_loading: boolean;
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
      "Initialization",
      "Train Model",
      "Launch Simulation",
      "Shutdown",
      "Auto Testing",
      "Clear Datasets",
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
  project,
  disabled, is_connected, is_running,
  is_loading,
  on_menu_click,
  on_run_simulation,
  on_pause_simulation,
  on_stop_simulation,
}: MenuBarProps) => {
  const [open_menu, set_open_menu] = useState<number | null>(null);


  const [cache_size, set_cache_size] = useState<number>(0);
  const [cache_integrity, set_cache_integrity] = useState<boolean>(false);

  useEffect(() => {
    get_cache_size().then((size) => set_cache_size(size / (1024 * 1024))).catch(() => set_cache_size(0));
  }, [open_menu]);

  useEffect(() => {
    check_cache_integrity(project).then((integrity) =>
      set_cache_integrity(integrity)
    ).catch(() => set_cache_integrity(false));
  }, [open_menu, project]);

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
                disabled &&
                menu.label !== "Visualization" &&
                menu.label !== "Simulation"
                  ? button_disabled
                  : button_active
              }`}
              onMouseEnter={() => set_open_menu(idx)}
              onFocus={() => set_open_menu(idx)}
              onClick={() => set_open_menu(idx)}
              type="button"
              disabled={
                disabled &&
                menu.label !== "Visualization" &&
                menu.label !== "Simulation"
              }
            >
              {menu.label}
            </button>
            {open_menu === idx && (
              <div className="absolute w-52 left-0 top-full bg-gray-08 z-20 animate-fade-in">
                {menu.children.map((child) => (
                  <button
                    key={child}
                    className={`${child_button_base} ${
                      (disabled &&
                        menu.label !== "Visualization" &&
                        menu.label !== "Simulation")
                        ? button_disabled
                        : button_active
                    }`}
                    type="button"
                    onClick={() => {
                      on_menu_click?.(menu.label, child);
                      set_open_menu(null);
                    }}
                    disabled={
                      (disabled &&
                        menu.label !== "Visualization" &&
                        menu.label !== "Simulation")
                    }
                  >
                    {child}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="flex items-center">
        {is_connected && (
          <>
            <div className="flex items-center mr-3">
              <span className="px-3 py-1 text-xs text-white rounded-full bg-gray-07">
                Simulation Web Socket | Cache {cache_integrity ? "ready" : "cold"} | Size: {cache_size.toFixed(2)} MB
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
            <span className="mr-2">Initializing Datasets...</span>
            <SpinnerWidget className={"w-4 h-4 border-2 border-white"} />{" "}
          </div>
        )}
      </div>
    </div>
  );
};

export default MenuBar;

async function check_cache_integrity(project: Project) {
  const result = await check_cache(project);
  return Object.values(result).every(Boolean);
}
