import Earth from "./earthbg";

export default function EarthBackdrop({ on_ready, on_error }: { on_ready: () => void; on_error: (error: string) => void }) {
  return <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
    <Earth is_full={false} on_ready={on_ready} on_error={on_error} />
    <div className="absolute inset-0 bg-linear-to-r from-black/10 via-black/30 to-black/65" />
  </div>;
}
