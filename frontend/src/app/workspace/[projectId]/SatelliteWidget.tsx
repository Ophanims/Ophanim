"use client";

import { useEffect, useMemo } from "react";
import * as THREE from "three";
import type { SatellitePoint as SimulationSatellitePoint } from "@/app/simulation/[projectId]/simulation.model";

export type RenderSatellitePoint = Pick<SimulationSatellitePoint, "x" | "y" | "z"> & {
  id?: string;
  addr?: string;
  onSUN?: boolean;
  velocityVector?: [number, number, number] | number[];
  corX1?: number;
  corY1?: number;
  corZ1?: number;
  corX2?: number;
  corY2?: number;
  corZ2?: number;
  corX3?: number;
  corY3?: number;
  corZ3?: number;
  corX4?: number;
  corY4?: number;
  corZ4?: number;
};

type SatelliteWidgetProps = {
  satellite: RenderSatellitePoint;
  scale: number;
  showFootprint?: boolean;
};

type Vec3 = [number, number, number];

function toScenePosition(x: number, y: number, z: number, scale: number): Vec3 {
  return [x * scale, y * scale, z * scale];
}

function createTriangleGeometry(a: Vec3, b: Vec3, c: Vec3): THREE.BufferGeometry {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute([...a, ...b, ...c], 3),
  );
  geometry.setIndex([0, 1, 2]);
  geometry.computeVertexNormals();
  return geometry;
}

function createQuadGeometry(a: Vec3, b: Vec3, c: Vec3, d: Vec3): THREE.BufferGeometry {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute([...a, ...b, ...c, ...d], 3),
  );
  geometry.setIndex([0, 1, 2, 0, 2, 3]);
  geometry.computeVertexNormals();
  return geometry;
}

export default function SatelliteWidget({ satellite, scale, showFootprint = true }: SatelliteWidgetProps) {
  const bodyColor = satellite.onSUN ? "#22c55e" : "#ef4444";
  const projectionColor = "#ffffff";
  const footprintColor = "#facc15";

  const bodySize: Vec3 = [0.03, 0.03, 0.03];
  const position = toScenePosition(satellite.x, satellite.y, satellite.z, scale);

  const bodyQuaternion = useMemo(() => {
    const pos = new THREE.Vector3(...position);
    if (pos.lengthSq() < 1e-12) return new THREE.Quaternion();

    // Local +Z axis points to Earth center.
    const zAxis = pos.clone().negate().normalize();

    const velocity = new THREE.Vector3(
      Number(satellite.velocityVector?.[0] ?? 0),
      Number(satellite.velocityVector?.[1] ?? 0),
      Number(satellite.velocityVector?.[2] ?? 0),
    );

    // Use velocity projected onto the tangent plane as local +X axis.
    let xAxis = velocity.clone().sub(zAxis.clone().multiplyScalar(velocity.dot(zAxis)));
    if (xAxis.lengthSq() < 1e-12) {
      const fallback = Math.abs(zAxis.y) < 0.95
        ? new THREE.Vector3(0, 1, 0)
        : new THREE.Vector3(1, 0, 0);
      xAxis = fallback.sub(zAxis.clone().multiplyScalar(fallback.dot(zAxis)));
    }
    xAxis.normalize();

    const yAxis = new THREE.Vector3().crossVectors(zAxis, xAxis).normalize();

    const basis = new THREE.Matrix4().makeBasis(xAxis, yAxis, zAxis);
    return new THREE.Quaternion().setFromRotationMatrix(basis);
  }, [position, satellite.velocityVector]);

  const corners = useMemo<Vec3[]>(() => {
    const c1 = toScenePosition(Number(satellite.corX1), Number(satellite.corY1), Number(satellite.corZ1), scale);
    const c2 = toScenePosition(Number(satellite.corX2), Number(satellite.corY2), Number(satellite.corZ2), scale);
    const c3 = toScenePosition(Number(satellite.corX3), Number(satellite.corY3), Number(satellite.corZ3), scale);
    const c4 = toScenePosition(Number(satellite.corX4), Number(satellite.corY4), Number(satellite.corZ4), scale);

    const all = [c1, c2, c3, c4];
    return all.filter((p) => p.every((v) => Number.isFinite(v)));
  }, [
    satellite.corX1,
    satellite.corY1,
    satellite.corZ1,
    satellite.corX2,
    satellite.corY2,
    satellite.corZ2,
    satellite.corX3,
    satellite.corY3,
    satellite.corZ3,
    satellite.corX4,
    satellite.corY4,
    satellite.corZ4,
    scale,
  ]);

  const geometries = useMemo(() => {
    if (corners.length !== 4) return null;

    const [p1, p2, p3, p4] = corners;
    return {
      side1: createTriangleGeometry(p1, p2, position),
      side2: createTriangleGeometry(p2, p3, position),
      side3: createTriangleGeometry(p3, p4, position),
      side4: createTriangleGeometry(p4, p1, position),
      base: createQuadGeometry(p1, p2, p3, p4),
    };
  }, [corners, position]);

  useEffect(() => {
    return () => {
      if (!geometries) return;
      geometries.side1.dispose();
      geometries.side2.dispose();
      geometries.side3.dispose();
      geometries.side4.dispose();
      geometries.base.dispose();
    };
  }, [geometries]);

  return (
    <group>
      <mesh position={position} quaternion={bodyQuaternion}>
        <boxGeometry args={bodySize} />
        <meshStandardMaterial color={bodyColor} emissive={bodyColor} emissiveIntensity={0.2} />
      </mesh>

      {showFootprint && geometries ? (
        <>
          <mesh geometry={geometries.side1}>
            <meshStandardMaterial color={projectionColor} transparent opacity={0.2} side={THREE.DoubleSide} />
          </mesh>
          <mesh geometry={geometries.side2}>
            <meshStandardMaterial color={projectionColor} transparent opacity={0.2} side={THREE.DoubleSide} />
          </mesh>
          <mesh geometry={geometries.side3}>
            <meshStandardMaterial color={projectionColor} transparent opacity={0.2} side={THREE.DoubleSide} />
          </mesh>
          <mesh geometry={geometries.side4}>
            <meshStandardMaterial color={projectionColor} transparent opacity={0.2} side={THREE.DoubleSide} />
          </mesh>
          <mesh geometry={geometries.base}>
            <meshStandardMaterial color={footprintColor} transparent opacity={0.5} side={THREE.DoubleSide} />
          </mesh>
        </>
      ) : null}
    </group>
  );
}
