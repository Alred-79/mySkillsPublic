import { useEffect } from 'react';
import { useThree } from '@react-three/fiber';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

export default function ScrollCamera() {
  const camera = useThree((s) => s.camera);
  const scene = useThree((s) => s.scene);

  useEffect(() => {
    const tween = gsap.to(camera.position, {
      x: 3,
      y: 2,
      z: 4,
      scrollTrigger: {
        trigger: '.story',
        start: 'top bottom',
        end: 'bottom top',
        scrub: 1,
        onUpdate: () => camera.lookAt(0, 0, 0),
      },
    });

    const fade = scene.getObjectByName('fadeTarget');
    if (fade) {
      fade.material.transparent = true;
      gsap.to(fade.material, { opacity: 0.4, duration: 0.6 });
    }

    return () => tween.scrollTrigger.kill();
  }, [camera, scene]);

  return null;
}
