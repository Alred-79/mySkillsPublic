import * as THREE from 'three';

export const glowMaterial = new THREE.ShaderMaterial({
  uniforms: {
    uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
    uColor: { value: new THREE.Color('#9fe8d0') },
  },
  vertexShader: /* glsl */ `
    varying vec3 vNormal;
    void main() {
      vNormal = normalize(normalMatrix * normal);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: /* glsl */ `
    uniform vec2 uResolution;
    uniform vec3 uColor;
    varying vec3 vNormal;
    void main() {
      vec2 uv = gl_FragCoord.xy / uResolution;
      float rim = pow(1.0 - abs(vNormal.z), 2.0);
      gl_FragColor = vec4(uColor * (0.6 + rim) * (0.8 + 0.2 * uv.y), 1.0);
    }
  `,
});
