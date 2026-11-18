import type { ReactNode } from "react";

export function InventorySection({ title, children }: { title: string; children: ReactNode }) {
  return <details open className="mb-4">
    <summary className="mb-2 cursor-pointer text-xs font-medium uppercase text-white">{title}</summary>
    <div className="space-y-2">{children}</div>
  </details>;
}

export function InfoItem({ label, value }: { label: string; value: string | number | boolean | null | undefined }) {
  return <div className="flex justify-between gap-2 text-xs text-white/70">
    <span>{label}</span><span className="break-all text-right">{value ?? "—"}</span>
  </div>;
}
