"use client";

import { Suspense, useEffect, useRef } from "react";
import { Canvas, useFrame, useLoader } from "@react-three/fiber";
import { PerspectiveCamera, Stars } from "@react-three/drei";
import { TextureLoader } from "three";
import * as THREE from "three";

const INITIAL_ROTATION_OFFSET_Y = -2.63;
const EARTH_TEXTURE_URLS = ["/planet_texture/earth_texture_hd.jpg", "/planet_texture/clouds_texture_hd.jpg"];

export function clear_earth_textures() {
  useLoader.clear(TextureLoader, EARTH_TEXTURE_URLS);
}

// 只能在 Canvas 内部调用 hooks
function EarthModel({ on_ready }: { on_ready: () => void }) {
  const earth_group = useRef<THREE.Group>(null);
  const atmosphere_group = useRef<THREE.Group>(null);
  const [texture, cloud_texture] = useLoader(TextureLoader, EARTH_TEXTURE_URLS);
  const ready_frame = useRef<number | null>(null);
  const is_reported = useRef(false);
  useEffect(() => () => {
    if (ready_frame.current !== null) cancelAnimationFrame(ready_frame.current);
    ready_frame.current = null;
    is_reported.current = false;
  }, []);

  const report_first_render = () => {
    if (is_reported.current) return;
    is_reported.current = true;
    // The mesh has been drawn. Reveal the page on the following presentation frame.
    ready_frame.current = requestAnimationFrame(on_ready);
  };

  useFrame((_, delta) => {
    if (earth_group.current) {
      earth_group.current.rotation.y += Math.min(delta, 0.1) * 0.03;
    }
    if (atmosphere_group.current) {
      atmosphere_group.current.rotation.y += Math.min(delta, 0.1) * 0.054;
    }
  });

  return (
    <>
      {/* 大气与云层（快速旋转） */}
      <group ref={atmosphere_group} rotation={[0, INITIAL_ROTATION_OFFSET_Y, 0]}>
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
            alphaMap={cloud_texture}
            transparent
            opacity={0.8}
            depthWrite={false}
          />
        </mesh>
      </group>

      {/* 地表（慢速旋转） */}
      <group ref={earth_group} rotation={[0, INITIAL_ROTATION_OFFSET_Y, 0]}>
        <mesh onAfterRender={report_first_render}>
          <sphereGeometry args={[2, 64, 64]} />
          <meshStandardMaterial map={texture} roughness={0.8} metalness={0.02} />
        </mesh>
      </group>
    </>
  );
}

export default function Earth({ is_full, on_ready, on_error }: {
  is_full: boolean;
  on_ready: () => void;
  on_error: (error: string) => void;
}) {
  const cleanup_context = useRef<(() => void) | null>(null);
  useEffect(() => () => cleanup_context.current?.(), []);
  return (
    <div className="w-full h-full" style={{ filter: "grayscale(1)" }}
      role="img" aria-label="Rotating monochrome Earth" data-testid="dashboard-earth">
      <Canvas className="w-full h-full bg-black" dpr={[1, 1.5]}
        gl={(defaults) => {
          try { return new THREE.WebGLRenderer({ ...defaults, antialias: true, alpha: true, powerPreference: "high-performance" }); }
          catch (error) { on_error("The 3D background could not start. Please try again."); throw error; }
        }}
        fallback={<p>The 3D background is unavailable.</p>}
        onCreated={({ gl }) => {
          cleanup_context.current?.();
          const handle_context_loss = () => on_error("The background connection was interrupted. Please try again.");
          gl.domElement.addEventListener("webglcontextlost", handle_context_loss);
          cleanup_context.current = () => gl.domElement.removeEventListener("webglcontextlost", handle_context_loss);
        }}>
        <PerspectiveCamera
          makeDefault
          position={[0, 0, is_full ? 12 : 5]}
          fov={30}
        />
        <directionalLight position={[10, 10, 10]} intensity={0.5} color="#fff" />
        <ambientLight intensity={0.2} />
        <Stars radius={150} depth={50} count={600} factor={3} fade speed={0.1} />
        <Suspense fallback={null}><EarthModel on_ready={on_ready} /></Suspense>
      </Canvas>
    </div>
  );
}
