import { validate_contract } from "../communication/contract_validation";
import template from "../contracts/default_project.json";
import type { Project } from "../contracts/generated";

export function create_initial_project(): Project {
  const project = validate_contract<Project>(structuredClone(template), "Project");
  const now = new Date();
  project.experiment.start_time = now.toISOString();
  project.experiment.end_time = new Date(now.getTime() + 7200_000).toISOString();
  return project;
}
