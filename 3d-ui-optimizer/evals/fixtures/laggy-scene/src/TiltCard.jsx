import { useRef } from 'react';

export default function TiltCard() {
  const ref = useRef();
  const onMove = (e) => {
    const r = ref.current.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    ref.current.style.transform = `perspective(1000px) rotateX(${-y * 12}deg) rotateY(${x * 12}deg)`;
  };
  return (
    <div ref={ref} className="tilt" onPointerMove={onMove}>
      <div className="tilt-photo" role="img" aria-label="The Besseggen ridge at dawn" />
      <div className="tilt-label">Tested on Besseggen</div>
    </div>
  );
}
