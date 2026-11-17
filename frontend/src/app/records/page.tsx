"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import type { RecordSnapshot } from "@/features/simulation/contracts/generated";
import { list_records, get_download_url, delete_record } from "@/features/simulation/communication/records";

export default function RecordsPage() {
  const [records, set_records] = useState<RecordSnapshot[]>([]);
  const [error, set_error] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    list_records(controller.signal).then(set_records).catch((error: Error) => {
      if (!controller.signal.aborted) set_error(error.message);
    });
    return () => controller.abort();
  }, []);
  return <div className="h-full overflow-auto p-8 text-sm">
    <h1 className="mb-6 text-xl">Simulation records</h1>
    {error && <p role="alert" className="text-red-300">{error}</p>}
    {!records.length && !error && <p>No recordings yet. Simulations are recorded automatically.</p>}
    <table className="w-full text-left"><thead><tr><th>record_id</th><th>algorithm</th><th>status</th><th>frame_count</th><th>Actions</th></tr></thead>
      <tbody>{records.map((record) => <tr key={record.record_id} className="border-b border-white/10">
        <td className="py-3">{record.record_id}</td><td>{record.algorithm}</td><td>{record.status}</td><td>{record.frame_count}</td>
        <td className="space-x-4"><Link href={`/workspace/${encodeURIComponent(record.project_id)}?record_id=${record.record_id}`}>Replay</Link>
          <a href={get_download_url(record.record_id)} download>Download</a>
          <button onClick={async () => {
            if (!window.confirm("Delete this record?")) return;
            try { await delete_record(record.record_id); set_records((previous) => previous.filter((entry) => entry.record_id !== record.record_id)); }
            catch (error) { set_error(error instanceof Error ? error.message : "Delete failed"); }
          }}>Delete</button></td>
      </tr>)}</tbody></table>
  </div>;
}
