"use client";

import { useMemo } from "react";
import { Line } from "@react-three/drei";

const DEFAULT_ROTATION_Y = Math.PI;
const INITIAL_ROTATION_OFFSET_Y = 0.06;
// const AXIAL_TILT_RAD = (23.44 * Math.PI) / 180;

type LatLonLineSpec = {
  points: Array<[number, number, number]>;
  color: string;
  lineWidth?: number;
  opacity: number;
};

function createLatitudeLine(radius: number, latitudeDeg: number, segments: number) {
  const points: Array<[number, number, number]> = [];
  const latitudeRad = (latitudeDeg * Math.PI) / 180;
  const sinLat = Math.sin(latitudeRad);
  const cosLat = Math.cos(latitudeRad);

  for (let index = 0; index <= segments; index += 1) {
    const lon = (index / segments) * Math.PI * 2;
    const x = radius * cosLat * Math.cos(lon);
    const y = radius * sinLat;
    const z = radius * cosLat * Math.sin(lon);
    points.push([x, y, z]);
  }

  return points;
}

function createLongitudeLine(radius: number, longitudeDeg: number, segments: number) {
  const points: Array<[number, number, number]> = [];
  const longitudeRad = (longitudeDeg * Math.PI) / 180;
  const sinLon = Math.sin(longitudeRad);
  const cosLon = Math.cos(longitudeRad);

  for (let index = 0; index <= segments; index += 1) {
    const lat = -Math.PI / 2 + (index / segments) * Math.PI;
    const cosLat = Math.cos(lat);
    const x = radius * cosLat * cosLon;
    const y = radius * Math.sin(lat);
    const z = radius * cosLat * sinLon;
    points.push([x, y, z]);
  }

  return points;
}

type LatLonWidgetProps = {
  visible: boolean;
  radius: number;
  rotationSpeed?: number;
  slotCount?: number;
};

export default function LatLonWidget({ visible, radius, rotationSpeed = 0.004178074, slotCount = 0 }: LatLonWidgetProps) {

  const lines = useMemo(() => {
    if (!visible) return [] as LatLonLineSpec[];

    const groupLines: LatLonLineSpec[] = [];
    const lineRadius = radius * 1.02;
    const segments = 256;

    for (let lat = -90; lat <= 90; lat += 10) {
      const isEquator = lat === 0;
      groupLines.push({
        points: createLatitudeLine(lineRadius, lat, segments),
        color: isEquator ? "#ffffff" : "#eeeeee",
        lineWidth: isEquator ? 2 : 1,
        opacity: isEquator ? 0.75 : 0.45,
      });
    }

    for (let lon = -180; lon <= 180; lon += 10) {
      groupLines.push({
        points: createLongitudeLine(lineRadius, lon, segments),
        color: "#eeeeee",
        lineWidth: 1,
        opacity: 0.45,
      });
    }

    return groupLines;
  }, [radius, visible]);

  if (!visible) return null;

  const twoPi = Math.PI * 2;
  const safeSlotCount = Number.isFinite(slotCount) ? slotCount : 0;
  const rotationY = (DEFAULT_ROTATION_Y + INITIAL_ROTATION_OFFSET_Y + safeSlotCount * ((rotationSpeed * Math.PI) / 180)) % twoPi;

  return (
    <group rotation={[0, rotationY, 0]}>
      {/* <group rotation={[AXIAL_TILT_RAD, 0, 0]} renderOrder={3}> */}
        {lines.map((line, index) => (
          <Line
            key={index}
            points={line.points}
            color={line.color}
            lineWidth={line.lineWidth}
            transparent
            opacity={line.opacity}
            depthWrite={false}
            depthTest
          />
        ))}
      {/* </group> */}
    </group>
  );
}
