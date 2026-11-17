import VoidPage from "../../components/VoidPage";
import { useFrames } from "../workspace/useFramesContext";

export default function ParameterPanel() {
  const { frames, selected_frame_index } = useFrames();
  const frame = frames[selected_frame_index];
  if (!frame) return <VoidPage />;
  return <div className="h-full overflow-auto bg-black p-6 text-sm text-white">
    <h2 className="mb-4 text-lg">Snapshot parameters · {frame.time}</h2>
    <h3>Satellites</h3>
    <table className="my-4 w-full text-left"><thead><tr><th>id</th><th>battery_percent</th><th>processor_clock_frequency_ghz</th><th>task_queue</th><th>is_processing</th><th>is_charging</th></tr></thead>
      <tbody>{frame.satellites.map((satellite) => <tr key={satellite.id}>
        <td>{satellite.id}</td><td>{satellite.battery_percent.toFixed(2)}%</td>
        <td>{satellite.processor_clock_frequency_ghz?.toFixed(2) ?? "—"}</td><td>{satellite.task_queue}/{satellite.max_task_queue}</td>
        <td>{String(satellite.is_processing)}</td><td>{String(satellite.is_charging)}</td>
      </tr>)}</tbody></table>
    <h3>Physical missions</h3>
    <table className="my-4 w-full text-left"><thead><tr><th>id</th><th>status</th><th>position</th><th>inference_layer</th><th>data_size</th></tr></thead>
      <tbody>{frame.missions.map((mission) => <tr key={mission.id}><td>{mission.id}</td><td>{mission.status}</td><td>{mission.position}</td><td>{mission.inference_layer}</td><td>{mission.data_size.toFixed(2)}</td></tr>)}</tbody></table>
    <h3>Stations</h3>
    <table className="my-4 w-full text-left"><thead><tr><th>id</th><th>lat</th><th>lon</th><th>on_upload</th><th>on_download</th></tr></thead>
      <tbody>{frame.stations.map((station) => <tr key={station.id}><td>{station.id}</td>
        <td>{station.loc.lat}</td><td>{station.loc.lon}</td>
        <td>{String(station.on_upload)}</td><td>{String(station.on_download)}</td></tr>)}</tbody></table>
    <h3>Links</h3><pre className="mt-4 whitespace-pre-wrap">{JSON.stringify(frame.links, null, 2)}</pre>
  </div>;
}
