import { validate_contract } from "../communication/contract_validation";
import type { Project } from "../contracts/generated";

export function export_project(project: Project): void {
  const data = JSON.stringify(validate_contract<Project>(project, "Project"), null, 2);
  const url = URL.createObjectURL(new Blob([data], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url; link.download = `${project.project_id || "project"}.json`; link.click();
  URL.revokeObjectURL(url);
}

export function select_project_file(): Promise<Project | null> {
  return new Promise((resolve, reject) => {
    const input = document.createElement("input");
    input.type = "file"; input.accept = ".json,application/json";
    input.oncancel = () => resolve(null);
    input.onchange = async () => {
      try {
        const file = input.files?.[0];
        resolve(file ? validate_contract<Project>(JSON.parse(await file.text()), "Project") : null);
      } catch (error) { reject(error); }
    };
    input.click();
  });
}
