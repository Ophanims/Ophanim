import * as THREE from "three";
export function create_latitude_line(
  radius: number,
  latitude_deg: number,
  segments: number,
  color: number | string,
  _linewidth: number
): THREE.Line<THREE.BufferGeometry, THREE.LineBasicMaterial> {
  const lat_rad = THREE.MathUtils.degToRad(latitude_deg);
  const cos_lat = Math.cos(lat_rad);
  const sin_lat = Math.sin(lat_rad);
  const points: THREE.Vector3[] = [];
  for (let i = 0; i <= segments; i++) {
    const lon = (i / segments) * Math.PI * 2;
    const x = radius * cos_lat * Math.cos(lon);
    const y = radius * sin_lat;
    const z = radius * cos_lat * Math.sin(lon);
    points.push(new THREE.Vector3(x, y, z));
  }
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineBasicMaterial({
    color, linewidth: _linewidth,
    transparent: true,
    opacity: 0.4,
  });
  return new THREE.Line(geometry, material);
}

export function create_longitude_line(
  radius: number,
  longitude_deg: number,
  segments: number,
  color: number | string,
  _linewidth: number
): THREE.Line<THREE.BufferGeometry, THREE.LineBasicMaterial> {
  const lon_rad = THREE.MathUtils.degToRad(longitude_deg);
  // Meridian lies on a plane rotated by longitude around Y-axis
  const points: THREE.Vector3[] = [];
  for (let i = 0; i <= segments; i++) {
    const t = (i / segments) * Math.PI * 2; // angle from south to north pole and back
    // Build great-circle in XZ -> rotate around Y to desired longitude
    const x = radius * Math.cos(t);
    const y = radius * Math.sin(t);
    const z = 0;
    const p = new THREE.Vector3(x, y, z);
    p.applyAxisAngle(new THREE.Vector3(0, 1, 0), lon_rad);
    points.push(p);
  }
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineBasicMaterial({
    color, linewidth: _linewidth,
    transparent: true,
    opacity: 0.4,
  });
  return new THREE.Line(geometry, material);
}
