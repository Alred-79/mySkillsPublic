# 3D craft for Three.js and React Three Fiber

Load this when building or fixing a Three.js or R3F scene.
Rules were checked against the official R3F, drei, and react-postprocessing docs and against library source (R3F 9.8, drei 10.7, @react-three/postprocessing 3.2, three r175 to r182) in 2026-10, and the R3F seek pattern below was run.
Where the installed r3f, three, threejs-webgl, and react-three-fiber skills disagree with this file, prefer this file, and the last section says why. Re-check version-sensitive rows when a major version changes.

## Contents

- Art direction (the default look to replace)
- Budgets
- The frame loop
- Assets and GPU memory
- DOM integration and loading
- Device tiers and degradation
- Seeking an R3F scene
- Known-wrong advice in the installed skills

## Art direction

The default a model ships is fov 75, `ambientLight` 0.5, one directional light at 1, and a saturated MeshStandard object on a grey plane.
Those intensities were tuned for the pre-r155 lighting model, so under physical lights the scene renders dim and flat.
Replace each part.

| Part | Do this | Why |
|---|---|---|
| Light | Image-based lighting first, then one key light for shape. Self-host the HDR (`<Environment files>`) or build the environment from children at resolution 256. Art-direct with `environmentIntensity`, `environmentRotation`, `backgroundBlurriness` 0 to 1. | drei presets fetch from a CDN and are documented as not for production. Metals with no environment map render black. |
| Direct lights | If you add any, key, fill, and rim at about 3 to 1 to 0.5. Three lights or fewer. | Each light costs every fragment. |
| Tone mapping | Neutral for product and brand-accurate color, AgX for high-contrast light, ACES only when its hue shift is wanted. Never Linear on a lit scene. `flat` only for unlit or UI scenes. Without a composer, set it on the renderer (`gl={{ toneMapping: THREE.NeutralToneMapping }}`). With a react-postprocessing `<EffectComposer>`, the renderer setting is ignored, so put `<ToneMapping mode={ToneMappingMode.NEUTRAL} />` last in the chain. | R3F defaults to ACES, which shifts brand colors toward orange. @react-three/postprocessing forces `gl.toneMapping = NoToneMapping` while the composer is mounted, so a scene with a composer and no ToneMapping effect renders untonemapped and washed out. |
| Color space | `SRGBColorSpace` on color and emissive maps. Normal, roughness, metalness, and AO stay linear. Custom ShaderMaterials include `<tonemapping_fragment>` and `<colorspace_fragment>` so they match built-in materials when the renderer tone maps. Under a composer those includes are no-ops, and the ToneMapping effect handles every material at once. | R3F v9 no longer converts textures on custom materials. |
| Camera | fov 35 to 50 for objects and products, near as large and far as small as the scene allows. OrbitControls with damping 0.05, clamped distances, `maxPolarAngle` π/2, `enablePan` false for products. | fov 75 distorts objects and reads as a game viewport. |
| Grounding | ContactShadows with `frames={1}` for static objects, AccumulativeShadows, or a baked gradient plane. Never a real-time shadow map and ContactShadows together. | Real-time shadows on a grey plane are the stock look and cost a pass per caster. |
| Shadows | Directional or spot casters only. Map 512 to 1024 mobile, 1024 to 2048 desktop, 4096 for a hero still. Fit the shadow camera tightly. `shadowMap.autoUpdate = false` for static scenes. | A point light shadow renders six times. |
| Materials | Roughness 0.2 glossy, 0.5 plastic, 0.8 matte. Metalness 0 or 1. IOR glass 1.5, water 1.33. Clearcoat 1 at roughness 0.1 for paint. Prefer `alphaTest` or `alphaHash` over `transparent: true`. | In-between metalness reads as dirty plastic, and transparency brings sort artifacts. |
| Bloom | Selective by construction. `luminanceThreshold` 1, glowing materials set `toneMapped={false}` with emissive above 1. Intensity 0.5 to 2, radius 0.5 to 1. | Threshold 0, which several installed examples use, makes everything glow. |
| Postprocessing | pmndrs postprocessing, effects merged into one pass. Renderer with `antialias: false, stencil: false, depth: false` when a composer owns the frame. One AA strategy, so `multisampling={0}` when using SMAA. The `<ToneMapping>` effect last, then compare a still against a render without the composer. | Missing tone mapping under a composer is the classic washed-out bug. Rendering the composer at half resolution cuts its fragment cost by about four, so measure before and after. |
| Finish | Vignette offset 0.5 and darkness 0.5 as a start. Depth of field on hero stills only. Dither every smooth gradient. | DOF is expensive per frame, and banding is visible on 8-bit screens. |

## Budgets

| Measure | Target | Hard ceiling |
|---|---|---|
| Draw calls (`renderer.info.render.calls`) | about 100, under 50 on mobile-first pages | 1000 (R3F docs) |
| Triangles | under 100K mobile | 1M desktop |
| Hero model, compressed | under 500KB | 5MB, only for a dedicated configurator |
| Texture size | 1024 default, 512 for backgrounds | 2048 |
| GPU texture memory | 30 to 50MB mobile | 100 to 150MB desktop |
| Initial JS | under 150KB gzipped, so three and R3F (about 235KB gzipped together, measured with Vite 6, three 0.175, R3F 9.8) load in a lazy chunk | time to interactive under 3s |

With a composer, set `renderer.info.autoReset = false` and reset it per frame yourself, or you only count the last pass.
More than 100 textures or 500 geometries in `renderer.info.memory` is a leak signal.

## The frame loop

- Never call setState inside useFrame. Mutate refs, read stores with `getState()`.
- Never allocate inside useFrame. Hoist `Vector3`, `Color`, and `Matrix4` temporaries and reuse them with `.set()`.
- Move with `+= speed * delta`. Smooth with `damp` or `lerp(target, 1 - Math.exp(-λ * delta))` at λ 3 to 8, never a fixed 0.1 factor. Treat only outlier gaps (over about 0.25s) as one 60Hz frame, so slow devices keep real time instead of running in slow motion.
- Animate from your own accumulated time, not `state.clock.elapsedTime`. R3F's `setFrameloop` stops the clock and sets `elapsedTime` to 0 on every call, so a scene paused off screen snaps back to t=0 when it resumes. The seek pattern below keeps time in a ref.
- A positive useFrame priority turns off automatic rendering, so you must call `gl.render` yourself. Negative priorities only order callbacks.
- `frameloop="demand"` for anything static between interactions. Direct mutations then need `invalidate()`, and that includes every GSAP tween, called from the tween's `onUpdate`.
- PerformanceMonitor gives meaningless readings under demand mode, so use it only with the always loop.
- PerformanceMonitor with `flipflops={3}` and `onFallback` to lock a low tier. Never hardcode `bounds={() => [50, 90]}`, because a 60Hz screen can never reach 90 and quality never climbs back.
- Do not combine AdaptiveDpr with a PerformanceMonitor that drives a dpr state. They fight.
- Toggle `visible` instead of mounting and unmounting. Wrap expensive mounts in `startTransition`.
- Same geometry and material means InstancedMesh, then `computeBoundingSphere()` after `setMatrixAt` or culling breaks. Different geometries with one material means BatchedMesh. Static parts merge. drei `<Instances>` costs CPU, so use raw InstancedMesh past a few thousand.
- Raycasting runs only while the pointer moves, so call `state.events.update()` when the camera moves. Wrap heavy meshes in `<Bvh firstHitOnly>`.
- WebGPU earns its place only for compute, such as particle counts past about 50k. Import from `three/webgpu` and `three/tsl`, call `await renderer.init()`, render synchronously, and test the WebGL2 fallback with `forceWebGL: true`.

## Assets and GPU memory

GPU memory, not download size, is the real budget.
An uncompressed 2048 map costs 16MB of VRAM, about 21MB with mipmaps, whether it shipped as a JPEG or a PNG, so three of them exceed a mobile budget.

- `gltfjsx --transform` runs Draco, prune, resize to 1024, and WebP, typically 70 to 90 percent smaller. Use meshopt for animated or morph-target models and Draco for static ones.
- KTX2 stays compressed on the GPU. UASTC for normal maps and hero textures, ETC1S for environment and background textures. Load it through `useGLTF(path, true, true, (loader) => loader.setKTX2Loader(ktx2.detectSupport(gl)))`.
- Self-host the Draco and Basis decoders.
- Blender export is GLB with transforms applied, lights and cameras off (recreate them in code), and Draco level 6 with quantization position 14, normal 10, UV 12. Multiple clips need NLA tracks. Pack ORM as R occlusion, G roughness, B metalness.
- Loaded assets are cached by URL, so do not dispose them by hand. gltfjsx output sets `dispose={null}` for this reason. In vanilla three, dispose geometry, material, every texture slot, and render targets, since `material.dispose()` does not free its textures.
- Leak test by mounting and unmounting the scene 10 times and checking `renderer.info.memory` returns to baseline.

## DOM integration and loading

- One canvas per page. For several 3D regions use drei `<View>` on a fixed full-screen canvas, with `frames={1}` for views that do not move. Each extra `<Canvas>` is another WebGL context, and browsers cap them at about 16.
- Set `eventSource` to a shared parent so the canvas and the DOM overlay both receive events, plus `eventPrefix="client"` for a fixed background canvas.
- Readable copy lives in the DOM, never in Text3D. drei `<Html>` keeps text accessible, and its `transform` mode can render blurry.
- drei ScrollControls replaces native scroll, which breaks anchors, find-in-page, and SEO. Use it only for full-bleed experiences. On document pages drive 3D from a GSAP ScrollTrigger scrub or from a progress ref read in useFrame. See motion.md.
- Every loader sits inside Suspense, and nested boundaries let a low-poly model show first. `useGLTF.preload` at module scope. An ErrorBoundary around the model and the Canvas.
- 3D below the fold loads through IntersectionObserver plus a dynamic import of three. The hero GLB gets `<link rel="preload" as="fetch" crossorigin>`.

## Device tiers and degradation

Detect tiers from capability, never the user agent. Treat `hardwareConcurrency <= 4`, `deviceMemory < 4`, or `(pointer: coarse)` with a small viewport as low end.

| Tier | DPR | Textures | Shadows | Postprocessing |
|---|---|---|---|---|
| High | up to 2 | 2048 | on | on |
| Medium | 1.5 | 1024 | on | off |
| Low | 1 | 512 | off | off, or a static poster |

- `dpr={[1, 2]}`, capped at 1.5 on mobile. Never raw `devicePixelRatio`.
- Canvas `fallback` prop for no WebGL, and a poster or CSS gradient under the canvas so a failure still looks designed.
- Pause when off screen or hidden with `setFrameloop('never')` from an IntersectionObserver on the canvas wrapper, keeping the context. This resets `state.clock`, which is harmless only when animation reads its own time ref.
- Handle `webglcontextlost` with `preventDefault` and test it with `WEBGL_lose_context`.
- Decorative canvases get `aria-hidden`, and the meaning lives in DOM text. Configurator controls are real buttons and inputs, reachable by keyboard.
- Reduced motion stops auto-rotate, scroll scrub, and camera flights, and shows the designed still frame.

## Seeking an R3F scene

R3F owns its own loop, so wire seek-clock's contract into it rather than running a second rAF.
This pattern was run on 2026-10-24 with R3F 9.8 and capture.mjs. Seeked frames differed, the reduced-motion frame matched its still, and `__stats` reported the real counts.

```jsx
// Read on the client only, so server rendering never touches location or matchMedia.
function readSeek(stillAt) {
  if (typeof window === 'undefined') return null;
  const t = new URLSearchParams(location.search).get('t');
  if (t !== null && Number.isFinite(Number(t))) return Number(t);
  return matchMedia('(prefers-reduced-motion: reduce)').matches ? stillAt : null;
}

// Own time, because setFrameloop resets state.clock. Every animated component reads time.current.
const time = { current: 0 };
function SceneClock({ frozenAt }) {
  useFrame((_, delta) => {
    time.current = frozenAt ?? time.current + (delta > 0.25 ? 1 / 60 : delta);
  }, -1); // negative priority runs first and keeps R3F's automatic render
  return null;
}

// Inside Suspense, so it runs only after the assets resolve. gl.info still holds the last render's counts.
function Ready() {
  const gl = useThree((s) => s.gl);
  const invalidate = useThree((s) => s.invalidate);
  useEffect(() => {
    invalidate();
    requestAnimationFrame(() => requestAnimationFrame(() => {
      window.__stats = { calls: gl.info.render.calls, triangles: gl.info.render.triangles, ...gl.info.memory };
      window.__ready = true;
    }));
  }, [gl, invalidate]);
  return null;
}

function App() {
  const frozenAt = useMemo(() => readSeek(STILL_AT), []);
  return (
    <Canvas frameloop={frozenAt !== null ? 'demand' : 'always'} fallback={<img src="/poster.jpg" alt="" />}>
      <SceneClock frozenAt={frozenAt} />
      <Suspense fallback={null}>
        <Scene />
        <Ready />
      </Suspense>
    </Canvas>
  );
}
```

With a composer, `gl.info` counts only the last pass, so set `gl.info.autoReset = false` and call `gl.info.reset()` in a `useFrame` at a negative priority to count every pass.
For GSAP-driven scenes, seek with `gsap.globalTimeline.pause().time(t)` before the frame, or capture at scroll positions with `--scroll`.

## Known-wrong advice in the installed skills

Each line names what the installed skills say and what holds.

- Uncapped `devicePixelRatio` in threejs-webgl's quick start. Cap it.
- Bloom threshold 0 in react-three-fiber's examples. Use 1 with `toneMapped={false}`.
- `renderAsync` for WebGPU. Deprecated in r181, so `init()` then render.
- `PCFSoftShadowMap`. Deprecated, so use `PCFShadowMap`, which R3F exposes as `shadows="percentage"`.
- Disposing a useLoader texture to avoid a leak. Loader assets are cached, and disposing them breaks other users.
- `scene.clone()` inline in render. It re-clones every render and breaks skinned meshes, so use a gltfjsx component or `useMemo` with SkeletonUtils.
- Calling `clock.getDelta()` inside useFrame. R3F already calls it, so a second call returns about 0. Use the `delta` argument.
- `import create from 'zustand'` and `shallow` as a second argument. Removed in zustand v5, so use `{ create }` and `useShallow`.
- Mipmaps off on mobile. Keep them on, since minified textures shimmer without them.
- Real-time ground shadows stacked with ContactShadows in the react-three-fiber starter. Pick one.
- `framer-motion-3d`. Deprecated. Drive R3F from refs, springs, or GSAP.
