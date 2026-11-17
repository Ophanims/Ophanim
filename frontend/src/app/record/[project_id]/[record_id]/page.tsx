import { redirect } from "next/navigation";
export default async function LegacyRecordPage({ params }: { params: Promise<{ project_id: string; record_id: string }> }) {
  const { project_id, record_id } = await params;
  redirect(`/workspace/${encodeURIComponent(project_id)}?record_id=timescale_${encodeURIComponent(record_id)}`);
}
