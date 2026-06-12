import * as THREE from 'three';

export const PAL = {
  neonPurple: 0x9e40ff,
  neonPink: 0xff4db8,
  neonCyan: 0x40f2ff,
  gold: 0xffd159,
  floor: 0x111016,
  wall: 0x1d1a26,
};

// 3-step gradient map shared by all toon materials → anime cel shading
let gradientMap = null;
function getGradientMap() {
  if (!gradientMap) {
    const data = new Uint8Array([90, 150, 255, 255]);
    gradientMap = new THREE.DataTexture(data, 4, 1, THREE.RedFormat);
    gradientMap.minFilter = THREE.NearestFilter;
    gradientMap.magFilter = THREE.NearestFilter;
    gradientMap.needsUpdate = true;
  }
  return gradientMap;
}

const cache = new Map();

export function toon(color, opts = {}) {
  const key = `t_${color}_${opts.transparent ? opts.opacity : 1}`;
  if (cache.has(key)) return cache.get(key);
  const m = new THREE.MeshToonMaterial({
    color,
    gradientMap: getGradientMap(),
    transparent: !!opts.transparent,
    opacity: opts.opacity ?? 1,
  });
  cache.set(key, m);
  return m;
}

export function neon(color, intensity = 2.6) {
  const key = `n_${color}_${intensity}`;
  if (cache.has(key)) return cache.get(key);
  const m = new THREE.MeshStandardMaterial({
    color: 0x0a0a10,
    emissive: color,
    emissiveIntensity: intensity,
  });
  cache.set(key, m);
  return m;
}

export function chrome(color = 0xccd4e6) {
  const key = `c_${color}`;
  if (cache.has(key)) return cache.get(key);
  const m = new THREE.MeshStandardMaterial({ color, metalness: 1, roughness: 0.18 });
  cache.set(key, m);
  return m;
}

export function glossy(color, roughness = 0.3) {
  const key = `g_${color}_${roughness}`;
  if (cache.has(key)) return cache.get(key);
  const m = new THREE.MeshStandardMaterial({ color, metalness: 0.15, roughness });
  cache.set(key, m);
  return m;
}

export function sheer(color, opacity = 0.42) {
  const m = new THREE.MeshStandardMaterial({
    color, transparent: true, opacity, roughness: 0.5, depthWrite: false,
  });
  return m;
}

// ---- primitive helpers (every part casts a shadow) -----------------------
function add(parent, geo, mat, pos, scale, rot) {
  const mesh = new THREE.Mesh(geo, mat);
  if (pos) mesh.position.set(pos[0], pos[1], pos[2]);
  if (scale) mesh.scale.set(scale[0], scale[1], scale[2]);
  if (rot) mesh.rotation.set(rot[0], rot[1], rot[2]);
  mesh.castShadow = true;
  parent.add(mesh);
  return mesh;
}

const GEO = {
  sphere: new THREE.SphereGeometry(0.5, 24, 18),
  box: new THREE.BoxGeometry(1, 1, 1),
  cyl: new THREE.CylinderGeometry(0.5, 0.5, 1, 20),
  capsule: new THREE.CapsuleGeometry(0.5, 1, 6, 16),
  cone: new THREE.ConeGeometry(0.5, 1, 14),
  torus: new THREE.TorusGeometry(0.5, 0.08, 10, 28),
};

// conventions: sph/box take full extents [x,y,z]; cyl/cone take [radiusX, height, radiusZ]
export const sph = (p, m, pos, s) => add(p, GEO.sphere, m, pos, s);
export const box = (p, m, pos, s, r) => add(p, GEO.box, m, pos, s, r);
export const cyl = (p, m, pos, s, r) => add(p, GEO.cyl, m, pos, [s[0] * 2, s[1], s[2] * 2], r);
export const cone = (p, m, pos, s, r) => add(p, GEO.cone, m, pos, [s[0] * 2, s[1], s[2] * 2], r);
export const torus = (p, m, pos, radius, tube, r) =>
  add(p, new THREE.TorusGeometry(radius, tube, 10, 28), m, pos, [1, 1, 1], r);

// capsule with total visual height ≈ 2*halfLen + 2*rad, axis Y
export function cap(p, m, pos, rad, halfLen, r) {
  const geo = new THREE.CapsuleGeometry(rad, halfLen * 2, 6, 16);
  return add(p, geo, m, pos, [1, 1, 1], r);
}

export function group(parent, pos) {
  const g = new THREE.Group();
  if (pos) g.position.set(pos[0], pos[1], pos[2]);
  parent.add(g);
  return g;
}
