import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import Bottle from './Bottle.jsx';
import ScrollCamera from './ScrollCamera.jsx';
import TiltCard from './TiltCard.jsx';
import Badge from './Badge.jsx';

export default function App() {
  return (
    <>
      <section className="stage">
        <Canvas dpr={window.devicePixelRatio} frameloop="demand" camera={{ position: [0, 1, 6], fov: 75 }} shadows>
          <ambientLight intensity={0.5} />
          <directionalLight position={[5, 5, 5]} intensity={1} castShadow />
          <Bottle />
          <mesh name="fadeTarget" position={[0, 0.5, -4]}>
            <planeGeometry args={[14, 7]} />
            <meshBasicMaterial color="#1c2a25" />
          </mesh>
          <mesh rotation-x={-Math.PI / 2} position-y={-1.5} receiveShadow>
            <planeGeometry args={[20, 20]} />
            <meshStandardMaterial color="#888" />
          </mesh>
          <OrbitControls enableDamping />
          <ScrollCamera />
          <EffectComposer>
            <Bloom luminanceThreshold={0} intensity={1.5} />
          </EffectComposer>
        </Canvas>
      </section>
      <section className="story">
        <h2>Carried up 1,200 meters</h2>
        <p>Fjell bottles are tested on the Besseggen ridge before they ship.</p>
        <TiltCard />
        <Badge />
      </section>
    </>
  );
}
