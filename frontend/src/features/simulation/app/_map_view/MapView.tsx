"use client";
import "leaflet/dist/leaflet.css";
import { CircleMarker,MapContainer,Polygon,Popup,TileLayer } from "react-leaflet";
import ClockWidget from "../../components/ClockWidget";
import VoidPage from "../../components/VoidPage";
import type { LatLon } from "../../contracts/generated";
import { useFrames } from "../workspace/useFramesContext";

function polygon_points(corners: LatLon[]): [number, number][] | null {
  if (corners.length < 3) return null;
  const points: [number, number][] = corners.map((corner) => [corner.lat, corner.lon]);
  // Avoid drawing across the whole map when a ring crosses the antimeridian.
  if (points.some((point, index) => Math.abs(point[1] - points[(index + 1) % points.length][1]) > 180)) return null;
  return points;
}

export default function MapViewPage() {
  const { frames, selected_frame_index } = useFrames();
  const frame = frames[selected_frame_index];
  if (!frame) return <VoidPage />;
  return <div className="relative h-full w-full bg-black text-white">
    <div className="absolute right-0 top-0 z-[500] bg-black/70">
      <ClockWidget frame_counter={frame.frame_counter} time={frame.time} />
    </div>
    <MapContainer center={[0, 0]} zoom={2} minZoom={1} className="h-full w-full">
      <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='© OpenStreetMap contributors © CARTO' />
      {frame.satellites.map((satellite) => {
        const points = polygon_points(satellite.img_corners_loc);
        return points && <Polygon key={satellite.id} positions={points} pathOptions={{ color: "#334155", weight: 1, fillOpacity: 0.2 }}><Popup>{satellite.id}</Popup></Polygon>;
      })}
      {frames.slice(0, selected_frame_index).flatMap((state, index) => state.satellites.map((satellite) => {
        const points = polygon_points(satellite.img_corners_loc);
        return points && <Polygon key={`${index}-${satellite.id}`} positions={points} pathOptions={{ color: "green", weight: 1, opacity: 0.15, fillOpacity: 0 }} />;
      }))}
      {frame.stations.map((station) => <CircleMarker key={station.id} center={[station.loc.lat, station.loc.lon]} radius={4} pathOptions={{ color: "green" }}><Popup>{station.id}</Popup></CircleMarker>)}
      {frame.rois.map((roi) => {
        const points = polygon_points(roi.corners_loc);
        return points && <Polygon key={roi.id} positions={points} pathOptions={{ color: "red", weight: 1 }}><Popup>{roi.id}</Popup></Polygon>;
      })}
    </MapContainer>
  </div>;
}
