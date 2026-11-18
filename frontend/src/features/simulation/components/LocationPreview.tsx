"use client";
import { useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { LatLon } from "../contracts/generated";
import LocationMarker from "./LocationMarker";

function PreviewCenter({ location }: { location: LatLon }) {
  const map = useMap();
  useEffect(() => {
    map.setView([location.lat, location.lon], map.getZoom(), { animate: false });
    map.invalidateSize();
  }, [map, location.lat, location.lon]);
  return null;
}

export default function LocationPreview({ location }: { location: LatLon }) {
  return <div role="img" aria-label="Ground station map preview" className="h-40 overflow-hidden rounded-md border border-white/25">
    <MapContainer center={[location.lat, location.lon]} zoom={6} className="h-full w-full"
      dragging={false} zoomControl={false} scrollWheelZoom={false} doubleClickZoom={false}
      touchZoom={false} boxZoom={false} keyboard={false}>
      <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />
      <PreviewCenter location={location} />
      <LocationMarker location={location} />
    </MapContainer>
  </div>;
}
