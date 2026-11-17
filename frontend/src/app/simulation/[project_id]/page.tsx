import { redirect } from "next/navigation";
export default async function LegacyPage({ params }: { params: Promise<{ project_id: string }> }) {
  const { project_id } = await params;
  redirect(`/workspace/${encodeURIComponent(project_id)}?algorithm=ophanim`);
}
