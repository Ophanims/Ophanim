"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { useLoader } from "@react-three/fiber";
import { TextureLoader, type Mesh } from "three";
import type { EarthMode } from "@/app/workspace/[projectId]/useFrameWidgetSettings";

type EarthWidgetProps = {
  mode: EarthMode;
  radius: number;
  rotationSpeed?: number;
};

function TextureEarth({ radius, rotationSpeed = 0.0012 }: { radius: number; rotationSpeed?: number }) {
  const earthRef = useRef<Mesh>(null);
  const texture = useLoader(TextureLoader, "/planet_texture/earth_obj_texture.png");
  const defaultRotationY = Math.PI;

  useFrame(() => {
    if (earthRef.current) {
      earthRef.current.rotation.y += rotationSpeed;
    }
  });

  return (
    <mesh ref={earthRef} rotation={[0, defaultRotationY, 0]}>
      <sphereGeometry args={[radius, 64, 64]} />
      <meshStandardMaterial map={texture} roughness={0.8} metalness={0.02} />
    </mesh>
  );
}

function RealisticEarth({ radius, rotationSpeed = 0.0012 }: { radius: number; rotationSpeed?: number }) {
  const earthRef = useRef<Mesh>(null);
  const cloudRef = useRef<Mesh>(null);
  const texture = useLoader(TextureLoader, "/planet_texture/earth_texture_hd.jpg");
  const cloudTexture = useLoader(TextureLoader, "/planet_texture/clouds_texture_hd.jpg");
  const defaultRotationY = Math.PI;

  useFrame(() => {
    if (earthRef.current) {
      earthRef.current.rotation.y += rotationSpeed;
    }
    if (cloudRef.current) {
      cloudRef.current.rotation.y += rotationSpeed * 1.8;
    }
  });

  return (
    <group>
      {/* <mesh rotation={[Math.PI / 2, defaultRotationY, 0]}> */}
      <mesh rotation={[0, defaultRotationY, 0]}>
        <sphereGeometry args={[radius * 1.04, 64, 64]} />
        <meshBasicMaterial color={0xffffff} transparent opacity={0.1} depthWrite={false} />
      </mesh>

      <mesh ref={cloudRef} rotation={[0, defaultRotationY, 0]}>
        <sphereGeometry args={[radius * 1.02, 64, 64]} />
        <meshPhongMaterial
          color={0xffffff}
          alphaMap={cloudTexture}
          transparent
          opacity={0.8}
          depthWrite={false}
        />
      </mesh>

      {/* <mesh ref={earthRef} rotation={[Math.PI / 2, defaultRotationY, 0]}> */}
      <mesh ref={earthRef} rotation={[0, defaultRotationY, 0]}>
        <sphereGeometry args={[radius, 64, 64]} />
        <meshStandardMaterial map={texture} roughness={0.8} metalness={0.02} />
      </mesh>
    </group>
  );
}

export default function EarthWidget({ mode, radius, rotationSpeed = 0.0012 }: EarthWidgetProps) {
  if (mode === "hidden") return null;

  if (mode === "sphere") {
    return (
      <mesh rotation={[0, Math.PI, 0]}>
        <sphereGeometry args={[radius, 64, 64]} />
        <meshStandardMaterial color="#1d4ed8" roughness={0.7} metalness={0.05} />
      </mesh>
    );
  }

  if (mode === "texture") {
    return <TextureEarth radius={radius} rotationSpeed={rotationSpeed} />;
  }

  return <RealisticEarth radius={radius} rotationSpeed={rotationSpeed} />;
}
