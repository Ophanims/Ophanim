import { useEffect, useRef, useState, type FormEvent } from "react";
import { createPortal } from "react-dom";
import type { GroundStation } from "../../../contracts/generated";
import { validate_contract } from "../../../communication/contract_validation";
import { open_map_picker } from "../../../components/MapPickerModal";
import LocationPreview from "../../../components/LocationPreview";

export default function GroundStationEditor({ ground_station, is_new, is_saving, on_save, on_close }: {
  ground_station: GroundStation; is_new: boolean; is_saving: boolean;
  on_save: (ground_station: GroundStation) => Promise<void>; on_close: () => void;
}) {
  const [draft, set_draft] = useState({ name: ground_station.name ?? "", lat: String(ground_station.location.lat),
    lon: String(ground_station.location.lon), altitude_m: String(ground_station.altitude_m ?? 0) });
  const [error, set_error] = useState("");
  const [show_preview, set_show_preview] = useState(!is_new);
  const lat = Number(draft.lat), lon = Number(draft.lon);
  const can_preview = show_preview && draft.lat.trim() !== "" && draft.lon.trim() !== ""
    && Number.isFinite(lat) && Number.isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180;
  const panel_ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous_focus = document.activeElement;
    panel_ref.current?.querySelector<HTMLInputElement>('input[name="name"]')?.focus();
    return () => { if (previous_focus instanceof HTMLElement && previous_focus.isConnected) previous_focus.focus(); };
  }, []);
  const submit = async (event: FormEvent) => {
    event.preventDefault(); set_error("");
    try {
      if (!draft.name.trim()) throw new Error("A station name is required.");
      const station = validate_contract<GroundStation>({ ...ground_station, name: draft.name.trim(),
        altitude_m: Number(draft.altitude_m), location: { lat: Number(draft.lat), lon: Number(draft.lon) } }, "GroundStation");
      await on_save(station);
    } catch (error) { set_error(error instanceof Error ? error.message : "Save failed"); }
  };
  const pick_location = async () => {
    try {
      const location = await open_map_picker();
      if (location) {
        set_draft((previous) => ({ ...previous, lat: String(location.lat), lon: String(location.lon) }));
        set_show_preview(true);
      }
    } catch (error) { set_error(error instanceof Error ? error.message : "Map could not open"); }
  };
  return createPortal(<div className="fixed inset-0 z-40 flex items-center justify-center bg-black/45 p-4 backdrop-blur-sm">
    <div ref={panel_ref} role="dialog" aria-modal="true" aria-label={is_new ? "Add ground station" : "Edit ground station"}
      onKeyDown={(event) => {
        if (event.key === "Escape" && !is_saving) { event.stopPropagation(); on_close(); }
        if (event.key === "Tab") {
          const controls = Array.from(panel_ref.current?.querySelectorAll<HTMLElement>('input:not(:disabled),button:not(:disabled)') ?? []);
          const target = event.shiftKey ? controls.at(-1) : controls[0];
          if (document.activeElement === (event.shiftKey ? controls[0] : controls.at(-1))) { event.preventDefault(); target?.focus(); }
        }
      }} className="max-h-[90dvh] w-full max-w-xl overflow-auto rounded-xl border border-white/30 bg-black/90 p-6 text-white shadow-2xl">
      <h2 className="mb-6 text-lg font-semibold">{is_new ? "Add Ground Station" : "Edit Ground Station"}</h2>
      <form onSubmit={submit}>
        <fieldset disabled={is_saving} className="space-y-4">
          <label className="flex flex-col gap-2 text-sm">Name
            <input name="name" required value={draft.name} onChange={(event) => set_draft({ ...draft, name: event.target.value })} className="rounded border border-white/25 bg-transparent px-3 py-2" />
          </label>
          <div className="grid grid-cols-3 gap-3">
            {([{ field: "lat", label: "Latitude (deg)", min: -90, max: 90 }, { field: "lon", label: "Longitude (deg)", min: -180, max: 180 },
              { field: "altitude_m", label: "Altitude (m)", min: undefined, max: undefined }] as const).map(({ field, label, min, max }) =>
              <label key={field} className="flex min-w-0 flex-col gap-2 text-xs sm:text-sm"><span className="min-h-8 sm:min-h-0">{label}</span>
                <input name={field} required type="number" step="any" min={min} max={max} value={draft[field]}
                  onChange={(event) => set_draft({ ...draft, [field]: event.target.value })} className="w-full min-w-0 rounded border border-white/25 bg-transparent px-2 py-2 sm:px-3" />
              </label>)}
          </div>
          <button type="button" onClick={() => void pick_location()} className="w-full rounded border border-white/25 px-3 py-2 text-sm">Pick location</button>
          {can_preview && <LocationPreview location={{ lat, lon }} />}
          {error && <p role="alert" className="text-sm text-red-200">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="submit" className="rounded bg-white px-4 py-2 text-sm font-semibold text-black">{is_saving ? "Saving…" : "Save station"}</button>
            <button type="button" onClick={on_close} className="rounded border border-white/25 px-4 py-2 text-sm">Cancel</button>
          </div>
        </fieldset>
      </form>
    </div>
  </div>, document.body);
}
