"use client";
import { ExperimentDetails } from "@/features/simulation/app/_project_config/_sections/ExpDetails";
import { Project } from "@/features/simulation/types";
import { useState } from "react";
import { ConstellationDetails } from "./_sections/ConstellationDetails";
import { GSDetails } from "./_sections/GSDetails";
import { HardwareDetails } from "./_sections/HardwareDetails";
import { ProjectDetails } from "./_sections/ProjectDetails";
import { ROIDetails } from "./_sections/ROIDetails";
import { ResourcesDetails } from "./_sections/ResourcesDetails";
import { useProjectConfig } from "./useProjectConfig";

interface ProjectConfigProps {
  project: Project;
  on_save: (updated: Project) => void;
}
const TABS = [
  "project",
  "constellation",
  "hardware",
  "resources",
  "entity",
  "experiment",
] as const;
export const ProjectConfig = ({ project, on_save }: ProjectConfigProps) => {
  const [active_tab, set_active_tab] = useState<(typeof TABS)[number]>("project");

  const { form, modified, loading, error, update_field, update_list_item,
    delete_list_item, add_list_item, select_location, handle_submit } = useProjectConfig(project, on_save);

  return (
    <div className="h-full w-full px-4 py-12 text-white bg-gray-09">
      <div className="flex justify-between mb-4 border-b border-white/20">
        <nav className="flex gap-4 text-white">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => set_active_tab(tab)}
              className={`px-4 py-2 transition-colors hover:cursor-pointer ${
                active_tab === tab
                  ? "border-b-2 border-white font-semibold"
                  : "text-white/70 hover:text-white"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>

        <button
          disabled={!modified || loading}
          onClick={handle_submit}
          className={`mx-3 px-6 my-1  ${
            modified ? "bg-white hover:bg-white/80" : "bg-gray-04"
          } rounded-3xl flex items-center text-black transition-colors hover:cursor-pointer`}
        >
          Save
        </button>
      </div>

      {error && <p role="alert" className="text-red-300">{error}</p>}
      {/* tab content */}
      <div className="h-full w-full px-4 overflow-y-auto">
        {active_tab === "project" && (
          <ProjectDetails form={form} update_field={update_field} />
        )}
        {active_tab === "constellation" && (
          <ConstellationDetails
            constellation={form.constellation}
            update_field={update_field}
          />
        )}
        {active_tab === "hardware" && (
          <HardwareDetails hardware={form.hardware} update_field={update_field} />
        )}
        {active_tab === "resources" && <ResourcesDetails resources={form.resources} update_field={update_field} />}
        {active_tab === "entity" && (
          <div className="space-y-4 mt-4 mb-8 mx-20">
            <div className="mb-2">
              <span className="text-xl">Entities</span>
            </div>
            <GSDetails
              ground_stations={form.ground_stations}
              update_list_item={update_list_item}
              add_list_item={add_list_item}
              delete_list_item={delete_list_item}
              select_location={select_location}
            />
            <ROIDetails
              rois={form.rois}
              update_list_item={update_list_item}
              add_list_item={add_list_item}
              delete_list_item={delete_list_item}
              select_location={select_location}
            />
            {/* <SatDetails satellites={form.satellites} /> */}
          </div>
        )}
        {active_tab === "experiment" && (
          <ExperimentDetails
            experiment={form.experiment}
            ground_stations={form.ground_stations}
            rois={form.rois}
            add_list_item={add_list_item}
            update_field={update_field}
            delete_list_item={delete_list_item}
            update_list_item={update_list_item}
          />
        )}
      </div>
    </div>
  );
};
