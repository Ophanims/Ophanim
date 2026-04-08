"use client";

import { useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

type SatellitePoint = {
  id: string;
  x: number;
  y: number;
  z: number;
};

export default function RecordFrameWidget({
  satellites,
}: {
  satellites: SatellitePoint[];
}) {
  const scale = useMemo(() => {
    let maxAbs = 0;
    for (const s of satellites) {
      maxAbs = Math.max(maxAbs, Math.abs(s.x), Math.abs(s.y), Math.abs(s.z));
    }
    if (maxAbs <= 0) return 1;
    return 2.2 / maxAbs;
  }, [satellites]);

  return (
    <div className="h-80 w-full overflow-hidden border bg-black/95">
      <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
        {satellites.map((s) => (
          <mesh key={s.id} position={[s.x * scale, s.y * scale, s.z * scale]}>
            <sphereGeometry args={[0.03, 10, 10]} />
            <meshStandardMaterial
              color="#ffffff"
              emissive="#ffffff"
              emissiveIntensity={0.35}
            />
          </mesh>
        ))}
      </Canvas>
    </div>
  );
}
