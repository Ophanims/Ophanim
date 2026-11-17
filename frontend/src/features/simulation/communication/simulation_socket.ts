import type { ControlMessage,SimulationSnapshot,StatusMessage } from "../contracts/generated";
import { get_websocket_url } from "./config";
import { validate_contract } from "./contract_validation";

type Callbacks = {
  on_state: (state: SimulationSnapshot) => void;
  on_status: (status: StatusMessage["status"]) => void;
  on_error: (message: string) => void;
  on_close: () => void;
};

export class SimulationSocket {
  private socket: WebSocket;
  constructor(command: ControlMessage, callbacks: Callbacks) {
    this.socket = new WebSocket(get_websocket_url());
    this.socket.onopen = () => this.send_command(command);
    this.socket.onmessage = (event) => {
      try {
        const message: unknown = JSON.parse(event.data);
        if (!message || typeof message !== "object" || !("type" in message)) throw new Error("Invalid simulation message");
        if (message.type === "state") callbacks.on_state(validate_contract<{ state: SimulationSnapshot }>(message, "StateMessage").state);
        else if (message.type === "status") callbacks.on_status(validate_contract<StatusMessage>(message, "StatusMessage").status);
        else if (message.type === "error") callbacks.on_error(validate_contract<{ message: string }>(message, "ErrorMessage").message);
        else throw new Error("Unknown simulation message type");
      } catch (error) { callbacks.on_error(error instanceof Error ? error.message : "Invalid simulation payload"); }
    };
    this.socket.onerror = () => callbacks.on_error("Simulation connection failed");
    this.socket.onclose = callbacks.on_close;
  }
  send_command(command: ControlMessage): void {
    if (this.socket.readyState !== WebSocket.OPEN) throw new Error("Simulation is not connected");
    validate_contract<ControlMessage>(command, "ControlMessage");
    this.socket.send(JSON.stringify(command));
  }
  close(): void {
    this.socket.onmessage = null;
    this.socket.onclose = null;
    this.socket.onerror = null;
    if (this.socket.readyState === WebSocket.CONNECTING) this.socket.onopen = () => this.socket.close();
    else this.socket.close();
  }
}
