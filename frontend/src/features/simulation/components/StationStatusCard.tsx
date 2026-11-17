import type { StationSnapshot } from "../contracts/generated";
export default function StationStatusCard({ gs }: { gs: StationSnapshot }) {
  return <div className="text-xs text-white/70">
    <div>lat: {gs.loc.lat.toFixed(4)} · lon: {gs.loc.lon.toFixed(4)}</div>
    <div>on_upload: {String(gs.on_upload)} · on_download: {String(gs.on_download)}</div>
  </div>;
}
