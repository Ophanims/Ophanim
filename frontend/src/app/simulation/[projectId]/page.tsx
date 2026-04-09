"use client";

import { useParams } from "next/navigation";
import { useSimulationController } from "./simulation.controller";
import SimulationView from "./simulation.view";

export default function SimulationPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const controller = useSimulationController({ projectId });

  return (
    <SimulationView
      projectId={projectId}
      status={controller.status}
      tickCount={controller.tickCount}
      maxSlot={controller.maxSlot}
      error={controller.error}
      satellites={controller.satellites}
      stations={controller.stations}
      onPlay={controller.play}
      onPause={controller.pause}
      onStop={controller.stop}
    />
  );
}
