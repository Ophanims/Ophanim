"use client";
import CameraVisualizer from "@/features/simulation/components/CameraVisualizer";
import { Hardware } from "@/features/simulation/types";
import { BlurUpdateInput } from "../../../components/BlurUpdateInput";

interface HardwareDetailsProps {
  hardware: Hardware;
  update_field: (path: string[], value: unknown) => void;
}

export const HardwareDetails = ({
  hardware,
  update_field,
}: HardwareDetailsProps) => {
  const render_input = (
    label: string,
    path: string[],
    value: number | null | undefined,
    min?: number,
    max?: number
  ) => (
    <div className="mb-2">
      <label className="block mb-1 text-xs">{label}</label>
      <BlurUpdateInput
        type="number" min={min} max={max}
        value={value ?? ""}
        on_save={(val) => update_field(path, isNaN(val) ? undefined : val)}
      />
    </div>
  );

  return (
    <div className="mt-4 mb-8 mx-20">
      {/* Imagery */}
      <div className="mb-2 text-xl">Imagery</div>
      <div className="flex">
        <div className="w-2/3">
          {render_input(
            "Channels per Pixel",
            ["hardware", "channels_per_pixel"],
            hardware.channels_per_pixel
          )}
          {render_input(
            "Bits per Channel",
            ["hardware", "bits_per_channel"],
            hardware.bits_per_channel
          )}
          {render_input(
            "Focal Length (mm)",
            ["hardware", "focal_length_mm"],
            hardware.focal_length_mm
          )}
          {render_input("Width (px)", ["hardware", "width_px"], hardware.width_px)}
          {render_input(
            "Length (px)",
            ["hardware", "length_px"],
            hardware.length_px
          )}
          {render_input("Pixel Length (μm)", ["hardware", "px_size_length"], hardware.px_size_length)}
          {render_input(
            "Pixel Width (μm)",
            ["hardware", "px_size_width"],
            hardware.px_size_width
          )}
        </div>
        <div className="w-1/3 flex items-center justify-center">
          <CameraVisualizer
            focal_length_mm={hardware.focal_length_mm}
            width_px={hardware.width_px}
            length_px={hardware.length_px}
          />
        </div>
      </div>

      {/* Uplink */}
      <div className="mt-8 mb-2 text-xl">Uplink</div>
      {render_input(
        "Uplink Frequency (Hz)",
        ["hardware", "uplink_frequency_hz"],
        hardware.uplink_frequency_hz
      )}
      {render_input(
        "Uplink Bandwidth (Hz)",
        ["hardware", "uplink_bandwidth_hz"],
        hardware.uplink_bandwidth_hz
      )}
      {render_input(
        "Uplink TX Power (W)",
        ["hardware", "uplink_tx_power_w"],
        hardware.uplink_tx_power_w
      )}
      {render_input(
        "Uplink TX Gain (dBi)",
        ["hardware", "uplink_gain_tx_dbi"],
        hardware.uplink_gain_tx_dbi
      )}
      {render_input(
        "Uplink RX Gain (dBi)",
        ["hardware", "uplink_gain_rx_dbi"],
        hardware.uplink_gain_rx_dbi
      )}
      {render_input(
        "Uplink Noise Temp (K)",
        ["hardware", "uplink_noise_temp_k"],
        hardware.uplink_noise_temp_k
      )}

      {/* Downlink */}
      <div className="mt-8 mb-2 text-xl">Downlink</div>
      {render_input(
        "Downlink Frequency (Hz)",
        ["hardware", "downlink_frequency_hz"],
        hardware.downlink_frequency_hz
      )}
      {render_input(
        "Downlink Bandwidth (Hz)",
        ["hardware", "downlink_bandwidth_hz"],
        hardware.downlink_bandwidth_hz
      )}
      {render_input(
        "Downlink TX Power (W)",
        ["hardware", "downlink_tx_power_w"],
        hardware.downlink_tx_power_w
      )}
      {render_input(
        "Downlink TX Gain (dBi)",
        ["hardware", "downlink_gain_tx_dbi"],
        hardware.downlink_gain_tx_dbi
      )}
      {render_input(
        "Downlink RX Gain (dBi)",
        ["hardware", "downlink_gain_rx_dbi"],
        hardware.downlink_gain_rx_dbi
      )}
      {render_input(
        "Downlink Noise Temp (K)",
        ["hardware", "downlink_noise_temp_k"],
        hardware.downlink_noise_temp_k
      )}

      {/* ISL */}
      <div className="mt-8 mb-2 text-xl">ISL (Inter-Satellite Link)</div>
      {render_input(
        "ISL Frequency (Hz)",
        ["hardware", "isl_frequency_hz"],
        hardware.isl_frequency_hz
      )}
      {render_input(
        "ISL Bandwidth (Hz)",
        ["hardware", "isl_bandwidth_hz"],
        hardware.isl_bandwidth_hz
      )}
      {render_input(
        "ISL TX Power (W)",
        ["hardware", "isl_tx_power_w"],
        hardware.isl_tx_power_w
      )}
      {render_input(
        "ISL TX Gain (dBi)",
        ["hardware", "isl_gain_tx_dbi"],
        hardware.isl_gain_tx_dbi
      )}
      {render_input(
        "ISL RX Gain (dBi)",
        ["hardware", "isl_gain_rx_dbi"],
        hardware.isl_gain_rx_dbi
      )}
      {render_input(
        "ISL Noise Temp (K)",
        ["hardware", "isl_noise_temp_k"],
        hardware.isl_noise_temp_k
      )}
    </div>
  );
};
