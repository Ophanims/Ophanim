import { ManagedGeometry, ManagedObject } from "../../components/ManagedGeometry";
import {
EarthSnapshot,
LinkSnapshot,
ROISnapshot,
SatelliteSnapshot,
StationSnapshot
} from "@/features/simulation/types/simulation";
import { useLoader } from "@react-three/fiber";
import React,{
useMemo
} from "react";
import * as THREE from "three";
import { TextureLoader } from "three";
import { EARTH_DISPLAY_RADIUS_P,SCALE } from "../../lib/DefaultObjects";
import { create_latitude_line,create_longitude_line } from "./ObjectPrimitivesGrid";
export function invert_texture(texture: THREE.Texture) {
  if (!(texture.image instanceof HTMLImageElement)) return texture;
  const canvas = document.createElement("canvas");
  canvas.width = texture.image.width;
  canvas.height = texture.image.height;
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(texture.image, 0, 0);
  const img_data = ctx.getImageData(0, 0, canvas.width, canvas.height);
  for (let i = 0; i < img_data.data.length; i += 4) {
    // 反相灰度
    const gray = img_data.data[i]; // R=G=B
    const inv = 255 - gray;
    img_data.data[i] = inv;
    img_data.data[i + 1] = inv;
    img_data.data[i + 2] = inv;
    // alpha不变
  }
  ctx.putImageData(img_data, 0, 0);
  const new_texture = new THREE.Texture(canvas);
  new_texture.needsUpdate = true;
  return new_texture;
}

export function Earth({
  earth,
  earth_ref,
}: {
  earth: EarthSnapshot;
  earth_ref: React.RefObject<THREE.Object3D>;
}) {
  const texture = useLoader(TextureLoader, "/planet_texture/earth_obj_texture.png");
  // const defaultRotationY = 3.01;
  const default_rotation_y = 3.14;



  // 经纬线组
  const grid_group = useMemo(() => {
    const group = new THREE.Group();
    group.name = "LatLonIndicator";

    const radius = EARTH_DISPLAY_RADIUS_P + 10; // slightly above surface
    const segments = 256;

    // 纬线（Latitude circles）
    for (let lat = -90; lat <= 90; lat += 10) {
      const is_equator = lat === 0;
      const color = is_equator ? 0xffffff : 0x2b2b2b;
      const width = is_equator ? 2 : 1;
      const line = create_latitude_line(radius, lat, segments, color, width);
      group.add(line);
    }

    // 经线（Longitude meridians）
    for (let lon = -180; lon <= 180; lon += 10) {
      const line = create_longitude_line(radius, lon, segments, 0x2b2b2b, 1);
      group.add(line);
    }

    return group;
  }, []);

  return (
    <group>
      <mesh rotation={[Math.PI / 2, earth.rotation + default_rotation_y, 0]}>
        <sphereGeometry args={[EARTH_DISPLAY_RADIUS_P * 1.04, 64, 64]} />
        <meshBasicMaterial
          color={0x4b4b4b}
          transparent
          opacity={0}
          depthWrite={false}
        />
      </mesh>
      {/* 经纬线与地球同轴、同自转 */}
      <group rotation={[Math.PI / 2, earth.rotation + default_rotation_y, 0]}><ManagedObject object={grid_group} /></group>
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

export function Satellites({
  satellites,
  plane_color_map,
}: {
  satellites: SatelliteSnapshot[];
  earth_ref: React.RefObject<THREE.Object3D>;
  plane_color_map: Map<number, string>;
}) {
  return (
    <>
      {satellites.map((sat) => {
        const color = plane_color_map.get(Number(sat.plane)) ?? `hsl(0, 0%, 80%)`; // 假设图像颜色为黄色
        // 新增：使用dimensions设置卫星大小（假设单位m，缩放以匹配场景）
        const pj_color =
          plane_color_map.get(Number(sat.plane)) ?? `hsl(0, 0%, 80%)`; // 假设图像颜色为黄色
        const img_color =
          plane_color_map.get(Number(sat.plane)) ?? `hsl(0, 0%, 80%)`; // 假设图像颜色为黄色
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
                    color: labelColor,
                    fontWeight: 200,
                    fontSize: 20,
                    padding: "1px 4px",
                  }}
                >
                  <span>S {sat.plane}-{sat.order}</span>
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

export function Stations({
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

export function build_plane_color_map(satellites: SatelliteSnapshot[]) {
  const by_plane = new Map<number, SatelliteSnapshot[]>();
  satellites.forEach((s) => {
    const p = s.plane;
    by_plane.set(p, [...(by_plane.get(p) || []), s]);
  });
  const plane_ids = Array.from(by_plane.keys()).sort((a, b) => a - b);
  const plane_color_map = new Map<number, string>();
  plane_ids.forEach((pid, idx) => {
    const hue = (idx / Math.max(1, plane_ids.length)) * 360;
    plane_color_map.set(pid, `hsl(${Math.round(hue)}, 70%, 55%)`);
  });
  return { by_plane, plane_ids, plane_color_map };
}

export function Links({
  links,
  plane_color_map,
}: {
  links: LinkSnapshot[];
  plane_color_map: Map<number, string>;
}) {
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
        const src_plane = link.src.split("-")[1];
        const dst_plane = link.dst.split("-")[1];
        let color;
        if (src_plane === dst_plane) {
          // 同一平面，使用平面颜色
          color = plane_color_map.get(Number(src_plane)) ?? "white";
        } else color = link.type === "ISL" ? "white" : "red";
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
              opacity={1}
            />
          </line>
        );
      })}
    </>
  );
}

export function OrbitRings({
  satellites,
  plane_color_map,
}: {
  satellites: SatelliteSnapshot[];
  plane_color_map: Map<number, string>;
}) {
  const rings = useMemo(() => {
    // 按 plane 分组
    const by_plane = new Map<number, SatelliteSnapshot[]>();
    satellites.forEach((s) => {
      const p = s.plane;
      by_plane.set(p, [...(by_plane.get(p) || []), s]);
    });
    const plane_ids = Array.from(by_plane.keys()).sort((a, b) => a - b);

    return plane_ids.map((pid) => {
      const sats = by_plane.get(pid)!;
      const positions = sats.map((s) =>
        new THREE.Vector3(s.pos.x, s.pos.y, s.pos.z).multiplyScalar(SCALE)
      );

      // 平面法向：用相邻向量的叉积累加并归一化
      let normal = new THREE.Vector3(0, 0, 1);
      if (positions.length >= 2) {
        const n = new THREE.Vector3();
        for (let i = 0; i < positions.length; i++) {
          const a = positions[i].clone().normalize();
          const b = positions[(i + 1) % positions.length].clone().normalize();
          n.add(new THREE.Vector3().crossVectors(a, b));
        }
        if (n.lengthSq() > 1e-8) normal = n.normalize();
      }

      // 半径：取该平面卫星到地心的平均距离
      const radius =
        positions.reduce((acc, v) => acc + v.length(), 0) /
        Math.max(1, positions.length);

      // 在 XY 平面生成圆点，然后旋转到法向 normal 所在平面
      const segments = 256;
      const pts: THREE.Vector3[] = [];
      const q = new THREE.Quaternion().setFromUnitVectors(
        new THREE.Vector3(0, 0, 1),
        normal
      );
      for (let i = 0; i <= segments; i++) {
        const ang = (i / segments) * Math.PI * 2;
        const p = new THREE.Vector3(
          Math.cos(ang) * radius,
          Math.sin(ang) * radius,
          0
        );
        pts.push(p.applyQuaternion(q));
      }

      const geometry = new THREE.BufferGeometry().setFromPoints(pts);
      // 颜色取自 planeColorMap，确保与卫星标签一致
      const color = plane_color_map.get(Number(pid)) ?? `hsl(0, 0%, 80%)`;

      return { key: `orbit-plane-${pid}`, geometry, color };
    });
  }, [satellites, plane_color_map]);

  return (
    <>
      {rings.map((r) => (
        <line key={r.key}>
          <ManagedGeometry geometry={r.geometry} />
          <lineBasicMaterial
            attach="material"
            color={r.color}
            transparent
            opacity={0.6}
          />
        </line>
      ))}
    </>
  );
}
