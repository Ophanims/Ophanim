"use client";

import { useParams } from "next/navigation";
import WorkspaceView from "./workspace.view";
import { useWorkspaceController } from "./workspace.controller";
import type { ProjectPatch } from "./workspace.model";

export default function WorkspaceProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const controller = useWorkspaceController({ projectId });

  const normalizeDatetimePatch = (patch: ProjectPatch): ProjectPatch => {
    const next: ProjectPatch = { ...patch };

    const normalize = (value: unknown) => {
      if (typeof value !== "string") return value;
      if (!value.trim()) return null;
      return value.replace("T", " ");
    };

    if ("startTime" in next) next.startTime = normalize(next.startTime) as string | null | undefined;
    if ("endTime" in next) next.endTime = normalize(next.endTime) as string | null | undefined;
    return next;
  };

  const handleSaveProject = async (patch: ProjectPatch) => {
    await controller.updateProject(normalizeDatetimePatch(patch));
  };

  return (
    <WorkspaceView
      projectId={projectId}
      project={controller.project}
      satellites={controller.satellites}
      groundStations={controller.groundStations}
      records={controller.records}
      loading={controller.loading}
      saving={controller.saving}
      error={controller.error}
      onRefresh={() => {
        void controller.refresh();
      }}
      onSaveProject={(patch) => {
        void handleSaveProject(patch);
      }}
      onDeleteGroundStation={(stationId) => {
        void controller.deleteGroundStation(stationId);
      }}
      onDeleteRecord={(recordId) => {
        void controller.deleteRecord(recordId);
      }}
      onClearRecords={() => {
        void controller.clearRecords();
      }}
      onAddGroundStation={() => {
        void controller.addGroundStation();
      }}
      newStationName={controller.newStationName}
      newStationLat={controller.newStationLat}
      newStationLon={controller.newStationLon}
      newStationAlt={controller.newStationAlt}
      setNewStationName={controller.setNewStationName}
      setNewStationLat={controller.setNewStationLat}
      setNewStationLon={controller.setNewStationLon}
      setNewStationAlt={controller.setNewStationAlt}
    />
  );
}
