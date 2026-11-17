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
import { useFrames } from "../workspace/useFramesContext";
import { Earth,Links,RoIs,Satellites,Stations,Sun } from "./GeometryPrimitives";







function GeometryView({
  sun,
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
  return (
    <Canvas
      camera={{ position: [0, 0, 28000], fov: 30, near: 1000, far: 100000 }}
    >
      <group rotation={[-Math.PI / 2, 0, 0]}>
        {/* <primitive
          object={(() => {
            const arrow = new THREE.ArrowHelper(
              new THREE.Vector3(-1, 0, 0),
              new THREE.Vector3(0, 0, 0),
              10000,
              0xff0000,
              400,
              200
            );
            return arrow;
          })()}
        />
        <primitive
          object={(() => {
            const arrow = new THREE.ArrowHelper(
              new THREE.Vector3(0, 1, 0),
              new THREE.Vector3(0, 0, 0),
              10000,
              0x00ff00,
              400,
              200
            );
            return arrow;
          })()}
        />
        <primitive
          object={(() => {
            const arrow = new THREE.ArrowHelper(
              new THREE.Vector3(0, 0, 1),
              new THREE.Vector3(0, 0, 0),
              10000,
              0x0000ff,
              400,
              200
            );
            return arrow;
          })()}
        /> */}
        {/* <Html position={[-10000, 0, 0]}>
          <span style={{ color: "red" }}>X</span>
        </Html>
        <Html position={[0, 10000, 0]}>
          <span style={{ color: "green" }}>Y</span>
        </Html>
        <Html position={[0, 0, 10000]}>
          <span style={{ color: "blue" }}>Z</span>
        </Html> */}
        <Sun sun={sun} />
        <Satellites satellites={satellites} />
        <Stations stations={stations} />
        <Links links={links} />
        <RoIs rois={rois} />
      </group>
      <Earth earth={earth} />
      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        minDistance={6371}
        maxDistance={50000}
      />
    </Canvas>
  );
}

export default function UniverseView() {
  const { frames, selected_frame_index } = useFrames();
  const frame = frames[selected_frame_index];
  if (!frame) return <VoidPage />;
  return <div className="relative flex h-full w-full flex-col bg-black text-white">
    <div className="absolute top-2 right-0 z-10"><ClockWidget frame_counter={frame.frame_counter} time={frame.time} /></div>
    <GeometryView sun={frame.sun} earth={frame.earth} satellites={frame.satellites}
      stations={frame.stations} links={frame.links} rois={frame.rois} />
  </div>;
}
