import type { Project,SimulationSnapshot } from "../../contracts/generated";
import React,{ createContext,useContext,useLayoutEffect } from "react";
import { useRealtimeFrames } from "./useRealtimeFrames";

export const RealtimeFramesContext = createContext<ReturnType<typeof useRealtimeFrames> | null>(null);

export function RealtimeFramesProvider({ children, initial_algorithm, session_key, initial_frames }: {
  children: React.ReactNode; initial_algorithm: Project["algorithm"]; session_key: string; initial_frames?: SimulationSnapshot[];
}) {
  const value = useRealtimeFrames(initial_algorithm, initial_frames);
  const { reset_session } = value;
  useLayoutEffect(() => {
    reset_session(initial_algorithm, initial_frames);
  }, [session_key, initial_algorithm, initial_frames, reset_session]);
  return (
    <RealtimeFramesContext.Provider value={value}>
      {children}
    </RealtimeFramesContext.Provider>
  );
}

export function useFrames() {
    const ctx = useContext(RealtimeFramesContext);
    if (!ctx) throw new Error("useRealtimeFramesGlobal must be used within RealtimeFramesProvider");
    return ctx;
}
