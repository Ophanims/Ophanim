import * as THREE from "three";
export function create_latitude_line(
  radius: number,
  lat_deg: number,
  segments: number = 256,
  color: number = 0xffffff,
  opacity: number = 1
): THREE.LineLoop {
  const positions: number[] = [];
  const lat_rad = THREE.MathUtils.degToRad(lat_deg);
  const y = radius * Math.sin(lat_rad);
  const r = radius * Math.cos(lat_rad);

  for (let i = 0; i <= segments; i++) {
    const theta = (i / segments) * Math.PI * 2;
    const x = r * Math.cos(theta);
    const z = r * Math.sin(theta);
    positions.push(x, y, z);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(positions, 3)
  );

  const material = new THREE.LineBasicMaterial({
    color,
    linewidth: 2,
    transparent: opacity < 1,
    opacity,
  });

  return new THREE.LineLoop(geometry, material);
}

export function create_longitude_line(
  radius: number,
  lon_deg: number,
  segments: number = 256,
  color: number = 0xffffff,
  opacity: number = 1
): THREE.Line {
  const positions: number[] = [];
  const lon_rad = THREE.MathUtils.degToRad(lon_deg);

  for (let i = 0; i <= segments; i++) {
    const lat_rad = THREE.MathUtils.degToRad(-90 + (i / segments) * 180);
    const x = radius * Math.cos(lat_rad) * Math.cos(lon_rad);
    const y = radius * Math.sin(lat_rad);
    const z = radius * Math.cos(lat_rad) * Math.sin(lon_rad);
    positions.push(x, y, z);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(positions, 3)
  );

  const material = new THREE.LineBasicMaterial({
    color,
    linewidth: 1,
    transparent: opacity < 1,
    opacity,
  });

  return new THREE.Line(geometry, material);
}
