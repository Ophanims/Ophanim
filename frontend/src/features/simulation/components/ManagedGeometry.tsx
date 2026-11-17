import { useEffect } from "react";
import type { BufferGeometry, Object3D } from "three";
import { Line, Mesh } from "three";

export function ManagedGeometry({ geometry }: { geometry: BufferGeometry }) {
  useEffect(() => () => geometry.dispose(), [geometry]);
  return <primitive object={geometry} attach="geometry" />;
}
export function ManagedObject({ object }: { object: Object3D }) {
  useEffect(() => () => object.traverse((child) => {
    if (child instanceof Mesh || child instanceof Line) {
      child.geometry.dispose();
      const materials = Array.isArray(child.material) ? child.material : [child.material];
      materials.forEach((material) => material.dispose());
    }
  }), [object]);
  return <primitive object={object} />;
}
