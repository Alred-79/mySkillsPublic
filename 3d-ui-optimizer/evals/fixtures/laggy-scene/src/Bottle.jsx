import { useMemo, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import { glowMaterial } from './glowMaterial.js';

export default function Bottle() {
  const ref = useRef();
  const capRef = useRef();
  const [t, setT] = useState(0);

  const geometry = useMemo(() => new THREE.CapsuleGeometry(0.6, 2, 8, 32), []);
  const material = useMemo(() => new THREE.MeshStandardMaterial({ color: '#2f6f5e', roughness: 0.35 }), []);

  useFrame((state, delta) => {
    setT(state.clock.elapsedTime);
    ref.current.position.lerp(new THREE.Vector3(0, Math.sin(state.clock.elapsedTime) * 0.1, 0), 0.1);
    capRef.current.rotation.y = THREE.MathUtils.damp(capRef.current.rotation.y, t * 0.5, 4, delta);
  });

  return (
    <group ref={ref}>
      <mesh geometry={geometry} material={material} castShadow />
      <mesh ref={capRef} position-y={1.75} material={glowMaterial}>
        <cylinderGeometry args={[0.35, 0.35, 0.4, 32]} />
      </mesh>
      <Html position={[1.2, 0.8, 0]} className="price">
        <span>Fjell 750 ml, 449 kr</span>
      </Html>
    </group>
  );
}
