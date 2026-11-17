import ClockWidget from "@/features/simulation/components/ClockWidget";
import VoidPage from "@/features/simulation/components/VoidPage";
import {
EarthSnapshot,
LinkSnapshot,
ROISnapshot,
SatelliteSnapshot,
StationSnapshot,
SunSnapshot,
} from "@/features/simulation/types/simulation";
import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import {
useMemo,
useRef
} from "react";
import * as THREE from "three";
import { useFrames } from "../workspace/useFramesContext";
import { build_plane_color_map,Earth,Links,OrbitRings,RoIs,Satellites,Stations } from "./ObjectPrimitives";









function UniverseScene({
  earth,
  satellites,
  stations,
  links,
  rois,
}: {
  sun: SunSnapshot;
  earth: EarthSnapshot;
  satellites: SatelliteSnapshot[];
  stations: StationSnapshot[];
  links: LinkSnapshot[];
  rois: ROISnapshot[];
}) {
  const earth_ref = useRef<THREE.Object3D>(null!);
  const { plane_color_map } = useMemo(
    () => build_plane_color_map(satellites),
    [satellites]
  );

  return (
    <Canvas
      shadows
      camera={{ position: [0, 0, 28000], fov: 30, near: 1000, far: 100000 }}
      onCreated={({ gl }) => {
        gl.setClearColor("#fff"); // 背景白色
      }}
    >
      <ambientLight intensity={1.2} />
      <group rotation={[-Math.PI / 2, 0, 0]}>
        <Earth earth={earth} earth_ref={earth_ref} />
        <Satellites
          satellites={satellites}
          earth_ref={earth_ref}
          plane_color_map={plane_color_map}
        />
        <Stations stations={stations} earth_ref={earth_ref} />
        <Links links={links} plane_color_map={plane_color_map} />
        <OrbitRings satellites={satellites} plane_color_map={plane_color_map} />
        <RoIs rois={rois} />
      </group>
      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        minDistance={7500}
        maxDistance={100000}
      />
    </Canvas>
  );
}

export default function ObjectView() {
  const { frames, selected_frame_index } = useFrames();
  const frame = frames[selected_frame_index];
  if (!frame) return <VoidPage />;
  return <div className="relative flex h-full w-full flex-col bg-black text-white">
    <div className="absolute top-2 right-0 z-10"><ClockWidget frame_counter={frame.frame_counter} time={frame.time} /></div>
    <UniverseScene sun={frame.sun} earth={frame.earth} satellites={frame.satellites}
      stations={frame.stations} links={frame.links} rois={frame.rois} />
  </div>;
}
