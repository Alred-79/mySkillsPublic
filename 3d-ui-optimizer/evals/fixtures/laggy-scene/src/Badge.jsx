import { Canvas, useFrame } from '@react-three/fiber';
import { useRef } from 'react';

function Spinner() {
  const ref = useRef();
  useFrame((_, delta) => (ref.current.rotation.y += delta * 0.8));
  return (
    <mesh ref={ref}>
      <icosahedronGeometry args={[1, 0]} />
      <meshNormalMaterial />
    </mesh>
  );
}

// A small spinning badge next to the story copy.
export default function Badge() {
  return (
    <div className="badge">
      <Canvas camera={{ position: [0, 0, 3] }}>
        <Spinner />
      </Canvas>
    </div>
  );
}
