import { ManagedGeometry } from "../../components/ManagedGeometry";
import ClockWidget from "@/features/simulation/components/ClockWidget";
import VoidPage from "@/features/simulation/components/VoidPage";
import {
LinkSnapshot,
SatelliteSnapshot,
StationSnapshot,
TaskSnapshot,
} from "@/features/simulation/types/simulation";
import { Html,OrbitControls } from "@react-three/drei";
import { Canvas,useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";
import { SCALE } from "../../lib/DefaultObjects";
import { useFrames } from "../workspace/useFramesContext";


function SatDataNode({ sat }: { sat: SatelliteSnapshot }) {
  const mesh_ref = useRef<THREE.Mesh>(null!);

  useFrame(() => {
    if (mesh_ref.current) {
      const { x, y, z } = sat.pos;
      mesh_ref.current.position.set(x * SCALE, y * SCALE, z * SCALE);
      const size = 1;
      mesh_ref.current.scale.set(size, size, size);
    }
  });

  const color = "#ffffff";

  return (
    <mesh ref={mesh_ref}>
      <sphereGeometry args={[5, 16, 16]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={2}
      />
      {/* <Html distanceFactor={5000} position={[0, 0, 0]}>
        <div
          className="select-none flex flex-col w-20 items-center"
          style={{
            color: sat.onGS
              ? "red"
              : sat.attnHead || ratio > 0
              ? "white"
              : "#333",
            fontWeight: 200,
            fontSize: 10,
            padding: "1px 4px",
          }}
        >
          <span>SAT-{sat.id.slice(-6)}</span>
          <span>{ratio.toFixed(4)}</span>
        </div>
      </Html> */}
    </mesh>
  );
}
function TaskDataNode({ sat, task }: { sat: SatelliteSnapshot; task: TaskSnapshot }) {
  const mesh_ref = useRef<THREE.Mesh>(null!);
  const ratio = 1 - task.completion;

  useFrame(() => {
    if (mesh_ref.current) {
      const { x, y, z } = sat.pos;
      mesh_ref.current.position.set(x * SCALE, y * SCALE, z * SCALE);
      const size = THREE.MathUtils.clamp(
        ratio * 5000,
        sat.is_processing ? 1 : 0,
        80 * (1 - task.data_percent * 0.6)
      );
      mesh_ref.current.scale.set(size, size, size);
    }
  });

  const color = get_color_from_id(task.id);

  return (
    <mesh ref={mesh_ref}>
      <sphereGeometry args={[5, 16, 16]} />
      <meshStandardMaterial
        color={color}
        transparent
        opacity={1}
        emissive={color}
        emissiveIntensity={1}
      />
      <Html position={[0, 0, 0]}>
        <div className="select-none px-3 py-1 w-20 items-center bg-black/50 rounded-md text-sm">
          <span>Task {task.id}</span>
        </div>
      </Html>
    </mesh>
  );
}

function GsDataNode({ gs }: { gs: StationSnapshot }) {
  const mesh_ref = useRef<THREE.Mesh>(null!);
  const ratio = 1;

  useFrame(() => {
    if (mesh_ref.current) {
      const { x, y, z } = gs.pos;
      mesh_ref.current.position.set(x * SCALE, y * SCALE, z * SCALE);
      const size = THREE.MathUtils.clamp(
        ratio * 5000,
        Number(gs.on_upload) ? 1 : 0,
        10
      );
      mesh_ref.current.scale.set(size, size, size);
    }
  });

  const color = gs.on_download ? "red" : gs.on_upload ? "blue" : "#ffffff";

  return (
    <mesh ref={mesh_ref}>
      <sphereGeometry args={[5, 16, 16]} />
      <meshStandardMaterial
        color={color}
        transparent
        opacity={1}
        emissive={color}
        emissiveIntensity={1}
      />
      <Html position={[0, 0, 0]}>
        <div
          className="select-none flex flex-col w-20 items-center"
          style={{
            color: gs.on_download ? "red" : "white",
            fontWeight: 200,
            fontSize: 10,
            padding: "1px 4px",
          }}
        >
          <span>GS-{gs.id.slice(-5)}</span>
          {/* <span>{ratio.toFixed(4)}</span> */}
        </div>
      </Html>
    </mesh>
  );
}

function DataFlowScene({
  satellites,
  stations,
  links,
  tasks,
}: {
  satellites: SatelliteSnapshot[];
  stations: StationSnapshot[];
  links: LinkSnapshot[];
  tasks: TaskSnapshot[];
}) {
  return (
    <Canvas
      camera={{ position: [0, 0, 28000], fov: 30, near: 1000, far: 100000 }}
    >
      <ambientLight intensity={0.5} />
      <pointLight position={[5, 5, 5]} intensity={1.5} />
      <OrbitControls />
      <group rotation={[-Math.PI / 2, 0, 0]}>
        {satellites.map((sat) => (
          <SatDataNode key={sat.id} sat={sat} />
        ))}
        {tasks.map((t) => {
          if (t.is_done) return null;
          const sat = satellites.find(
            (s) => s.plane === t.plane_at && s.order === t.order_at
          );
          if (!sat) return null;
          // console.log("Rendering task:", t.id, "on sat:", sat.id);
          const act = Number(t.acted);
          if ([1, 2, 3, 4].includes(act) === false) {
            if (sat) return <TaskDataNode key={t.id} sat={sat} task={t} />;
            return null;
          }
          let target_plane = t.plane_at;
          let target_order = t.order_at;
          switch (act) {
            case 1:
              target_plane++;
              break;
            case 2:
              target_plane--;
              break;
            case 3:
              target_order++;
              break;
            default:
              target_order--;
              break;
          }
          const tar = satellites.find(
            (s) => s.plane === target_plane && s.order === target_order
          );

          let arrow_el = null;
          if (tar) {
            const start_vec = new THREE.Vector3(
              sat.pos.x,
              sat.pos.y,
              sat.pos.z
            ).multiplyScalar(SCALE);
            const end_vec = new THREE.Vector3(
              tar.pos.x,
              tar.pos.y,
              tar.pos.z
            ).multiplyScalar(SCALE);

            const dir = new THREE.Vector3().subVectors(end_vec, start_vec);
            const dist = dir.length();
            const dir_norm = dir.clone().normalize();

            // --- cone size ---
            const cone_height = Math.min(1000, Math.max(60, dist * 0.1));
            const cone_radius = cone_height * 0.2;

            // --- short line: length = 1/2 of full distance ---
            const line_length = dist * t.data_percent;
            const cylinder_radius = Math.max(8, dist * 0.008); // 控制粗细
            const cyl_pos = start_vec
              .clone()
              .add(dir_norm.clone().multiplyScalar(line_length * 0.5));
            const cyl_height = line_length;

            // quaternion 从 +Y 轴指向 dirNorm（用于 cylinder 和 cone）
            const q = new THREE.Quaternion().setFromUnitVectors(
              new THREE.Vector3(0, 1, 0),
              dir_norm
            );

            // 把箭头放在目标方向但离目标一点（避免与 cylinder 相撞）
            const cone_pos = start_vec
              .clone()
              .add(
                dir_norm.clone().multiplyScalar(line_length + cone_height * 0.5)
              );

            const color = get_color_from_id(t.id);
            const trans = 1;

            arrow_el = (
              <group key={`arrow-${t.id}`}>
                {/* 粗线用 cylinder 实现 */}
                <mesh position={[cyl_pos.x, cyl_pos.y, cyl_pos.z]} quaternion={q}>
                  <cylinderGeometry
                    args={[cylinder_radius, cylinder_radius, cyl_height, 12]}
                  />
                  <meshStandardMaterial
                    color={color}
                    emissive={color}
                    transparent
                    opacity={trans}
                  />
                </mesh>

                {/* 箭头锥体，放在 cylinder 末端外侧 */}
                <mesh
                  position={[cone_pos.x, cone_pos.y, cone_pos.z]}
                  quaternion={q}
                >
                  <coneGeometry args={[cone_radius, cone_height, 8]} />
                  <meshStandardMaterial
                    color={color}
                    emissive={color}
                    transparent
                    opacity={trans}
                  />
                </mesh>
              </group>
            );
          }

          return (
            <group key={`task-${t.id}`}>
              <TaskDataNode sat={sat} task={t} />
              {arrow_el}
            </group>
          );
        })}
        {stations.map((gs) => (
          <GsDataNode key={gs.id} gs={gs} />
        ))}
        {links.map((link, i) => {
          const [start, end] = link.link_pos;
          const start_vec = new THREE.Vector3(
            start.x,
            start.y,
            start.z
          ).multiplyScalar(1 * SCALE);
          const end_vec = new THREE.Vector3(end.x, end.y, end.z).multiplyScalar(
            1 * SCALE
          );
          const geometry = new THREE.BufferGeometry().setFromPoints([
            start_vec,
            end_vec,
          ]);

          // 计算线段中点
          const link_color = link.type === "ISL" ? "#ffffff" : "red";
          return (
            <line key={i}>
              <ManagedGeometry geometry={geometry} />
              <lineBasicMaterial
                attach="material"
                transparent
                opacity={0.2}
                color={link_color}
                linewidth={2}
              />
              {/* <Html distanceFactor={1} position={[midVec.x, midVec.y, midVec.z]}>
              <div
                className="select-none w-20"
                style={{
                  color: "white",
                  fontWeight: 200,
                  fontSize: 5,
                  padding: "1px 4px",
                }}
              >
                {link.rate.toFixed(2)} bps
              </div>
            </Html> */}
            </line>
          );
        })}
      </group>
    </Canvas>
  );
}

export default function DataFlowPanel() {
  const { frames, selected_frame_index } = useFrames();
  const frame = frames[selected_frame_index];
  if (!frame) return <VoidPage />;
  return <div className="relative h-full w-full bg-black text-white">
    <div className="absolute top-2 right-0 z-10"><ClockWidget frame_counter={frame.frame_counter} time={frame.time} /></div>
    {(frame.info.is_terminated || frame.info.is_truncated) && <p className="absolute top-2 left-4 z-10">
      {frame.info.terminated_reason} · reward: {frame.info.reward.toFixed(2)}
    </p>}
    <DataFlowScene satellites={frame.satellites} stations={frame.stations} links={frame.links} tasks={frame.tasks} />
  </div>;
}

function get_color_from_id(id: string | number) {
  const s = String(id);
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h << 5) - h + s.charCodeAt(i);
    h |= 0;
  }
  // 用常数乘并取无符号值再 mod 360，能把相邻输入扩散到不同 hue
  const hue = Math.abs(((h * 2654435761) >>> 0) % 360);
  return `hsl(${hue}, 70%, 50%)`;
}
