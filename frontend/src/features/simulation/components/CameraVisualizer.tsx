import { Box,Html,Line } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";

export default function CameraVisualizer({
  focal_length_mm = 64, // 单位：mm，假定焦距
  width_px = 4096,
  length_px = 4096,
  px_size_length = 5.5, // μm
  px_size_width = 5.5, // μm
  h = 500000, // 卫星高度，单位：m
}: {
  focal_length_mm?: number | null;
  width_px?: number | null;
  length_px?: number | null;
  px_size_length?: number | null;
  px_size_width?: number | null;
  h?: number | null;
}) {
  if (focal_length_mm === null || width_px === null || length_px === null || px_size_length === null || px_size_width === null || h === null) {
    return <p className="text-sm text-white/60">Complete the camera parameters to preview coverage.</p>;
  }
  // 计算传感器尺寸（mm）
  const sensor_w = width_px * px_size_width * 0.001;
  const sensor_l = length_px * px_size_length * 0.001;

  // 计算 FOV（弧度）
  const fov_w = 2 * Math.atan(sensor_w / (2 * focal_length_mm));
  const fov_l = 2 * Math.atan(sensor_l / (2 * focal_length_mm));

  // 地面投影宽度和长度（m）
  const swath_w = 2 * h * Math.tan(fov_w / 2);
  const swath_l = 2 * h * Math.tan(fov_l / 2);
  const gsd = (swath_w / width_px + swath_l / length_px) / 2; // m/pixel

  // 三维可视化参数缩放
  const R = 0.0003;
  const r = 0.5;

  const sat_pos: [number, number, number] = [0, 0, 0];
  const plane_pos: [number, number, number] = [0, focal_length_mm * r, 0];
  const ground_pos: [number, number, number] = [0, -h * R, 0];

  // 成像面四角（朝上，Y轴为法线）
  const plane_corners: [number, number, number][] = [
    [
      plane_pos[0] + (sensor_w * r) / 2,
      plane_pos[1],
      plane_pos[2] + (sensor_l * r) / 2,
    ],
    [
      plane_pos[0] - (sensor_w * r) / 2,
      plane_pos[1],
      plane_pos[2] + (sensor_l * r) / 2,
    ],
    [
      plane_pos[0] - (sensor_w * r) / 2,
      plane_pos[1],
      plane_pos[2] - (sensor_l * r) / 2,
    ],
    [
      plane_pos[0] + (sensor_w * r) / 2,
      plane_pos[1],
      plane_pos[2] - (sensor_l * r) / 2,
    ],
  ];
  // 地面影像四角（朝上，Y轴为法线）
  const ground_corners: [number, number, number][] = [
    [
      ground_pos[0] + (swath_w * R) / 2,
      ground_pos[1],
      ground_pos[2] + (swath_l * R) / 2,
    ],
    [
      ground_pos[0] - (swath_w * R) / 2,
      ground_pos[1],
      ground_pos[2] + (swath_l * R) / 2,
    ],
    [
      ground_pos[0] - (swath_w * R) / 2,
      ground_pos[1],
      ground_pos[2] - (swath_l * R) / 2,
    ],
    [
      ground_pos[0] + (swath_w * R) / 2,
      ground_pos[1],
      ground_pos[2] - (swath_l * R) / 2,
    ],
  ];

  return (
    <Canvas camera={{ position: [500, -200, 200], fov: 20 }}>
      <group position={[0, (h * R) / 2, 0]}>
        <mesh position={sat_pos}>
          <sphereGeometry args={[0.5, 16, 16]} />
          <meshStandardMaterial
            color="white"
            emissive="#ffffff"
            emissiveIntensity={2}
          />
        </mesh>
        {/* 成像面（蓝色） */}
        <Box args={[sensor_w * r, 0.2, sensor_l * r]} position={plane_pos}>
          <meshStandardMaterial color="#3399ff" opacity={0.5} transparent />
        </Box>
        {/* 地面影像（红色） */}
        <Box args={[swath_w * R, 0.2, swath_l * R]} position={ground_pos}>
          <meshStandardMaterial color="#ff3333" opacity={0.5} transparent />
        </Box>
        {/* 卫星到成像面四角的线 */}
        {plane_corners.map((corner, i) => (
          <Line
            key={`sat-plane-${i}`}
            points={[sat_pos, corner]}
            color="#fff"
            lineWidth={0.5}
          />
        ))}
        {/* 卫星到地面影像四角的线 */}
        {ground_corners.map((corner, i) => (
          <Line
            key={`sat-ground-${i}`}
            points={[sat_pos, corner]}
            color="#fff"
            lineWidth={0.5}
          />
        ))}
        {/* 成像面四边框 */}
        <Line
          points={[...plane_corners, plane_corners[0]]}
          color="#3399ff"
          lineWidth={0.5}
        />
        {/* 地面影像四边框 */}
        <Line
          points={[...ground_corners, ground_corners[0]]}
          color="#ff3333"
          lineWidth={0.5}
        />

        <Html position={sat_pos}>
          <div className="w-40" style={{ color: "#ffffff" }}>
            <p className="text-xs">
              FoV-Width: {((fov_w * 180) / Math.PI).toFixed(2)}°
            </p>
            <p className="text-xs">
              FoV-Length: {((fov_l * 180) / Math.PI).toFixed(2)}°
            </p>
            <p className="text-xs">GSD: {gsd.toFixed(2)} m/pixel</p>
          </div>
        </Html>
        <Html position={plane_pos}>
          <div className="w-40" style={{ color: "#3399ff" }}>
            <p className="text-sm">Imaging Plane</p>
            <p className="text-xs">w: {sensor_w.toFixed(1)} mm</p>
            <p className="text-xs">l: {sensor_l.toFixed(1)} mm</p>
          </div>
        </Html>
        <Html position={ground_pos}>
          <div className="w-40" style={{ color: "#ff3333" }}>
            <p className="text-sm">Ground Coverage</p>
            <p className="text-xs">W: {swath_w.toFixed(1)} m</p>
            <p className="text-xs">L: {swath_l.toFixed(1)} m</p>
          </div>
        </Html>
        <ambientLight intensity={0.8} />
      </group>
    </Canvas>
  );
}
