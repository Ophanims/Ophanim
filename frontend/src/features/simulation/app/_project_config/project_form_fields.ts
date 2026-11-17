/** Presentation labels and paths; validation constraints come from the generated schema. */
export interface ProjectFormField {
  label: string;
  path: readonly string[];
  type?: "text" | "datetime-local";
}
export interface ProjectFormSection {
  title: string;
  fields: ProjectFormField[];
}
function fields(group: string, definitions: Array<[string, string]>): ProjectFormField[] {
  return definitions.map(([field, label]) => ({ label, path: [group, field] }));
}

export const PROJECT_FORM_SECTIONS: ProjectFormSection[] = [
  { title: "Simulation Parameters", fields: [
    { label: "Time Slot (s)", path: ["experiment", "time_slot"] },
    { label: "Seed", path: ["seed"] },
    { label: "Start Time", path: ["experiment", "start_time"], type: "datetime-local" },
    { label: "End Time", path: ["experiment", "end_time"], type: "datetime-local" },
  ] },
  { title: "Orbital Parameters", fields: [
    { label: "Constellation Name", path: ["constellation", "name"], type: "text" },
    ...fields("constellation", [
      ["altitude", "Altitude (m)"], ["inclination", "Inclination (deg)"],
      ["number_of_planes", "Number of Planes"], ["number_of_sat_per_planes", "Satellites per Plane"],
      ["phase_factor", "Phase Factor"],
    ]),
  ] },
  { title: "Observation Parameters", fields: fields("hardware", [
    ["width_px", "Imagery Width (px)"], ["length_px", "Imagery Height (px)"],
    ["focal_length_mm", "Camera Focal Length (mm)"], ["px_size_width", "Pixel Width (μm)"],
    ["px_size_length", "Pixel Length (μm)"], ["channels_per_pixel", "Channels per Pixel"],
    ["bits_per_channel", "Bits per Channel"],
  ]) },
  { title: "Computation Parameters", fields: fields("resources", [
    ["processor_core_count", "Processor Cores"], ["computation_energy_factor", "Computation Energy Factor"],
    ["max_concurrent_computations", "Maximum Concurrent Computations"], ["max_clock_frequency_ghz", "Maximum Clock Frequency (GHz)"],
  ]) },
  { title: "Communication Parameters", fields: [
    ...(["isl", "uplink", "downlink"] as const).flatMap((direction) => fields("hardware", [
      [`${direction}_frequency_hz`, `${direction.toUpperCase()} Frequency (Hz)`],
      [`${direction}_bandwidth_hz`, `${direction.toUpperCase()} Bandwidth (Hz)`],
      [`${direction}_tx_power_w`, `${direction.toUpperCase()} TX Power (W)`],
      [`${direction}_gain_tx_dbi`, `${direction.toUpperCase()} TX Gain (dBi)`],
      [`${direction}_gain_rx_dbi`, `${direction.toUpperCase()} RX Gain (dBi)`],
      [`${direction}_noise_temp_k`, `${direction.toUpperCase()} Noise Temperature (K)`],
    ])),
    ...fields("resources", [
      ["transmission_energy_factor", "Transmission Energy Factor"],
      ["spectral_efficiency", "Spectral Efficiency"], ["max_concurrent_transmissions", "Maximum Concurrent Transmissions"],
    ]),
  ] },
  { title: "Energy Parameters", fields: fields("resources", [
    ["battery_capacity_wh", "Battery Capacity (Wh)"], ["solar_panel_area_m2", "Solar Panel Area (m²)"],
    ["solar_panel_efficiency", "Solar Panel Efficiency"], ["amplifier_efficiency", "Power Amplifier Efficiency"],
    ["static_processing_power_w", "Static Processing Power (W)"], ["static_isl_power_w", "Static ISL Power (W)"],
    ["static_uplink_power_w", "Static Uplink Power (W)"], ["static_downlink_power_w", "Static Downlink Power (W)"],
    ["static_other_power_w", "Other Static Power (W)"],
  ]) },
];
