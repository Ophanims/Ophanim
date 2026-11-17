export enum LayerMode {
  SOLID_MESH = "Solid/Mesh",
  WIREFRAME = "Wireframe",
  MATERIAL = "Material"
}

export interface ElementDisplaySettings {
  show_constellation: boolean;
  show_orbit: boolean;
  show_isl: boolean;
  show_ground_station: boolean;
  show_sgl: boolean;
  show_roi: boolean;
  show_swath: boolean;
}