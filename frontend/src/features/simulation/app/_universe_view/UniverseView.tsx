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
import { Canvas,useLoader } from "@react-three/fiber";
import React,{
useEffect,
useMemo,
useRef
} from "react";
import * as THREE from "three";
import { TextureLoader } from "three";
import { EARTH_DISPLAY_RADIUS_P,SCALE } from "../../lib/DefaultObjects";
import { useFrames } from "../workspace/useFramesContext";


function Earth({
  earth,
  earth_ref,
}: {
  earth: EarthSnapshot;
  earth_ref: React.RefObject<THREE.Object3D>;
}) {
  const texture = useLoader(TextureLoader, "/planet_texture/earth_texture_hd.jpg");
  const cloud_texture = useLoader(TextureLoader, "/planet_texture/clouds_texture_hd.jpg");
  // const cloudTexture = useMemo(
  //   () => invertTexture(rawCloudTexture),
  //   [rawCloudTexture]
  // );
  const default_rotation_y = 3.14;



  return (
    <group>
      <mesh rotation={[Math.PI / 2, earth.rotation + default_rotation_y, 0]}>
        <sphereGeometry args={[EARTH_DISPLAY_RADIUS_P * 1.04, 64, 64]} />
        <meshBasicMaterial
          color={0xffffff}
          transparent
          opacity={0.1}
          depthWrite={false}
        />
      </mesh>
      <mesh rotation={[Math.PI / 2, earth.rotation + default_rotation_y, 0]}>
        <sphereGeometry args={[EARTH_DISPLAY_RADIUS_P * 1.02, 64, 64]} />
        <meshPhongMaterial
          color={0xffffff}
          alphaMap={cloud_texture}
          transparent
          opacity={0.8}
          depthWrite={false}
        />
      </mesh>
      <mesh
        ref={earth_ref}
        rotation={[Math.PI / 2, earth.rotation + default_rotation_y, 0]}
      >
        <sphereGeometry args={[EARTH_DISPLAY_RADIUS_P, 64, 64]} />
        <meshStandardMaterial map={texture} roughness={0.8} />
      </mesh>
    </group>
  );
}

function Sun({ sun }: { sun: SunSnapshot }) {
  // DirectionalLight 位置是光源位置，target 默认是场景中心
  const light_ref = useRef<THREE.DirectionalLight>(null);
  const target = useMemo(() => new THREE.Object3D(), []);

  useEffect(() => {
    if (light_ref.current) {
      light_ref.current.target = target;
    }
  }, [target]);

  return (
    <group>
      <directionalLight
        ref={light_ref}
        position={[sun.pos.x * SCALE, sun.pos.y * SCALE, sun.pos.z * SCALE]}
        intensity={1.5}
        color="#fffbe6"
        castShadow
      />
      <primitive object={target} position={[0, 0, 0]} />
    </group>
  );
}

function Satellites({
  satellites,
}: {
  satellites: SatelliteSnapshot[];
  earth_ref: React.RefObject<THREE.Object3D>;
}) {
  return (
    <>
      {satellites.map((sat) => {
        const color = sat.is_charging ? "green" : "red";
        // 新增：使用dimensions设置卫星大小（假设单位m，缩放以匹配场景）
        const pj_color = "white"; // 假设图像颜色为白色
        const img_color = "yellow"; // 假设图像颜色为黄色
        const [length, width, height] = sat.dimensions.map((d) => d * 100);

        const cor = sat.img_corners_pos;

        if (!Array.isArray(cor) || cor.length !== 4) return null;

        // 生成顶点坐标
        const points = cor.map((c) => [c.x * SCALE, c.y * SCALE, c.z * SCALE]);

        return (
          <group
            key={sat.id}
            // quaternion={quaternion} // 应用旋转，使面朝向匹配
          >
            <mesh
              position={[
                sat.pos.x * SCALE,
                sat.pos.y * SCALE,
                sat.pos.z * SCALE,
              ]}
            >
              <boxGeometry args={[length, width, height]} />
              <meshBasicMaterial color={color} />
              {/* <Html
                distanceFactor={5000}
                position={[0, 0, 0]}
                occlude={[earthRef as React.RefObject<THREE.Object3D>]}
              >
                <div
                  className="select-none flex flex-col w-20 items-center"
                  style={{
                    color: "white",
                    fontWeight: 200,
                    fontSize: 10,
                    padding: "1px 4px",
                  }}
                >
                  <span>SAT-{sat.id.slice(-6)}</span>
                </div>
              </Html> */}
            </mesh>
            {points.length === 4 && (
              <>
                {/* 方锥体四个侧面 */}
                {points.map((p, idx) => {
                  const next_idx = (idx + 1) % 4;
                  const vertices = [
                    ...p,
                    ...points[next_idx],
                    sat.pos.x * SCALE,
                    sat.pos.y * SCALE,
                    sat.pos.z * SCALE,
                  ];
                  return (
                    <mesh key={idx}>
                      <bufferGeometry
                        ref={(geo) => {
                          if (geo) {
                            geo.setAttribute(
                              "position",
                              new THREE.Float32BufferAttribute(vertices, 3)
                            );
                            geo.setIndex([0, 1, 2]);
                          }
                        }}
                      />
                      <meshBasicMaterial
                        color={pj_color}
                        transparent
                        opacity={0.2}
                        side={THREE.DoubleSide}
                      />
                    </mesh>
                  );
                })}
                {/* 底面（四边形） */}
                <mesh>
                  <bufferGeometry
                    ref={(geo) => {
                      if (geo) {
                        geo.setAttribute(
                          "position",
                          new THREE.Float32BufferAttribute(points.flat(), 3)
                        );
                        geo.setIndex([0, 1, 2, 0, 2, 3]);
                      }
                    }}
                  />
                  <meshBasicMaterial
                    color={img_color}
                    transparent
                    opacity={0.5}
                    side={THREE.DoubleSide}
                  />
                </mesh>
              </>
            )}
          </group>
        );
      })}
    </>
  );
}

// 地面站组件
function Stations({
  stations,
}: {
  stations: StationSnapshot[];
  earth_ref: React.RefObject<THREE.Object3D>;
}) {
  return (
    <>
      {stations.map((gs) => {
        const color = gs.on_download ? "red" : gs.on_upload ? "blue" : "#ffffff";
        return (
          <mesh
            key={gs.id}
            position={[gs.pos.x * SCALE, gs.pos.y * SCALE, gs.pos.z * SCALE]}
          >
            <sphereGeometry args={[10, 32, 32]} />
            <meshBasicMaterial color={color} />
            {/* <Html
              distanceFactor={5000}
              position={[0, 0, 0]}
              occlude={[earthRef as React.RefObject<THREE.Object3D>]}
            >
              <div
                className="select-none flex flex-col w-20 items-center"
                style={{
                  color: "white",
                  fontWeight: 200,
                  fontSize: 10,
                  padding: "1px 4px",
                }}
              >
                <span>GS-{gs.id.slice(-6)}</span>
              </div>
            </Html> */}
          </mesh>
        );
      })}
    </>
  );
}

function RoIs({ rois }: { rois: ROISnapshot[] }) {
  return (
    <>
      {rois.map((roi) => {
        // 生成 RoI 区域的四个角点
        const cor = roi.corners_pos;
        if (!Array.isArray(cor) || cor.length !== 4) return null;

        // 生成顶点坐标
        const points = cor.map((c) => [c.x * SCALE, c.y * SCALE, c.z * SCALE]);
        // 闭合多边形
        const closed_points = [...points, points[0]];
        // 线条颜色
        const color = 0x00ff00;

        return (
          <group key={roi.id}>
            {/* 绘制 RoI 区域顶点 */}
            {points.map((p, idx) => (
              <mesh key={idx} position={p as [number, number, number]}>
                <sphereGeometry args={[10, 16, 16]} />
                <meshBasicMaterial color={color} />
              </mesh>
            ))}
            {/* 绘制 RoI 区域边界线 */}
            <line>
              <bufferGeometry>
                <bufferAttribute
                  attach="attributes-position"
                  args={[new Float32Array(closed_points.flat()), 3]}
                />
              </bufferGeometry>
              <lineBasicMaterial color={color} linewidth={2} />
            </line>
            {/* <Html
              distanceFactor={5000}
              position={[
                roi.centrePos.x * SCALE,
                roi.centrePos.y * SCALE,
                roi.centrePos.z * SCALE,
              ]}
            >
              <div
                className="select-none w-20"
                style={{
                  color: "white",
                  fontWeight: 200,
                  fontSize: 10,
                  padding: "1px 4px",
                }}
              >
                RoI-{roi.id.slice(-6)}
              </div>
            </Html> */}
          </group>
        );
      })}
    </>
  );
}

function Links({ links }: { links: LinkSnapshot[] }) {
  // 先在顶层一次性用 map 生成所有 positions，保证 hooks 只在顶层调用
  const positions_list = React.useMemo(() => {
    return links.map((link) => {
      const [start, end] = link.link_pos;
      const a = new THREE.Vector3(
        start.x * SCALE,
        start.y * SCALE,
        start.z * SCALE
      );
      const b = new THREE.Vector3(end.x * SCALE, end.y * SCALE, end.z * SCALE);
      return new Float32Array([a.x, a.y, a.z, b.x, b.y, b.z]);
    });
  }, [links]);

  return (
    <>
      {links.map((link, idx) => {
        const color = link.type === "ISL" ? "white" : "red";
        const positions = positions_list[idx];

        return (
          <line key={`${link.src}_${link.dst}_link`}>
            <bufferGeometry attach="geometry">
              <bufferAttribute
                attach="attributes-position"
                args={[positions, 3]}
              />
            </bufferGeometry>
            <lineBasicMaterial
              attach="material"
              color={color}
              transparent
              opacity={0.1}
            />
          </line>
        );
      })}
    </>
  );
}

function UniverseScene({
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
  const earth_ref = useRef<THREE.Object3D>(null!);

  return (
    <Canvas
      camera={{ position: [0, 0, 28000], fov: 30, near: 1000, far: 100000 }}
    >
      <group rotation={[-Math.PI / 2, 0, 0]}>
        <Earth earth={earth} earth_ref={earth_ref} />
        <Sun sun={sun} />
        <Satellites satellites={satellites} earth_ref={earth_ref} />
        <Stations stations={stations} earth_ref={earth_ref} />
        <Links links={links} />
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

export default function UniverseView() {
  const { frames, selected_frame_index } = useFrames();
  const frame = frames[selected_frame_index];
  if (!frame) return <VoidPage />;
  return <div className="relative flex h-full w-full flex-col bg-black text-white">
    <div className="absolute top-2 right-0 z-10"><ClockWidget frame_counter={frame.frame_counter} time={frame.time} /></div>
    <UniverseScene sun={frame.sun} earth={frame.earth} satellites={frame.satellites}
      stations={frame.stations} links={frame.links} rois={frame.rois} />
  </div>;
}
