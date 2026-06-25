"use client";

type SaveConfirmDialogProps = {
  open: boolean;
  onSave: () => void;
  onDiscard: () => void;
};

export default function SaveConfirmDialog({ open, onSave, onDiscard }: SaveConfirmDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="w-80 rounded-xl border bg-black/30 p-6">
        <h2 className="mb-2 text-lg font-semibold">Save Record?</h2>
        <p className="mb-6 text-sm text-white/70">
          Do you want to save the simulation timeline data?
        </p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onDiscard}
            className="rounded-lg border px-4 py-2 text-sm transition hover:bg-white/10"
          >
            Discard
          </button>
          <button
            onClick={onSave}
            className="rounded-lg bg-white px-4 py-2 text-sm text-black transition hover:bg-white/90"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
