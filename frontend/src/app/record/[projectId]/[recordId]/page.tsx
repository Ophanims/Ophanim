"use client";

import { useParams } from "next/navigation";
import { useRecordPlaybackController } from "./record.controller";
import RecordView from "./record.view";

export default function RecordPage() {
  const { projectId, recordId } = useParams<{ projectId: string; recordId: string }>();
  const controller = useRecordPlaybackController({ recordId });

  return (
    <RecordView
      projectId={projectId}
      recordId={recordId}
      loading={controller.loading}
      buffering={controller.buffering}
      error={controller.error}
      frameSlots={controller.frameSlots}
      frameIndex={controller.frameIndex}
      satellites={controller.satellites}
      playing={controller.playing}
      hasMore={controller.hasMore}
      onTogglePlay={() => controller.setPlaying(!controller.playing)}
      onRefresh={() => {
        void controller.loadSeries();
      }}
    />
  );
}
