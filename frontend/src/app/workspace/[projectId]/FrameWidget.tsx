"use client";

import { useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import EarthWidget from "@/app/workspace/[projectId]/EarthWidget";
import LatLonWidget from "@/app/workspace/[projectId]/LatLonWidget";
import SatelliteWidget, { type RenderSatellitePoint } from "@/app/workspace/[projectId]/SatelliteWidget";
import {
  EARTH_MODE,
  FOOTPRINT_MODE,
  LATLON_MODE,
  SATELLITE_MODE,
  STATION_MODE,
  type FrameWidgetSettings,
} from "@/app/workspace/[projectId]/useFrameWidgetSettings";
import {
  EarthPoint,
  StationPoint,
  SunPoint,
} from "@/app/simulation/[projectId]/simulation.model";

export default function FrameWidget({
  sun,
  earth,
  satellites,
  stations,
  slotCount,
  settings,
}: {
  sun?: SunPoint | null;
  earth?: EarthPoint | null;
  satellites: RenderSatellitePoint[];
  stations?: StationPoint[];
  slotCount?: number;
  settings?: Partial<FrameWidgetSettings>;
}) {
  const scale = 0.0000003;

  const earthRadius = 6371000 * scale;
  const earthMode = settings?.earthMode ?? EARTH_MODE.REALISTIC;
  const latLonMode = settings?.latLonMode ?? LATLON_MODE.HIDDEN;
  const satelliteMode = settings?.satelliteMode ?? SATELLITE_MODE.SHOW;
  const stationMode = settings?.stationMode ?? STATION_MODE.SHOW;
  const footprintMode = settings?.footprintMode ?? FOOTPRINT_MODE.SHOW;
  const earthRotationSpeed =
    earth?.rotationalAngularVelocity ??
    settings?.earthRotationSpeed ??
    0.004178074;
  const sunLightPosition = useMemo<[number, number, number]>(() => {
    if (!sun) return [4, 3, 6];

    // Convert backend coordinates to scene coordinates and normalize for stable directional lighting.
    const sx = sun.x * scale;
    const sy = sun.y * scale;
    const sz = sun.z * scale;
    const length = Math.hypot(sx, sy, sz);
    if (!Number.isFinite(length) || length <= 0) return [4, 3, 6];

    const lightDistance = 20;
    return [
      (sx / length) * lightDistance,
      (sy / length) * lightDistance,
      (sz / length) * lightDistance,
    ];
  }, [sun, scale]);

  return (
    <div className="h-screen w-full overflow-hidden bg-black pointer-events-auto">
      <Canvas
        className="pointer-events-auto touch-none"
        camera={{ position: [0, 0, 8], fov: 45 }}
      >
        <ambientLight intensity={0.01} />
        <directionalLight position={sunLightPosition} intensity={2} />
        <EarthWidget
          mode={earthMode}
          radius={earthRadius}
          rotationSpeed={earthRotationSpeed}
          slotCount={slotCount}
        />
        <LatLonWidget
          visible={latLonMode === LATLON_MODE.SHOW}
          radius={earthRadius}
          rotationSpeed={earthRotationSpeed}
          slotCount={slotCount}
        />
        {earth ? (
          <mesh
            key={"null-island"}
            position={[
              earth.nullIslandX * scale,
              earth.nullIslandZ * scale,
              -earth.nullIslandY * scale,
            ]}
          >
            <sphereGeometry args={[0.03, 10, 10]} />
            <meshStandardMaterial
              color="#ff0000"
              emissive="#ff0000"
              emissiveIntensity={0.25}
            />
          </mesh>
        ) : null}
        {satelliteMode === SATELLITE_MODE.SHOW
          ? satellites.map((s, idx) => (
              <SatelliteWidget
                key={`${s.id ?? "unknown"}-${s.addr ?? "unknown"}-${idx}`}
                satellite={s}
                scale={scale}
                showFootprint={footprintMode === FOOTPRINT_MODE.SHOW}
              />
            ))
          : null}
        {stationMode === STATION_MODE.SHOW && stations
          ? stations.map((st) => (
              <mesh
                key={`${st.addr}`}
                position={[st.x * scale, st.z * scale, -st.y * scale]}
              >
                <sphereGeometry args={[0.03, 10, 10]} />
                <meshStandardMaterial
                  color="#ffff00"
                  emissive="#ffff00"
                  emissiveIntensity={0.25}
                />
              </mesh>
            ))
          : null}
        <OrbitControls enablePan={false} enableDamping dampingFactor={0.08} />
      </Canvas>
    </div>
  );
}
