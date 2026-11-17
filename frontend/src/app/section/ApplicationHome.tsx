"use client";
import dynamic from "next/dynamic";
import { useSyncExternalStore } from "react";
import { ArrowRightIcon } from "@heroicons/react/24/outline";
import BrandIntroduction from "./BrandIntroduction";
import BackgroundGate from "./BackgroundGate";
import HomeViewTransition from "./HomeViewTransition";

const DashboardLoader = dynamic(() => import("@/features/simulation/app/dashboard/loader"), {
  ssr: false, loading: () => <div role="status" aria-label="Loading projects" aria-busy="true" className="flex min-h-32 items-center justify-center">
    <span aria-hidden="true" className="h-6 w-6 animate-spin rounded-full border border-white/20 border-t-white" />
  </div>,
});

function subscribe_view(on_change: () => void) {
  window.addEventListener("hashchange", on_change);
  return () => window.removeEventListener("hashchange", on_change);
}
function get_projects_view() { return window.location.hash === "#projects"; }
function get_initial_view() { return false; }

export default function ApplicationHome() {
  const show_projects = useSyncExternalStore(subscribe_view, get_projects_view, get_initial_view);
  return <BackgroundGate>
    <HomeViewTransition show_projects={show_projects}>{(displayed_projects) =>
    <div className="relative mx-auto flex min-h-full max-w-6xl items-center px-6 py-14 sm:px-12 lg:px-16">
      <div className="grid w-full gap-10 md:grid-cols-2 md:gap-0">
        <div>
          <BrandIntroduction title_id="home-title" />
          {!displayed_projects && <button type="button" aria-controls="project-browser" aria-expanded={false}
            onClick={() => { window.location.hash = "projects"; }}
            className="mt-8 inline-flex items-center gap-3 rounded-md border border-white/50 bg-black/10 px-5 py-2.5 text-sm font-medium transition hover:bg-white hover:text-black focus-visible:outline-2 focus-visible:outline-offset-4">
            Get Started<ArrowRightIcon className="h-4 w-4" />
          </button>}
        </div>
        {displayed_projects && <section id="project-browser" aria-label="Project management"
          className="min-w-0 border-t border-white/40 pt-8 md:border-t-0 md:border-l md:pl-12 md:pt-0 lg:pl-16">
          <DashboardLoader />
        </section>}
      </div>
    </div>}
    </HomeViewTransition>
  </BackgroundGate>;
}
