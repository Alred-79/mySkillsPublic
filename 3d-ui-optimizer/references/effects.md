# Shader signatures and how to ship them

Load this when the signature moment is a shader effect, a gradient, glass, particles, or grain.
Each recipe gives the mechanism that makes it look good, the values that separate the good look from the cheap one, and what the source code gets wrong.
Recipes are distilled from collidingScopes/liquid-logo, ruucm/shadergradient, dashersw/liquid-glass-js, and iart-ai/webgl-animation-skills, read at the source level on 2026-10-24.

## Contents

- Choosing CSS, a drop-in library, or a custom shader
- Hardening checklist (every effect)
- Liquid-metal mark
- Folded ribbon gradient
- Liquid glass
- Particles
- Grain, banding, and shader hygiene

## Choosing CSS, a drop-in library, or a custom shader

Use **CSS or SVG** when the effect is static or slow and ambient, when it is UI chrome, when it must survive reduced motion or no WebGL unchanged, or when there are more than about three instances or the content behind them changes.
The test is a static screenshot. If the shader version does not clearly beat a CSS gradient in a still, ship the CSS.

Use **a drop-in library** when the stack already runs React with R3F, one hero instance is needed, and a preset family matches. You still owe the hardening checklist, because none of these libraries do it for you. Budget roughly 150KB gzipped for three plus R3F if they are not already shipping.

Use **a custom shader** when the effect must bind to brand material such as a logo mask or a wordmark SDF, when it reacts to scroll or pointer, when it must run without three (one full-screen triangle with vertices `-1,-1, 3,-1, -1,3` and a single `drawArrays` is a few KB), or when a library fights the design.

## Hardening checklist

None of the four source repos does all of this, which is why it lives here.

1. Resolution uniform in drawing-buffer pixels (`canvas.width`, or `renderer.getDrawingBufferSize()`), since `gl_FragCoord` is in device pixels. Size the backing store from the CSS size times a capped DPR, never from the asset size.
2. DPR 1 for soft gradients, `min(devicePixelRatio, 2)` for marks and hard edges. `gl_PointSize` multiplied by the pixel ratio.
3. Pause off screen and in hidden tabs, keeping the context and the clock. Never unmount on scroll, which recompiles shaders and resets time with a visible jump.
4. Reduced motion renders one designed frame through seek-clock's `stillAt`, never a blank.
5. A poster or CSS gradient under the canvas, with the canvas faded in after its first frame. No WebGL or a lost context leaves the poster. Never `alert()`.
6. Decorative canvases get `aria-hidden` and `pointer-events: none`, and no camera controls.
7. `preserveDrawingBuffer` only when exporting frames.
8. Dither every smooth gradient by about ±1/255.
9. One WebGL context per page where possible. Browsers cap live contexts around 16 and kill the oldest.

## Liquid-metal mark

The strongest signature candidate, for a bold mark on a dark ground once per site.
It becomes gimmicky at small sizes, on thin or detailed marks, on light themes where the highlights read as glare, and when repeated.

**Mechanism.** An iterative cosine vector field, not a fluid sim, cut out by the logo's alpha.
The look comes from the tone step.
Dividing by the accumulated energy turns low-energy regions into bright filaments, and `tanh` soft-clips them to 1, which reads as molten chrome.
Per-channel vertical exponents give the top-to-bottom color shift.

```glsl
vec2 p = (gl_FragCoord.xy * 2. - u_resolution) / u_resolution.y;
float lx = abs(u_dotFactor - dot(p, p)) * u_dotMultiplier;          // radial ring that shapes the flow
vec2 v = p * (1. - lx) / u_scale;
vec4 o = vec4(0);
for (float i = 0.; i < 16.; i++) {
  if (i >= u_iterations) break;
  float k = i + 1.;
  v += cos(v.yx * k + vec2(0, k) + t) / k + u_vOffset;
  o += (sin(v.xyyx) + 1.) * abs(v.x - v.y) * u_intensity;
}
vec4 x = clamp(exp(p.y * vec4(u_colorFactors, 0.)) * exp(-u_expFactor * lx) / max(o, vec4(1e-3)), 0., 20.);
o = tanh(x);                                                         // WebGL1 has no tanh, write it with exp(2x) on the clamped x
float alpha = smoothstep(.05, .5, texture2D(u_logo, uv).a);          // not a hard discard
```

**Good values** (the Chrome preset). Speed 0.33 to 0.45, iterations 11 to 15 (fewer posterizes into bands), intensity 0.07 to 0.2, scale 3.1, dotFactor 0.04, dotMultiplier 0.21, color factors (1.1, 0.7, 0.9), edge rim 0.4 to 0.5.
Tint toward the brand by changing the color factors, then look at the frame, since a factor that seems warm on paper can render teal.
**Cheap values.** Noise above about 2, iterations under 8, color factors past ±1.5.

**Fixes over the source.** Anti-alias the mask with `smoothstep` or an SDF of the logo instead of a hard alpha discard. Clamp the ratio before tanh, since it overflows to NaN when energy nears 0. Cap DPR and pause off screen, which the source never does. Marks under about 120px turn to noise, so use a static render there.

**License.** The repo is MIT, but its core loop comes from XorDev's Plasma shader, which has no stated license. Rewrite the loop from the mechanism and credit both.

## Folded ribbon gradient

The best ambient hero background, behind sparse type.
Stock presets read as the generic AI-startup look, so the palette and crop must come from the brand.

**Mechanism.** Not a fragment gradient. A plane of `planeGeometry(10, 10, 1, 192)`, one segment across and 192 along, pushed along its normal by 3D Perlin noise.
Because noise varies along one axis, the surface folds into long silk ribbons instead of bumpy terrain, from 386 vertices.
Color mixes by position, `mix(mix(c1, c2, smoothstep(-3, 3, pos.x)), c3, pos.z)`, so the third color shows on the crests. Clamp `pos.z`, or high strength blows the mix out.
The camera crops into one fold and never shows the mesh edges.

**Good values.** Speed 0.1 to 0.2 behind type, strength 3 to 4, density 1.3, brightness 1.1 to 1.5, matte (roughness 0.9). Palettes of analogous colors plus one accent.

**Shipping @shadergradient/react.**

```tsx
<ShaderGradientCanvas style={{ position: 'absolute', inset: 0 }} pixelDensity={1} pointerEvents="none">
  <ShaderGradient type="plane" animate={reduced ? 'off' : 'on'} uSpeed={0.2} uStrength={3} uDensity={1.3}
    color1="#..." color2="#..." color3="#..." cDistance={3.6} cPolarAngle={90} cAzimuthAngle={180}
    positionX={-1.4} rotationZ={50} lightType="3d" brightness={1.2} grain="off" />
</ShaderGradientCanvas>
```

Every override there is load-bearing.
`pointerEvents="none"` stops its camera controls from hijacking page scroll on touch.
`grain="off"` avoids its halftone pass, which costs about 108 texture reads per pixel, so add a hash grain instead.
`lightType="3d"` avoids fetching three HDRs from the author's domain, or self-host them with `envBasePath`.
The React package has no reduced-motion handling, so pass `animate` yourself.
Its `lazyLoad` unmounts off screen and recompiles on return, so for a hero that scrolls back into view, pause instead.
Its canvas is linear and untonemapped, so the same hexes shift if you mount the mesh inside your own default R3F canvas.

## Liquid glass

Fits only when the glass moves over rich, changing imagery, so the refraction is visible.
Over flat color it is a blurry pill, and everywhere at once it is the 2025 to 2026 OS default.

**Production path.** `backdrop-filter: blur(12px to 20px) saturate(150% to 180%)` with the `-webkit-` prefix for Safari, a 1px inner highlight, and a rim gradient border.
True refraction through `backdrop-filter: url(#displacement)` works only in Chromium, so treat it as progressive enhancement.
Check text contrast against the brightest and darkest content that can pass behind it.

**The shader math worth keeping.** Bend concentrates at the rim and the center stays undistorted, which is what reads as thick glass. A uniform blur reads as frosted plastic.
With `d` the distance in pixels inside the shape's SDF, offset along the SDF gradient (not the radial direction, which bends wide pills diagonally) by `edgeI * exp(-d * 0.15) + rimI * exp(-d * 0.8)`, so the bend decays to 1/e within about 7px and 1.25px.
Mask with `1 - smoothstep(-1, 1, sdf)`. Defaults edge 0.01, rim 0.05, ripple at most 0.1, blur about 5.

**liquid-glass-js is a prototype tool only.** It snapshots the page once with html2canvas, so video, animation, lazy images, and theme changes behind it never refract. Cross-origin images silently taint the snapshot and the glass never starts. It opens one WebGL context per element, its buttons are divs with no role or keyboard support, and it runs about 770 texture reads per pixel.

## Particles

- Curl noise `(∂N/∂y, -∂N/∂x)` for flow, since it never lets particles pile up the way an angle field does.
- Stateless GPU life with `fract(seed + t * 0.15 * speed)` and a `sin(life * π)` fade runs 80k points with no CPU work, and seeks perfectly.
- Depth by tying size, speed, and opacity together, so near particles are bigger, faster, and more opaque.
- Confetti reads as paper through rotation plus a height squashed by `|cos(rot)|`. Use it on a real success moment only.
- Trails by painting `rgba(0, 0, 0, 0.04)` over the frame instead of clearing.
- Seeded random (mulberry32) so a seeked frame is identical run to run.
- Avoid connected-dot constellation backgrounds, a cliché.

## Grain, banding, and shader hygiene

- Cheapest good grain is a fixed overlay with an inline SVG `feTurbulence` (fractalNoise, baseFrequency 0.85, 3 octaves) on a 140px tile at opacity 0.07, `mix-blend-mode` screen or overlay, `pointer-events: none`. In a shader, one hash line at about ±0.06.
- Rotate each fbm octave by `mat2(.8, .6, -.6, .8)` to hide grid artifacts. Render heavy domain-warp shaders to a half-resolution target.
- Artifact triage when you look at a frame.

| You see | Likely cause |
|---|---|
| Black canvas | Shader compile error. Read the console |
| White or garbage pixels | NaN from `pow` or `log` of a negative, or a divide by zero |
| Objects vanish | NaN positions, or a stale bounding sphere on an instanced mesh |
| Particles stacked at the origin | Random seed not wired |
| Effect zoomed or off center on retina only | Resolution uniform in CSS pixels |
| Colors shifted from the hexes | Tone mapping or color space mismatch, see 3d-craft.md |
