import { useCallback,useEffect,useRef,useState,type SetStateAction } from "react";
import { SimulationSocket } from "../../communication/simulation_socket";
import type { ControlMessage,Project,SimulationSnapshot } from "../../contracts/generated";

const MAX_BUFFERED_FRAMES = 600;

export function useRealtimeFrames(initial_algorithm: Project["algorithm"], initial_frames?: SimulationSnapshot[]) {
  const [buffer, set_buffer] = useState<{ frames: SimulationSnapshot[]; selected_frame_index: number; follow_live: boolean }>({ frames: initial_frames ?? [], selected_frame_index: 0, follow_live: initial_frames === undefined });
  const { frames, selected_frame_index, follow_live } = buffer;
  const set_selected_frame_index = useCallback((update: SetStateAction<number>) => set_buffer((previous) => ({
    ...previous, selected_frame_index: Math.max(0, Math.min(typeof update === "function" ? update(previous.selected_frame_index) : update, previous.frames.length - 1)),
  })), []);
  const set_follow_live = (follow_live: boolean) => set_buffer((previous) => ({ ...previous, follow_live, selected_frame_index: follow_live ? Math.max(0, previous.frames.length - 1) : previous.selected_frame_index }));
  const [error, set_error] = useState<string | null>(null);
  const [is_loading, set_is_loading] = useState(false);
  const [is_connected, set_is_connected] = useState(false);
  const [is_running, set_is_running] = useState(false);
  const [algorithm, set_algorithm] = useState<NonNullable<ControlMessage["algorithm"]>>(initial_algorithm ?? "geometry");
  const socket_ref = useRef<SimulationSocket | null>(null);
  const generation_ref = useRef(0);
  const disconnect = useCallback(() => {
    generation_ref.current += 1;
    socket_ref.current?.close(); socket_ref.current = null;
    set_is_loading(false); set_is_connected(false); set_is_running(false);
  }, []);
  useEffect(() => () => { socket_ref.current?.close(); }, []);
  const connect = useCallback((project: Project) => {
    disconnect();
    const generation = ++generation_ref.current;
    set_is_loading(true); set_buffer({ frames: [], selected_frame_index: 0, follow_live: true }); set_error(null);
    socket_ref.current = new SimulationSocket({ action: "init", payload: project, algorithm }, {
      on_state: (state) => {
        if (generation !== generation_ref.current) return;
        set_buffer((previous) => {
          const frames = [...previous.frames, state].slice(-MAX_BUFFERED_FRAMES);
          return { ...previous, frames, selected_frame_index: previous.follow_live ? frames.length - 1 : Math.max(0, previous.selected_frame_index - (previous.frames.length === MAX_BUFFERED_FRAMES ? 1 : 0)) };
        });
        set_is_loading(false);
      },
      on_status: (status) => {
        if (generation !== generation_ref.current) return;
        set_is_connected(status !== "stopped"); set_is_running(status === "running");
        if (status === "ready") set_is_loading(false);
      },
      on_error: (message) => { if (generation === generation_ref.current) { set_error(message); set_is_loading(false); set_is_running(false); } },
      on_close: () => { if (generation === generation_ref.current) { set_is_connected(false); set_is_running(false); set_is_loading(false); } },
    });
  }, [algorithm, disconnect]);
  const load_record_frames = useCallback((frames: SimulationSnapshot[]) => {
    disconnect();
    set_buffer({ frames, selected_frame_index: 0, follow_live: false });
  }, [disconnect]);
  const reset_session = useCallback((initial_algorithm: Project["algorithm"], initial_frames?: SimulationSnapshot[]) => {
    disconnect();
    set_error(null);
    set_algorithm(initial_algorithm ?? "geometry");
    set_buffer({ frames: initial_frames ?? [], selected_frame_index: 0, follow_live: initial_frames === undefined });
  }, [disconnect]);
  const send_command = (action: "play" | "pause" | "stop") => {
    try { socket_ref.current?.send_command({ action }); }
    catch (error) { set_error(error instanceof Error ? error.message : "Command failed"); }
  };
  return { load_record_frames, reset_session, frames, selected_frame_index, follow_live, set_follow_live, set_selected_frame_index, error, is_loading, is_connected, is_running,
    algorithm, set_algorithm, connect, disconnect,
    run_simulation: () => send_command("play"), pause_simulation: () => send_command("pause"), stop_simulation: () => is_loading && !is_connected ? disconnect() : send_command("stop") };
}
