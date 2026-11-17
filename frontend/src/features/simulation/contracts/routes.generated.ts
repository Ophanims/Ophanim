// Generated from backend/simulator/api.py; do not edit.
export const API_ROUTES = {
  "list_projects": "/api/projects",
  "detect_project": "/api/projects/detect",
  "save_project": "/api/projects",
  "get_project": "/api/projects/{project_id}",
  "delete_project": "/api/projects/{project_id}",
  "get_cache_size": "/api/cache/size",
  "clear_cache": "/api/cache/clear",
  "check_cache": "/api/cache/check",
  "initial_cache": "/api/cache/initial",
  "start_job": "/api/jobs/{job_type}",
  "get_job": "/api/jobs/{job_id}",
  "cancel_job": "/api/jobs/{job_id}",
  "list_records": "/api/records",
  "get_record": "/api/records/{record_id}",
  "download_record": "/api/records/{record_id}/download",
  "delete_record": "/api/records/{record_id}",
  "simulation_ws": "/api/simulation/ws"
} as const;
