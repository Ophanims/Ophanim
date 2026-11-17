import { useEffect,useState } from "react";
import { cancel_job,get_job } from "../communication/cache";
import type { JobSnapshot } from "../contracts/generated";

export default function JobPanel({ job, on_change }: { job: JobSnapshot; on_change: (job: JobSnapshot) => void }) {
  const [error, set_error] = useState("");
  useEffect(() => {
    if (job.status !== "running") return;
    let active = true;
    const interval = setInterval(() => {
      get_job(job.job_id).then((result) => { if (active) on_change(result); })
        .catch((error: Error) => { if (active) set_error(error.message); });
    }, 1500);
    return () => { active = false; clearInterval(interval); };
  }, [job.job_id, job.status, on_change]);
  return <div className="flex gap-4 px-4 py-2 text-xs text-white/70">
    <span>{job.job_type} · {job.status} · {job.job_id}</span>
    {job.status === "running" && <button onClick={() => {
      cancel_job(job.job_id).then(on_change).catch((error: Error) => set_error(error.message));
    }}>Cancel job</button>}
    {error && <span role="alert" className="text-red-300">{error}</span>}
  </div>;
}
