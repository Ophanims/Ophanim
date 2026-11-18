"use client";
import { divIcon } from "leaflet";
import { Marker } from "react-leaflet";
import type { LatLon } from "../contracts/generated";

const LOCATION_ICON = divIcon({
  className: "ground-station-location-marker",
  html: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="32" viewBox="0 0 24 32"><path d="M12 31S1 19 1 12a11 11 0 0 1 22 0c0 7-11 19-11 19Z" fill="#111827" stroke="white" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="white"/></svg>',
  iconSize: [24, 32],
  iconAnchor: [12, 32],
});

export default function LocationMarker({ location }: { location: LatLon }) {
  return <Marker position={[location.lat, location.lon]} icon={LOCATION_ICON}
    title="Selected location" alt="Selected location" interactive={false} keyboard={false} />;
}
