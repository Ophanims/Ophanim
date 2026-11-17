"use client";
import { Project } from "@/features/simulation/types";
import { BlurUpdateInput } from "../../../components/BlurUpdateInput";


interface ProjectDetailsProps {
  form: Project;
  update_field: (path: string[], value: unknown) => void;
}

export const ProjectDetails = ({ form, update_field }: ProjectDetailsProps) => {
  return (
    <div className="mt-4 mb-8 mx-20">
      <div className="mb-2">
        <span className="text-xl">Basic</span>
      </div>

      {/* Title */}
      <div className="mb-4">
        <label className="block mb-1 text-xs">Title {form.project_id && `(ID: ${form.project_id})`}</label>
        <BlurUpdateInput
          value={form.title}
          on_save={(val) => update_field(["title"], val)}
        />
      </div>

      {/* Description */}
      <div className="mb-4">
        <label className="block mb-1 text-xs">Description</label>
        <textarea
          rows={3}
          defaultValue={form.description}
          onBlur={(e) =>
            update_field(["description"], e.target.value || undefined)
          }
          className="w-full rounded bg-white/20 px-3 py-2 text-white resize-none focus:outline-none focus:ring-2 focus:ring-gray-300"
          placeholder="Enter project description"
        />
      </div>
    </div>
  );
};
