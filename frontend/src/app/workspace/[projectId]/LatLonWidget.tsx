"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import { Group } from "three";

const DEFAULT_ROTATION_Y = Math.PI;

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
};

export default function LatLonWidget({ visible, radius, rotationSpeed = 0.0012 }: LatLonWidgetProps) {
  const groupRef = useRef<Group>(null);

  const lines = useMemo(() => {
    if (!visible) return [] as LatLonLineSpec[];

    const groupLines: LatLonLineSpec[] = [];
    const lineRadius = radius * 1.02;
    const segments = 256;

    for (let lat = -90; lat <= 90; lat += 10) {
      const isEquator = lat === 0;
      groupLines.push({
        points: createLatitudeLine(lineRadius, lat, segments),
        color: isEquator ? "#ffffff" : "#2b2b2b",
        lineWidth: isEquator ? 2 : 1,
        opacity: isEquator ? 0.75 : 0.45,
      });
    }

    for (let lon = -180; lon <= 180; lon += 10) {
      groupLines.push({
        points: createLongitudeLine(lineRadius, lon, segments),
        color: "#2b2b2b",
        lineWidth: 1,
        opacity: 0.45,
      });
    }

    return groupLines;
  }, [radius, visible]);

  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y += rotationSpeed;
      groupRef.current.rotation.y %= Math.PI * 2;
    }
  });

  if (!visible) return null;

  return (
    <group ref={groupRef} rotation={[0, DEFAULT_ROTATION_Y, 0]} renderOrder={3}>
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
    </group>
  );
}
