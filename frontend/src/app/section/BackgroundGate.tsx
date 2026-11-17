"use client";
import { useCallback, useState, type ReactNode } from "react";
import { useProgress } from "@react-three/drei";
import ApplicationLoading from "./ApplicationLoading";
import BackgroundBoundary from "./BackgroundBoundary";
import EarthBackdrop from "./EarthBackdrop";
import { clear_earth_textures } from "./earthbg";

type BackgroundState = { status: "loading" | "ready" | "failed"; error: string };

export default function BackgroundGate({ children }: { children: ReactNode }) {
  const [background, set_background] = useState<BackgroundState>({ status: "loading", error: "" });
  const [attempt, set_attempt] = useState(0);
  const progress = useProgress((state) => state.progress);
  const is_ready = background.status === "ready";
  const on_ready = useCallback(() => {
    set_background((previous) => previous.status === "failed" ? previous : { status: "ready", error: "" });
  }, []);
  const on_error = useCallback((error: string) => set_background({ status: "failed", error }), []);
  const retry_background = () => {
    clear_earth_textures();
    set_background({ status: "loading", error: "" });
    set_attempt((previous) => previous + 1);
  };

  return <main aria-busy={!is_ready} className="relative h-full min-h-[32rem] w-full overflow-auto bg-black text-white">
    <BackgroundBoundary key={attempt} on_error={on_error}>
      <EarthBackdrop on_ready={on_ready} on_error={on_error} />
    </BackgroundBoundary>
    <div inert={!is_ready} aria-hidden={!is_ready} className={`relative h-full ${is_ready ? "" : "invisible"}`}>
      {children}
    </div>
    {!is_ready && <ApplicationLoading progress={Math.min(100, Math.max(0, progress))}
      error={background.error} on_retry={retry_background} />}
  </main>;
}
