import {
EarthSnapshot,
LinkSnapshot,
ROISnapshot,
SatelliteSnapshot,
StationSnapshot,
SunSnapshot,
} from "@/features/simulation/types/simulation";
import { Html } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import React,{ useRef } from "react";
import * as THREE from "three";
import { SCALE } from "../../lib/DefaultObjects";
export function Earth({ earth }: { earth: EarthSnapshot }) {
  const earth_ref = useRef<THREE.Mesh>(null);
  const grid_group = new THREE.Group();

  const default_rotation_y = -0.12; // 初始旋转角度，用来对齐texture和真实数据坐标

  useFrame(() => {
    if (earth_ref.current) {
      earth_ref.current.rotation.y = earth.rotation + default_rotation_y;
    }
  });

  return (
    <group>
      <mesh ref={earth_ref}>
        <primitive object={grid_group} />
      </mesh>
    </group>
  );
}

export function Sun({ sun }: { sun: SunSnapshot }) {
  // DirectionalLight 位置是光源位置，target 默认是场景中心
  return (
    <directionalLight
      position={[sun.pos.x * SCALE, sun.pos.y * SCALE, sun.pos.z * SCALE]}
      intensity={2}
      color="#fffbe6"
      castShadow
      target-position={[0, 0, 0]}
    />
  );
}

export function Satellites({ satellites }: { satellites: SatelliteSnapshot[] }) {
  return (
    <>
      {satellites.map((sat) => {
        const color = sat.is_processing
          ? "white"
          : sat.is_communicating_sgl
          ? "red"
          : sat.is_charging
          ? "#ffeb3b"
          : sat.is_observing
          ? "#fb8c00"
          : "#aaaaaa";

        const img_color = "green"; // 假设图像颜色为绿色
        // 新增：使用dimensions设置卫星大小（假设单位m，缩放以匹配场景）
        const [length, width, height] = sat.dimensions.map((d) => d * 100);

        // 新增：计算卫星旋转，使面朝向匹配face_orientations
        // 构建旋转矩阵：+x=zenith (from pos), -z=velocity_vector, +y=cross(zenith, velocity)
        const zenith = new THREE.Vector3(
          sat.pos.x,
          sat.pos.y,
          sat.pos.z
        ).normalize(); // +x (away from Earth)，匹配three.js y-up = ECEF z
        const velocity_vec = new THREE.Vector3(
          sat.velocity_vector.x,
          sat.velocity_vector.y,
          sat.velocity_vector.z
        ).normalize(); // -z (flight direction)，匹配映射
        const solar_vec = new THREE.Vector3(
          sat.solar_vector.x,
          sat.solar_vector.y,
          sat.solar_vector.z
        )
          .normalize()
          .negate(); // -z (flight direction)，匹配映射
        const z_dir = velocity_vec.clone().negate(); // +z = -velocity (adjust if needed)
        const unit_y = new THREE.Vector3()
          .crossVectors(z_dir, zenith)
          .normalize();
        const x_dir = zenith; // +x
        // 验证右手系: cross(x, y) should ≈ z
        // const isRightHanded = cross_xy.distanceTo(z_dir) < 1e-6; // Approximate equality for floating point
        // console.log(isRightHanded); // Should be true if vectors are orthogonal and right-handed

        // 旋转矩阵：columns = [x_dir, y_dir, z_dir]
        const rotation_matrix = new THREE.Matrix4().makeBasis(
          x_dir,
          unit_y,
          z_dir
        );

        // 转换为Euler或Quaternion应用于mesh
        const quaternion = new THREE.Quaternion().setFromRotationMatrix(
          rotation_matrix
        );

        const cor = sat.img_corners_pos;

        if (!Array.isArray(cor) || cor.length !== 4) return null;

        // 生成顶点坐标
        const points = cor.map((c) => [c.x * SCALE, c.y * SCALE, c.z * SCALE]);
        // 闭合多边形

        const sat_pos: [number, number, number] = [
          sat.pos.x * SCALE,
          sat.pos.y * SCALE,
          sat.pos.z * SCALE,
        ];

        return (
          <group
            key={sat.id}
            // quaternion={quaternion} // 应用旋转，使面朝向匹配
          >
            <mesh
              position={sat_pos}
              quaternion={quaternion} // 应用旋转，使面朝向匹配
            >
              <boxGeometry args={[length, width, height]} />
              <meshBasicMaterial color={color} />
              {/* <Html distanceFactor={5000} position={[0, 0, 0]}>
                <div
                  className="select-none w-20"
                  style={{
                    color: "white",
                    fontWeight: 200,
                    fontSize: 10,
                    padding: "1px 4px",
                  }}
                >
                  P{sat.plane} - O{sat.order}
                </div>
              </Html> */}
            </mesh>

            {/* 新增：用三个ArrowHelper表示satellite-centered coordinate system的x,y,z轴 */}
            {/* +X axis (red arrow, away from Earth) */}
            <arrowHelper
              position={sat_pos}
              args={[x_dir, new THREE.Vector3(0, 0, 0), length * 20, "red"]}
            />
            {/* +Y axis (green arrow) */}
            <arrowHelper
              position={sat_pos}
              args={[unit_y, new THREE.Vector3(0, 0, 0), width * 20, "green"]}
            />
            {/* +Z axis (blue arrow) */}
            <arrowHelper
              position={sat_pos}
              args={[z_dir, new THREE.Vector3(0, 0, 0), height * 20, "blue"]}
            />
            {/* 新增：太阳向量 (yellow arrow) */}
            {sat.is_charging && (
              <arrowHelper
                position={sat_pos}
                args={[
                  solar_vec,
                  new THREE.Vector3(0, 0, 0),
                  Math.max(length, width, height) * 20,
                  "yellow",
                ]}
              />
            )}
            {points.length === 4 && (
              <mesh>
                <bufferGeometry
                  attach="geometry"
                  args={undefined}
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
                  opacity={0.3} // 半透明
                  side={THREE.DoubleSide}
                />
              </mesh>
            )}
          </group>
        );
      })}
    </>
  );
}

export function Stations({ stations }: { stations: StationSnapshot[] }) {
  return (
    <>
      {stations.map((gs) => {
        const color = gs.on_download ? "red" : gs.on_upload ? "blue" : "#ffeccf";
        return (
          <mesh
            key={gs.id}
            position={[
              gs.pos.x * SCALE,
              gs.pos.y * SCALE,
              gs.pos.z * SCALE,
            ]}
          >
            <sphereGeometry args={[10, 32, 32]} />
            <meshBasicMaterial color={color} />
            <Html distanceFactor={5000} position={[0, 0, 0]}>
              <div
                className="select-none w-20"
                style={{
                  color: "white",
                  fontWeight: 200,
                  fontSize: 10,
                  padding: "1px 4px",
                }}
              >
                GS-{gs.id.slice(-6)}
              </div>
            </Html>
          </mesh>
        );
      })}
    </>
  );
}

export function RoIs({ rois }: { rois: ROISnapshot[] }) {
  return (
    <>
      {rois.map((roi) => {
        // 生成 RoI 区域的四个角点
        const cor = roi.corners_pos;
        if (!Array.isArray(cor) || cor.length !== 4) return null;

        // 生成顶点坐标
        const points = cor.map((c) => [c.x * SCALE, c.y * SCALE, c.z * SCALE]);
        // 闭合多边形
        const cen = roi.centre_pos;

        // 线条颜色
        const color = 0x00ff00;

        return (
          <group key={roi.id}>
            {/* 绘制 RoI 区域顶点 */}
            {points.length === 4 && (
              <mesh>
                <bufferGeometry
                  attach="geometry"
                  args={undefined}
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
                  color={color}
                  transparent
                  opacity={1} // 半透明
                  side={THREE.DoubleSide}
                />
                <mesh position={[cen.x * SCALE, cen.y * SCALE, cen.z * SCALE]}>
                  <sphereGeometry args={[10, 16, 16]} />
                  <meshBasicMaterial color={color} />
                </mesh>
              </mesh>
            )}
            <Html
              distanceFactor={5000}
              position={[
                roi.centre_pos.x * SCALE,
                roi.centre_pos.y * SCALE,
                roi.centre_pos.z * SCALE,
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
            </Html>
          </group>
        );
      })}
    </>
  );
}

export function Links({ links }: { links: LinkSnapshot[] }) {
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
              opacity={0.8}
            />
          </line>
        );
      })}
    </>
  );
}
