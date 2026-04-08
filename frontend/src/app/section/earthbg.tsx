import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { PerspectiveCamera, Stars, useTexture } from "@react-three/drei";
import * as THREE from "three";

// 只能在 Canvas 内部调用 hooks
function EarthModel() {
  const mesh = useRef<THREE.Mesh>(null);
  const texture = useTexture("/planet_texture/earth_texture.jpg");

  useFrame(() => {
    if (mesh.current) {
      mesh.current.rotation.y += 0.0005;
    }
  });

  return (
    <mesh ref={mesh} position={[0, 0, 0]}>
      <sphereGeometry args={[2, 64, 64]} />
      <meshStandardMaterial map={texture} roughness={1} metalness={0.1} />
    </mesh>
  );
}

export default function Earth({ isFull }: { isFull: boolean }) {
  return (
    <Canvas className="w-full h-full bg-black">
      <PerspectiveCamera
        makeDefault
        position={[0, 0, isFull ? 12 : 5]}
        fov={30}
      />
      <directionalLight position={[10, 10, 10]} intensity={3} color="#fff" />
      <ambientLight intensity={0.2} />
      <Stars radius={150} depth={50} count={600} factor={3} fade speed={0.1} />
      <EarthModel />
    </Canvas>
  );
}
