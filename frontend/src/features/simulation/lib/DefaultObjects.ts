import * as THREE from "three";
import { LayerMode } from "./modes";

export const EARTH_RADIUS_METERS = 6356752;
export const EARTH_DISPLAY_RADIUS_P = 6356.752;
export const EARTH_DISPLAY_RADIUS_E = 6378.137;
export const OFFSET = 0.5;  // 线稍微抬高
export const SCALE = EARTH_DISPLAY_RADIUS_P / EARTH_RADIUS_METERS;

function create_latitude_line(
    radius: number,
    lat_deg: number,
    segments: number = 256,
    color: number = 0xffffff,
    opacity: number = 1
): THREE.LineLoop {
    const positions: number[] = [];
    const lat_rad = THREE.MathUtils.degToRad(lat_deg);
    const y = radius * Math.sin(lat_rad);
    const r = radius * Math.cos(lat_rad);

    for (let i = 0; i <= segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        const x = r * Math.cos(theta);
        const z = r * Math.sin(theta);
        positions.push(x, y, z);
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(positions, 3)
    );

    const material = new THREE.LineBasicMaterial({
        color,
        linewidth: 2,
        transparent: opacity < 1,
        opacity,
    });

    return new THREE.LineLoop(geometry, material);
}

function create_longitude_line(
    radius: number,
    lon_deg: number,
    segments: number = 256,
    color: number = 0xffffff,
    opacity: number = 1
): THREE.Line {
    const positions: number[] = [];
    const lon_rad = THREE.MathUtils.degToRad(lon_deg);

    for (let i = 0; i <= segments; i++) {
        const lat_rad = THREE.MathUtils.degToRad(-90 + (i / segments) * 180);
        const x = radius * Math.cos(lat_rad) * Math.cos(lon_rad);
        const y = radius * Math.sin(lat_rad);
        const z = radius * Math.cos(lat_rad) * Math.sin(lon_rad);
        positions.push(x, y, z);
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(positions, 3)
    );

    const material = new THREE.LineBasicMaterial({
        color,
        linewidth: 1,
        transparent: opacity < 1,
        opacity,
    });

    return new THREE.Line(geometry, material);
}


/**
 * 创建地球及经纬线
 */
export async function create_earth(
    active_layer: LayerMode,
): Promise<THREE.Group> {
    let material: THREE.MeshStandardMaterial; // 这样声明即可，后续保证必定赋值

    let show_grid = false;           // 是否显示经纬线

    if (active_layer === LayerMode.MATERIAL) {
        // 贴图，完全不透明，无经纬线
        const loader = new THREE.TextureLoader();
        const texture: THREE.Texture = await new Promise((resolve, reject) => {
            loader.load(
                "/planet_texture/earth_texture.jpg",
                resolve,
                undefined,
                reject
            );
        });
        material = new THREE.MeshStandardMaterial({
            map: texture,
            roughness: 0.9,
            metalness: 0.1,
            transparent: false,
            opacity: 1.0,
        });
    } else if (active_layer === LayerMode.WIREFRAME) {
        // 仅显示线框，球体透明度10%，不加载贴图
        material = new THREE.MeshStandardMaterial({
            map: null,
            color: 0x000000,
            roughness: 0.9,
            metalness: 0.1,
            transparent: true,
            opacity: 0, // 10% 不透明
        });
        show_grid = true;
    } else {
        // SolidMesh: 只显示球体
        material = new THREE.MeshStandardMaterial({
            map: null,
            color: 0x000000,
            roughness: 0.9,
            metalness: 0.1,
            transparent: true,
            opacity: 0.3, // 30% 不透明
        });
    }

    const geometry = new THREE.SphereGeometry(6371 - OFFSET, 64, 64);
    // const geometry = new THREE.SphereGeometry(1, 64, 64);
    const earth = new THREE.Mesh(geometry, material);
    // earth.scale.set(EARTH_DISPLAY_RADIUS_E, EARTH_DISPLAY_RADIUS_P, EARTH_DISPLAY_RADIUS_E);
    earth.name = "Earth";

    const group = new THREE.Group();
    group.name = "EarthWithLines";
    group.add(earth);

    // 经纬线组
    const grid_group = new THREE.Group();
    grid_group.name = "LatLonIndicator";
    grid_group.visible = show_grid;

    if (show_grid) {
        // 纬线
        for (let lat = -90; lat <= 90; lat += 10) {
            const is_equator = lat === 0;
            grid_group.add(create_latitude_line(
                EARTH_DISPLAY_RADIUS_P + OFFSET,
                lat,
                256,
                is_equator ? 0xff0000 : 0x2b2b2b,
                1
            ));
        }
        // 经线
        for (let lon = -180; lon <= 180; lon += 10) {
            grid_group.add(create_longitude_line(
                EARTH_DISPLAY_RADIUS_P + OFFSET,
                lon,
                256,
                0x2b2b2b,
                1
            ));
        }
    }

    group.add(grid_group);
    group.position.set(0, 0, 0);
    return group;
}