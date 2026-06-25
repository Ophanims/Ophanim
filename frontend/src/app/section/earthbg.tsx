"use client";

import { useRef } from "react";
import { Canvas, useFrame, useLoader } from "@react-three/fiber";
import { PerspectiveCamera, Stars } from "@react-three/drei";
import { TextureLoader } from "three";
import * as THREE from "three";

const INITIAL_ROTATION_OFFSET_Y = -2.63;

// 只能在 Canvas 内部调用 hooks
function EarthModel() {
  const earthGroup = useRef<THREE.Group>(null);
  const atmoGroup = useRef<THREE.Group>(null);
  const texture = useLoader(TextureLoader, "/planet_texture/earth_texture_hd.jpg");
  const cloudTexture = useLoader(TextureLoader, "/planet_texture/clouds_texture_hd.jpg");

  useFrame(() => {
    if (earthGroup.current) {
      earthGroup.current.rotation.y += 0.0005;
    }
    if (atmoGroup.current) {
      atmoGroup.current.rotation.y += 0.0009; // 大气/云层比地表快 1.8 倍
    }
  });

  return (
    <>
      {/* 大气与云层（快速旋转） */}
      <group ref={atmoGroup} rotation={[0, INITIAL_ROTATION_OFFSET_Y, 0]}>
        {/* 大气发光层 */}
        <mesh>
          <sphereGeometry args={[2.08, 64, 64]} />
          <meshBasicMaterial color={0xffffff} transparent opacity={0.1} depthWrite={false} />
        </mesh>

        {/* 云层 */}
        <mesh>
          <sphereGeometry args={[2.04, 64, 64]} />
          <meshPhongMaterial
            color={0xffffff}
            alphaMap={cloudTexture}
            transparent
            opacity={0.8}
            depthWrite={false}
          />
        </mesh>
      </group>

      {/* 地表（慢速旋转） */}
      <group ref={earthGroup} rotation={[0, INITIAL_ROTATION_OFFSET_Y, 0]}>
        <mesh>
          <sphereGeometry args={[2, 64, 64]} />
          <meshStandardMaterial map={texture} roughness={0.8} metalness={0.02} />
        </mesh>
      </group>
    </>
  );
}

export default function Earth({ isFull }: { isFull: boolean }) {
  return (
    <div className="w-full h-full" style={{ filter: "grayscale(1)" }}>
      <Canvas className="w-full h-full bg-black">
        <PerspectiveCamera
          makeDefault
          position={[0, 0, isFull ? 12 : 5]}
          fov={30}
        />
        <directionalLight position={[10, 10, 10]} intensity={0.5} color="#fff" />
        <ambientLight intensity={0.2} />
        <Stars radius={150} depth={50} count={600} factor={3} fade speed={0.1} />
        <EarthModel />
      </Canvas>
    </div>
  );
}
