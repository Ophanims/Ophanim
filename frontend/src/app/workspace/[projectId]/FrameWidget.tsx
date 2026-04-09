"use client";

import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import EarthWidget from "@/app/workspace/[projectId]/EarthWidget";
import LatLonWidget from "@/app/workspace/[projectId]/LatLonWidget";
import { EARTH_MODE, LATLON_MODE, SATELLITE_MODE, type FrameWidgetSettings } from "@/app/workspace/[projectId]/useFrameWidgetSettings";

type SatellitePoint = {
  id: string;
  x: number;
  y: number;
  z: number;
};

export default function FrameWidget({
  satellites,
  settings,
}: {
  satellites: SatellitePoint[];
  settings?: Partial<FrameWidgetSettings>;
}) {
  // const scale = useMemo(() => {
  //   let maxAbs = 0;
  //   for (const s of satellites) {
  //     maxAbs = Math.max(maxAbs, Math.abs(s.x), Math.abs(s.y), Math.abs(s.z));
  //   }
  //   if (maxAbs <= 0) return 1;
  //   return 2.2 / maxAbs;
  // }, [satellites]);

  const scale = 0.0000003;

  const earthRadius = 6371000 * scale;
  const earthMode = settings?.earthMode ?? EARTH_MODE.REALISTIC;
  const latLonMode = settings?.latLonMode ?? LATLON_MODE.HIDDEN;
  const satelliteMode = settings?.satelliteMode ?? SATELLITE_MODE.SHOW;
  const earthRotationSpeed = settings?.earthRotationSpeed ?? 0.0012;
  const earthTransitionDuration = settings?.earthTransitionDuration ?? 0.35;

  return (
    <div className="h-screen w-full overflow-hidden bg-black pointer-events-auto">
      <Canvas className="pointer-events-auto touch-none" camera={{ position: [0, 0, 8], fov: 45 }}>
        <ambientLight intensity={0.8} />
        <directionalLight position={[4, 3, 6]} intensity={1.2} />
        <EarthWidget
          mode={earthMode}
          radius={earthRadius}
          rotationSpeed={earthRotationSpeed}
        />
        <LatLonWidget
          visible={latLonMode === LATLON_MODE.SHOW}
          radius={earthRadius}
          rotationSpeed={earthRotationSpeed}
        />
        {satelliteMode === SATELLITE_MODE.SHOW
          ? satellites.map((s) => (
              <mesh key={s.id} position={[s.x * scale, s.z * scale, -s.y * scale]}>
                <sphereGeometry args={[0.02, 10, 10]} />
                <meshStandardMaterial
                  color="#ffffff"
                  emissive="#ffffff"
                  emissiveIntensity={0.35}
                />
              </mesh>
            ))
          : null}
        <OrbitControls enablePan={false} enableDamping dampingFactor={0.08} />
      </Canvas>
    </div>
  );
}
