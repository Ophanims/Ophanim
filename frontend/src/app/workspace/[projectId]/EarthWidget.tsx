"use client";

import { useLoader } from "@react-three/fiber";
import { TextureLoader } from "three";
import type { EarthMode } from "@/app/workspace/[projectId]/useFrameWidgetSettings";

const INITIAL_ROTATION_OFFSET_Y = -2.63;
// const AXIAL_TILT_RAD = (23.44 * Math.PI) / 180;

type EarthWidgetProps = {
  mode: EarthMode;
  radius: number;
  rotationSpeed?: number;
  slotCount?: number;
};

function TextureEarth({ radius, rotationY }: { radius: number; rotationY: number }) {
  const texture = useLoader(TextureLoader, "/planet_texture/earth_obj_texture.png");

  return (
    <group rotation={[0, rotationY, 0]}>
      {/* <group rotation={[AXIAL_TILT_RAD, 0, 0]}> */}
        <mesh>
          <sphereGeometry args={[radius, 64, 64]} />
          <meshStandardMaterial map={texture} roughness={0.8} metalness={0.02} />
        </mesh>
      {/* </group> */}
    </group>
  );
}

function RealisticEarth({ radius, earthRotationY, cloudRotationY }: { radius: number; earthRotationY: number; cloudRotationY: number }) {
  const texture = useLoader(TextureLoader, "/planet_texture/earth_texture_hd.jpg");
  const cloudTexture = useLoader(TextureLoader, "/planet_texture/clouds_texture_hd.jpg");

  return (
    <group rotation={[0, earthRotationY, 0]}>
      {/* <group rotation={[AXIAL_TILT_RAD, 0, 0]}> */}
        <mesh>
          <sphereGeometry args={[radius * 1.04, 64, 64]} />
          <meshBasicMaterial color={0xffffff} transparent opacity={0.1} depthWrite={false} />
        </mesh>

        <mesh>
          <sphereGeometry args={[radius * 1.02, 64, 64]} />
          <meshPhongMaterial
            color={0xffffff}
            alphaMap={cloudTexture}
            transparent
            opacity={0.8}
            depthWrite={false}
          />
        </mesh>

        <mesh>
          <sphereGeometry args={[radius, 64, 64]} />
          <meshStandardMaterial map={texture} roughness={0.8} metalness={0.02} />
        </mesh>
      {/* </group> */}
    </group>
  );
}

export default function EarthWidget({ mode, radius, rotationSpeed = 0.004178074, slotCount = 0 }: EarthWidgetProps) {
  if (mode === "hidden") return null;

  const twoPi = Math.PI * 2;
  const safeSlotCount = Number.isFinite(slotCount) ? slotCount : 0;
  const radPerSlot = (rotationSpeed * Math.PI) / 180;
  const earthRotationY = (Math.PI + INITIAL_ROTATION_OFFSET_Y + safeSlotCount * radPerSlot) % twoPi;
  const cloudRotationY = (Math.PI + INITIAL_ROTATION_OFFSET_Y + safeSlotCount * radPerSlot * 1.8) % twoPi;

  if (mode === "sphere") {
    return (
      <group rotation={[0, earthRotationY, 0]}>
        {/* <group rotation={[AXIAL_TILT_RAD, 0, 0]}> */}
          <mesh>
            <sphereGeometry args={[radius, 64, 64]} />
            <meshStandardMaterial color="#2b2b2b" emissive="#2b2b2b" roughness={0.7} metalness={0.05} />
          </mesh>
        {/* </group> */}
      </group>
    );
  }

  if (mode === "texture") {
    return <TextureEarth radius={radius} rotationY={earthRotationY} />;
  }

  return <RealisticEarth radius={radius} earthRotationY={earthRotationY} cloudRotationY={cloudRotationY} />;
}
