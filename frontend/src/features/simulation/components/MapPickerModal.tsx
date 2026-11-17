"use client";
import { CheckIcon,XMarkIcon } from "@heroicons/react/24/outline";
import "leaflet/dist/leaflet.css";
import dynamic from "next/dynamic";
import { useState } from "react";
import { createRoot } from "react-dom/client";
import { useMapEvents } from "react-leaflet"; // Static import for hook
import { LatLon } from "../types";

// Dynamically import react-leaflet components to avoid SSR
const MapContainer = dynamic(() => import("react-leaflet").then((mod) => mod.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then((mod) => mod.TileLayer), { ssr: false });
const Marker = dynamic(() => import("react-leaflet").then((mod) => mod.Marker), { ssr: false });

// Component to handle map click events
function MapClickHandler({ on_location_select }: { on_location_select: (latlon: LatLon) => void }) {
  useMapEvents({
    click(e) {
      on_location_select({ lat: e.latlng.lat, lon: ((e.latlng.lng + 180) % 360 + 360) % 360 - 180 });
    },
  });
  return null;
}

// Map Picker Modal Component
interface MapPickerModalProps {
  visible: boolean;
  on_confirm: (latlon: LatLon | null) => void;
  on_cancel: () => void;
}

const MapPickerModal = ({ visible, on_confirm, on_cancel }: MapPickerModalProps) => {
  const [selected_location, set_selected_location] = useState<LatLon | null>(null);

  if (!visible) return null;

  return (
    <>
      <div
        onClick={on_cancel}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
      />
      <div className="fixed inset-0 flex justify-center items-center z-50 p-6">
        <div className="bg-gray-800 rounded-lg w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6 text-white shadow-lg border border-gray-700">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold text-white">Select Location</h3>
            <button onClick={on_cancel} title="Close" className="hover:text-gray-300">
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>
          <div className="h-96 mb-4">
            <MapContainer
              center={[0, 0]}
              zoom={2}
              style={{ height: "100%", width: "100%", borderRadius: "0.5rem" }}
              className="border border-gray-600"
              attributionControl={true}
            >
              <TileLayer
                url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>'
              />
              <MapClickHandler on_location_select={set_selected_location} />
              {selected_location && (
                <Marker position={[selected_location.lat, selected_location.lon]} />
              )}
            </MapContainer>
          </div>
          {selected_location && (
            <p className="mb-4 text-gray-300">
              Selected: Lat <span className="font-semibold text-white">{selected_location.lat.toFixed(4)}</span>°, 
              Lon <span className="font-semibold text-white">{selected_location.lon.toFixed(4)}</span>°, 

            </p>
          )}
          <div className="flex justify-end gap-3">
            <button
              onClick={on_cancel}
              className="px-4 py-2 bg-gray-600 rounded hover:bg-gray-500 text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => on_confirm(selected_location)}
              className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-200 flex items-center gap-1 text-gray-900 transition-colors"
            >
              <CheckIcon className="w-5 h-5" />
              Confirm
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

// Function to open the map picker and return selected coordinates
export function open_map_picker(): Promise<LatLon | null> {
  return new Promise((resolve) => {
    // Ensure DOM is ready
    if (typeof window === "undefined") {
      resolve(null);
      return;
    }

    const modal_container = document.createElement("div");
    document.body.appendChild(modal_container);

    const root = createRoot(modal_container);

    const handle_confirm = (latlon: LatLon | null) => {
      root.unmount();
      modal_container.remove();
      resolve(latlon);
    };

    const handle_cancel = () => {
      root.unmount();
      modal_container.remove();
      resolve(null);
    };

    root.render(
      <MapPickerModal
        visible={true}
        on_confirm={handle_confirm}
        on_cancel={handle_cancel}
      />
    );
  });
}
