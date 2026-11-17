"use client";
import { useLayoutEffect, useRef, useState, type ReactNode } from "react";

/** Fade the outgoing content before changing layout; keep the background mounted. */
export default function HomeViewTransition({ show_projects, children }: {
  show_projects: boolean;
  children: (displayed_projects: boolean) => ReactNode;
}) {
  const [displayed_projects, set_displayed_projects] = useState(show_projects);
  const content_ref = useRef<HTMLDivElement>(null);
  const is_exiting = displayed_projects !== show_projects;

  useLayoutEffect(() => {
    const content = content_ref.current;
    if (!content) return;
    const reduced_motion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let is_active = true;
    const animation = content.animate(
      is_exiting ? [{ opacity: 1 }, { opacity: 0 }] : [{ opacity: 0 }, { opacity: 1 }],
      { duration: reduced_motion ? 0 : is_exiting ? 180 : 240, easing: "ease-in-out", fill: "both" },
    );
    if (is_exiting) {
      animation.finished.then(() => {
        if (is_active) set_displayed_projects(show_projects);
      }).catch(() => { /* Cancellation keeps rapid navigation on the latest requested view. */ });
    }
    return () => { is_active = false; animation.cancel(); };
  }, [show_projects, is_exiting]);

  return <div ref={content_ref} inert={is_exiting} aria-hidden={is_exiting} className="h-full">
    {children(displayed_projects)}
  </div>;
}
