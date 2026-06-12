import * as THREE from 'three';
import { PAL, toon, neon, chrome, glossy, sheer, box, cyl, sph } from '../core/materials.js';
import { byCategory, findItem } from '../clothing/catalog.js';
import { buildAvatar } from '../avatar/builder.js';
import { bodyFor, PRESETS } from '../avatar/presets.js';

// ---------------------------------------------------------------------------
// The walkable FINAL FIT district store: zoned fixtures along the walls,
// themed alcoves with dressed mannequins, a central theme totem, and the
// runway preview stage with a judges' desk.
// ---------------------------------------------------------------------------

export function textPanel(text, color = '#ffffff', size = 0.16, weight = 900) {
  const cv = document.createElement('canvas');
  const g = cv.getContext('2d');
  g.font = `${weight} 90px "Segoe UI", Arial, sans-serif`;
  const w = Math.ceil(g.measureText(text).width) + 40;
  cv.width = w; cv.height = 130;
  const g2 = cv.getContext('2d');
  g2.font = `${weight} 90px "Segoe UI", Arial, sans-serif`;
  g2.textBaseline = 'middle';
  g2.fillStyle = color;
  g2.shadowColor = color; g2.shadowBlur = 26;
  g2.fillText(text, 20, 68);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  // FrontSide only — double-sided planes show mirrored text from behind
  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry((w / 130) * size, size),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true })
  );
  mesh.userData.setText = (t, c = color) => {
    g2.clearRect(0, 0, w, 130);
    g2.fillStyle = c; g2.shadowColor = c;
    g2.fillText(t, 20, 68);
    tex.needsUpdate = true;
  };
  return mesh;
}

function strip(scene, pos, scale, color, intensity = 2.6) {
  const s = box(scene, neon(color, intensity), pos, scale);
  s.castShadow = false;
  return s;
}

export function buildStore(scene) {
  const racks = [];
  const obstacles = [];
  const mannequins = [];

  const floorMat = new THREE.MeshStandardMaterial({ color: PAL.floor, metalness: 0.25, roughness: 0.5 });
  const wallMat = glossy(PAL.wall, 0.7);

  const floor = box(scene, floorMat, [0, -0.05, 0], [44, 0.1, 30]);
  floor.receiveShadow = true; floor.castShadow = false;
  box(scene, wallMat, [0, 2.5, 15], [44, 5, 0.4]);
  box(scene, wallMat, [0, 2.5, -15], [44, 5, 0.4]);
  box(scene, wallMat, [22, 2.5, 0], [0.4, 5, 30]);
  box(scene, wallMat, [-22, 2.5, 0], [0.4, 5, 30]);

  strip(scene, [0, 4.6, 14.7], [43, 0.06, 0.06], PAL.neonPurple);
  strip(scene, [0, 4.6, -14.7], [43, 0.06, 0.06], PAL.neonPink);
  strip(scene, [21.7, 4.6, 0], [0.06, 0.06, 29], PAL.neonCyan);
  strip(scene, [-21.7, 4.6, 0], [0.06, 0.06, 29], PAL.neonPurple);
  strip(scene, [6, 0.02, 0], [24, 0.015, 0.18], PAL.neonPink, 1.8);

  const brandSign = textPanel('FINAL FIT — DISTRICT STORE', '#ff4db8', 0.7);
  brandSign.position.set(0, 4.0, 14.55); brandSign.rotation.y = Math.PI;
  scene.add(brandSign);

  // ---- lighting ----
  scene.add(new THREE.HemisphereLight(0x9d92cc, 0x221d2e, 1.4));
  const key = new THREE.DirectionalLight(0xbfb3ff, 1.3);
  key.position.set(8, 14, 6);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.camera.left = -24; key.shadow.camera.right = 24;
  key.shadow.camera.top = 18; key.shadow.camera.bottom = -18;
  scene.add(key);

  const pt = (x, y, z, c, i = 14, d = 11) => {
    const l = new THREE.PointLight(c, i, d, 1.8);
    l.position.set(x, y, z);
    scene.add(l);
  };
  pt(-10, 3.4, -8, PAL.neonPurple); pt(4, 3.4, -8, PAL.neonCyan);
  pt(-10, 3.4, 8, PAL.neonPink); pt(4, 3.4, 8, 0xffc070);
  pt(16, 3.6, 0, 0xffffff, 18, 13); pt(-19, 2.8, 0, PAL.gold, 10, 8);
  pt(-19, 2.8, -6.5, 0x9030c0, 10, 8); pt(-19, 2.8, 7, PAL.neonCyan, 10, 8);

  // ---- fixtures ----
  const fixture = (x, z, yaw, category, zone, accent) => {
    const root = new THREE.Group();
    root.position.set(x, 0, z);
    root.rotation.y = yaw;
    scene.add(root);
    racks.push({ x, z, category, zone });
    obstacles.push({ minX: x - 1.4, maxX: x + 1.4, minZ: z - 0.8, maxZ: z + 0.8 });

    const sign = textPanel(zone.toUpperCase(), hex(accent), 0.34);
    sign.position.set(0, 2.55, 0.05);
    root.add(sign);
    strip(root, [0, 0.015, 0.9], [2.6, 0.012, 0.1], accent, 1.6);
    return root;
  };

  const garmentRack = (x, z, yaw, category, zone, accent) => {
    const root = fixture(x, z, yaw, category, zone, accent);
    const metal = chrome(0xa6a6b3);
    cyl(root, metal, [-1.1, 0.85, 0], [0.03, 1.7, 0.03]);
    cyl(root, metal, [1.1, 0.85, 0], [0.03, 1.7, 0.03]);
    cyl(root, metal, [0, 1.62, 0], [0.025, 2.24, 0.025], [0, 0, Math.PI / 2]);
    const items = byCategory(category);
    const n = Math.max(3, Math.min(6, items.length));
    for (let i = 0; i < n; i++) {
      const c = items.length ? items[i % items.length].c1 : 0x44444c;
      box(root, toon(c), [-0.85 + (i * 1.7) / (n - 1), 1.18, 0],
        [0.26, 0.78, 0.07], [0, (Math.sin(i * 9) * 7 * Math.PI) / 180, 0]);
    }
  };

  // south wall
  garmentRack(-17, -13, 0, 'tops', 'Tops', PAL.neonPurple);
  garmentRack(-10, -13, 0, 'outerwear', 'Outerwear', PAL.neonPink);
  garmentRack(-3, -13, 0, 'bottoms', 'Bottoms', PAL.neonPurple);
  // shoe wall
  {
    const root = fixture(4.5, -13, 0, 'shoes', 'Shoe Wall', PAL.neonCyan);
    const shelfM = glossy(0x29262f, 0.5);
    const shoes = byCategory('shoes');
    for (let row = 0; row < 3; row++) {
      box(root, shelfM, [0, 0.55 + row * 0.55, -0.1], [2.6, 0.05, 0.45]);
      for (let i = 0; i < 4; i++)
        box(root, toon(shoes[(row * 4 + i) % shoes.length].c1),
          [-0.95 + i * 0.63, 0.63 + row * 0.55, -0.1], [0.16, 0.12, 0.34]);
    }
  }
  garmentRack(11.5, -13, 0, 'headwear', 'Headwear', 0xffc070);

  // north wall
  {
    const root = fixture(-17, 13, Math.PI, 'jewelry', 'Jewelry Counter', PAL.gold);
    box(root, glossy(0x1a1722, 0.4), [0, 0.5, 0], [2.4, 1.0, 0.9]);
    box(root, sheer(0xb3d9ff, 0.16), [0, 1.13, 0], [2.3, 0.25, 0.8]);
    for (let i = 0; i < 5; i++)
      box(root, chrome(i % 2 ? 0xffffff : PAL.gold), [-0.9 + i * 0.45, 1.08, 0],
        [0.09, 0.09, 0.09], [0.78, 0.78, 0]);
  }
  garmentRack(-10, 13, Math.PI, 'accessories', 'Accessories', PAL.neonPink);
  garmentRack(-3, 13, Math.PI, 'bags', 'Bags', 0xc09060);
  {
    const root = fixture(4.5, 13, Math.PI, 'hair', 'Hair & Makeup', PAL.neonPink);
    box(root, chrome(0xccd6ee), [0, 1.5, -0.4], [1.6, 2.2, 0.08]);
    strip(root, [0, 2.65, -0.4], [1.7, 0.05, 0.05], PAL.neonPink);
    cyl(root, toon(0x4d2d66), [0, 0.45, 0.5], [0.2, 0.09, 0.2]);
    cyl(root, chrome(0x888899), [0, 0.22, 0.5], [0.035, 0.44, 0.035]);
  }

  // ---- themed alcoves with mannequins ----
  const alcove = (z, title, accent, outfit) => {
    box(scene, glossy(0x16131d, 0.5), [-20.2, 1.6, z + 2.6], [3.2, 3.2, 0.25]);
    box(scene, glossy(0x16131d, 0.5), [-20.2, 1.6, z - 2.6], [3.2, 3.2, 0.25]);
    obstacles.push({ minX: -22, maxX: -18.6, minZ: z + 2.45, maxZ: z + 2.75 });
    obstacles.push({ minX: -22, maxX: -18.6, minZ: z - 2.75, maxZ: z - 2.45 });

    const sign = textPanel(title, hex(accent), 0.42);
    sign.position.set(-18.6, 2.9, z); sign.rotation.y = Math.PI / 2;
    scene.add(sign);

    cyl(scene, glossy(0x221f2b, 0.6), [-19.4, 0.15, z], [0.7, 0.3, 0.7]);
    strip(scene, [-19.4, 0.31, z], [1.5, 0.012, 1.5], accent, 1.5);
    obstacles.push({ minX: -20.2, maxX: -18.6, minZ: z - 0.8, maxZ: z + 0.8 });

    const keys = Object.keys(PRESETS);
    const pk = keys[Math.floor(Math.abs(z) * 7) % keys.length];
    const rig = buildAvatar({ preset: pk, body: bodyFor(pk), skin: (Math.abs(z) | 0) % 5 });
    rig.root.position.set(-19.4, 0.32, z);
    rig.root.rotation.y = Math.PI / 2;
    for (const id of outfit) rig.equip(findItem(id));
    scene.add(rig.root);
    mannequins.push(rig);
  };
  alcove(-6.5, 'OPIUM ROOM', 0x9030c0, ['out_trench', 'bot_leather', 'sho_platform', 'jwl_choker', 'hair_long']);
  alcove(0.5, 'LUXURY', PAL.gold, ['out_white_trench', 'bot_tailored', 'sho_loafers', 'jwl_chain', 'hair_slick']);
  alcove(7, 'STREETWEAR', PAL.neonCyan, ['top_hoodie_black', 'bot_baggy', 'sho_chunky', 'hat_cap', 'hair_wolf']);

  // ---- central theme totem ----
  box(scene, glossy(0x221f2b, 0.6), [-3, 1.6, 0], [0.5, 3.2, 0.5]);
  strip(scene, [-3, 3.25, 0], [0.7, 0.04, 0.7], PAL.neonPink);
  obstacles.push({ minX: -3.6, maxX: -2.4, minZ: -0.6, maxZ: 0.6 });
  // planes face +z by default → north plane rotation 0, south plane rotation π
  const totemTexts = [];
  for (const yaw of [0, Math.PI]) {
    const off = yaw === 0 ? 0.28 : -0.28;
    const a = textPanel('ROUND THEME', '#9a93b8', 0.16);
    a.position.set(-3, 2.75, off); a.rotation.y = yaw; scene.add(a);
    const b = textPanel('OPIUM NIGHT', '#9e40ff', 0.26);
    b.position.set(-3, 2.45, off); b.rotation.y = yaw; scene.add(b);
    const t = textPanel('10:00', '#f4f2ff', 0.34);
    t.position.set(-3, 2.05, off); t.rotation.y = yaw; scene.add(t);
    totemTexts.push(t);
  }

  // ---- runway preview stage ----
  const stage = box(scene, new THREE.MeshStandardMaterial({ color: 0x0d0d12, metalness: 0.4, roughness: 0.25 }),
    [16, 0.18, 0], [9.5, 0.36, 2.3]);
  stage.receiveShadow = true;
  strip(scene, [16, 0.37, 1.12], [9.5, 0.02, 0.05], PAL.neonPink);
  strip(scene, [16, 0.37, -1.12], [9.5, 0.02, 0.05], PAL.neonPink);
  obstacles.push({ minX: 11.2, maxX: 20.8, minZ: -1.2, maxZ: 1.2 });
  const runwaySign = textPanel('RUNWAY', '#ff4db8', 0.5);
  runwaySign.position.set(16, 3.4, 1.6);
  runwaySign.rotation.y = Math.PI; // faces the store interior (−z)
  scene.add(runwaySign);

  const spot = new THREE.SpotLight(0xffffff, 11, 16, 0.55, 0.45, 1.4);
  spot.position.set(16, 5.2, 2.5);
  spot.target.position.set(15, 0.4, 0);
  spot.castShadow = true;
  scene.add(spot, spot.target);

  // judges' desk
  box(scene, glossy(0x1a1722, 0.5), [16, 0.55, -2.6], [5.2, 1.1, 0.8]);
  strip(scene, [16, 1.12, -2.2], [5.2, 0.03, 0.03], PAL.gold, 2);
  obstacles.push({ minX: 13.4, maxX: 18.6, minZ: -3.0, maxZ: -2.2 });
  const judgesSign = textPanel('JUDGES', '#ffd159', 0.3);
  judgesSign.position.set(16, 1.6, -2.18); // front face of the desk, toward runway
  scene.add(judgesSign);

  const judges = [];
  const paddles = [];
  const judgeSetups = [
    { face: 'villain', extra: 'acc_shades' },
    { face: 'elegantRunway', extra: 'jwl_chain' },
    { face: 'sharpModel', extra: 'jwl_chain' },
  ];
  const presetKeys = ['maleLean', 'femaleRunway', 'andro'];
  for (let i = 0; i < 3; i++) {
    const pk = presetKeys[i];
    const rig = buildAvatar({ preset: pk, body: bodyFor(pk), faceKey: judgeSetups[i].face, skin: i + 1 });
    rig.root.position.set(14.4 + i * 1.6, 0, -3.3);
    rig.equip(findItem(i === 1 ? 'out_white_trench' : 'out_trench'));
    rig.equip(findItem('hair_slick'));
    rig.equip(findItem(judgeSetups[i].extra));
    scene.add(rig.root);
    judges.push(rig);

    const paddleRoot = new THREE.Group();
    paddleRoot.position.set(0.35, 1.55, 0.1);
    rig.root.add(paddleRoot);
    cyl(paddleRoot, toon(0x111114), [0, -0.12, 0], [0.012, 0.24, 0.012]);
    box(paddleRoot, toon(0xf0edf7), [0, 0.1, 0], [0.3, 0.22, 0.03]);
    const score = textPanel('—', '#33205c', 0.14);
    score.position.set(0, 0.1, 0.022);
    paddleRoot.add(score);
    paddles.push(score);
  }

  return {
    racks,
    obstacles,
    bounds: { minX: -21.2, maxX: 21.2, minZ: -14.2, maxZ: 14.2 },
    runway: {
      start: new THREE.Vector3(19.8, 0.36, 0),
      end: new THREE.Vector3(12.4, 0.36, 0),
      judgesLook: new THREE.Vector3(16, 1.2, -2.6),
    },
    paddles,
    judges,
    mannequins,
    totemTexts,
  };
}

function hex(c) {
  return '#' + c.toString(16).padStart(6, '0');
}
