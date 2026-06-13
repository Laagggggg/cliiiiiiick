import * as THREE from 'three';
import { toon, rimSkin, glossy, lathe, sph, box, cap, cyl, group } from '../core/materials.js';
import { FACES, SKINS, PRESETS } from './presets.js';
import { equipItem } from '../clothing/factory.js';

// ---------------------------------------------------------------------------
// Procedural anime-styled avatar. A continuous, curvy body built from smooth
// lathe sections + tapered limbs with joint fillers (no puppet gaps), rim-lit
// cel-shaded skin, and a canvas-painted anime face. The skeleton metrics
// (rig.dims / rig.joints / anchors) are unchanged, so the clothing system
// keeps aligning. A real GLB/VRoid model can replace the meshes later without
// touching gameplay code.
// ---------------------------------------------------------------------------

const faceTexCache = new Map();

function makeFaceTexture(faceKey, fem) {
  const key = `${faceKey}_${fem}`;
  if (faceTexCache.has(key)) return faceTexCache.get(key);

  const f = FACES[faceKey] || FACES.softAnime;
  const cv = document.createElement('canvas');
  cv.width = 512; cv.height = 384;
  const g = cv.getContext('2d');
  g.clearRect(0, 0, 512, 384);

  const eyeW = 74 * f.eye, eyeH = 66 * f.eye;
  const cy = 176;
  const sep = 104;

  for (const dir of [-1, 1]) {
    const cx = 256 + dir * sep;
    g.save();
    g.translate(cx, cy);

    // big glossy anime eye — white, gradient iris, dark pupil, twin highlights
    g.fillStyle = '#fdfdff';
    g.beginPath(); g.ellipse(0, 0, eyeW, eyeH, 0, 0, Math.PI * 2); g.fill();

    const grad = g.createLinearGradient(0, -eyeH, 0, eyeH);
    grad.addColorStop(0, '#120f1d');
    grad.addColorStop(0.4, f.iris);
    grad.addColorStop(1, lighten(f.iris, 80));
    g.fillStyle = grad;
    g.beginPath(); g.ellipse(0, eyeH * 0.08, eyeW * 0.66, eyeH * 0.9, 0, 0, Math.PI * 2); g.fill();

    g.fillStyle = '#0d0a16';
    g.beginPath(); g.ellipse(0, eyeH * 0.1, eyeW * 0.34, eyeH * 0.5, 0, 0, Math.PI * 2); g.fill();

    g.fillStyle = 'rgba(255,255,255,0.98)';
    g.beginPath(); g.ellipse(-eyeW * 0.26, -eyeH * 0.34, eyeW * 0.2, eyeH * 0.17, 0, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.ellipse(eyeW * 0.22, eyeH * 0.3, eyeW * 0.1, eyeH * 0.09, 0, 0, Math.PI * 2); g.fill();

    // thick upper lash line + winged liner
    g.strokeStyle = '#171019';
    g.lineWidth = f.lash ? 16 : 10;
    g.lineCap = 'round';
    g.beginPath();
    g.moveTo(-eyeW * 1.04, -eyeH * 0.36);
    g.quadraticCurveTo(0, -eyeH * 1.26, eyeW * 1.08, -eyeH * 0.5);
    g.stroke();
    if (f.lash) {
      g.lineWidth = 7;
      g.beginPath();
      g.moveTo(dir === 1 ? eyeW * 0.95 : -eyeW * 0.95, -eyeH * 0.66);
      g.lineTo(dir === 1 ? eyeW * 1.4 : -eyeW * 1.4, -eyeH * 1.05);
      g.stroke();
    }

    // brow
    g.strokeStyle = '#2a1d33';
    g.lineWidth = 10;
    g.save();
    g.rotate((-dir * f.brow * Math.PI) / 180);
    g.beginPath();
    g.moveTo(-eyeW * 0.8, -eyeH * 1.5);
    g.quadraticCurveTo(0, -eyeH * 1.74, eyeW * 0.82, -eyeH * 1.46);
    g.stroke();
    g.restore();

    g.restore();
  }

  // tiny nose shadow
  g.strokeStyle = 'rgba(60,40,55,0.45)';
  g.lineWidth = 5; g.lineCap = 'round';
  g.beginPath(); g.moveTo(256, 248); g.lineTo(250, 262); g.stroke();

  // small anime mouth
  g.strokeStyle = f.lips ? '#c2536b' : '#5e3a42';
  g.lineWidth = f.lips ? 9 : 6;
  g.beginPath();
  g.moveTo(238, 300);
  g.quadraticCurveTo(256, 314, 274, 300);
  g.stroke();
  if (f.lips) {
    g.fillStyle = 'rgba(210,90,120,0.32)';
    g.beginPath(); g.ellipse(256, 304, 22, 9, 0, 0, Math.PI * 2); g.fill();
  }

  if (fem) { // soft blush
    g.fillStyle = 'rgba(255,120,150,0.22)';
    for (const dir of [-1, 1]) {
      g.beginPath(); g.ellipse(256 + dir * 150, 256, 44, 22, 0, 0, Math.PI * 2); g.fill();
    }
  }

  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  faceTexCache.set(key, tex);
  return tex;
}

function lighten(hex, amt) {
  const n = parseInt(hex.slice(1), 16);
  const r = Math.min(255, (n >> 16) + amt), g2 = Math.min(255, ((n >> 8) & 255) + amt),
    b = Math.min(255, (n & 255) + amt);
  return `rgb(${r},${g2},${b})`;
}

// ---------------------------------------------------------------------------

export function buildAvatar({ preset = 'femaleCurvy', body, faceKey, skin = 0 } = {}) {
  const p = PRESETS[preset] || PRESETS.femaleCurvy;
  const cfg = body;
  const fem = p.fem;
  faceKey = faceKey || p.face;

  const skinHex = new THREE.Color(SKINS[skin] || SKINS[0]).getHex();
  const skinMat = rimSkin(skinHex);                 // rim-lit cel skin
  const baseMat = toon(0x241f2c);                   // dark base layer (bra/shorts)
  const hairBaseMat = skinMat;

  const root = new THREE.Group();
  const muscleW = THREE.MathUtils.lerp(0.92, 1.18, THREE.MathUtils.inverseLerp(0.6, 1.6, cfg.muscle));

  // ---- skeleton metrics (UNCHANGED so clothing keeps aligning) ----
  const legLen = 0.92 * cfg.legLen * cfg.height;
  const hipY = legLen;
  const torsoLen = 0.62 * cfg.height;
  const L = torsoLen;
  const shoulderY = hipY + torsoLen * 0.82;
  const headR = 0.14 * cfg.headSize;
  const headY = hipY + torsoLen * 0.95 + 0.07 + headR;
  const shw = 0.235 * cfg.shoulders * muscleW;
  const hipw = 0.165 * cfg.hips;

  const hipsK = cfg.hips, waistK = cfg.waist, chestK = cfg.chest, shK = cfg.shoulders * muscleW;
  const thighsK = cfg.thighs * THREE.MathUtils.lerp(1, cfg.hips, 0.3);
  const calvesK = cfg.calves;
  const armK = cfg.arms * muscleW;

  // ===================== PELVIS / HIPS (skin + base bottom) =====================
  const pelvis = group(root, [0, hipY + 0.04, 0]);
  sph(pelvis, skinMat, [0, 0, 0], [0.34 * hipsK, 0.26, 0.27 * hipsK]);
  sph(pelvis, skinMat, [0, -0.02, -0.08], [0.30 * hipsK, 0.23, 0.22 * cfg.glutes]);
  sph(pelvis, skinMat, [0, -0.11, 0.01], [0.20, 0.18, 0.20]);          // upper-thigh blend
  // base-layer bottoms (bikini/shorts) — covered when real bottoms are equipped
  lathe(pelvis, baseMat,
    [[0.12, -0.13], [0.175 * hipsK, -0.06], [0.18 * hipsK, 0.02], [0.135, 0.07]],
    { depthScale: 0.82, pos: [0, 0, 0] });

  // =============================== TORSO (lathe) ================================
  const torso = group(root, [0, hipY + 0.06, 0]);
  torso.rotation.x = -cfg.posture * 0.07;
  lathe(torso, skinMat, [
    [0.085, -0.10],
    [0.150 * hipsK, L * 0.03],
    [0.146 * hipsK, L * 0.12],
    [0.138 * waistK, L * 0.22],
    [0.118 * waistK, L * 0.33],     // waist pinch (narrowest)
    [0.140 * (fem ? 1.0 : chestK), L * 0.45],
    [0.166 * (fem ? 1.0 : chestK), L * 0.54],
    [0.168 * shK, L * 0.66],
    [0.182 * shK, L * 0.78],        // shoulders
    [0.120, L * 0.86],
    [0.064, L * 0.93],              // neck base
    [0.052, L * 1.00],
    [0.050, L * 1.07],              // neck → meets head
  ], { depthScale: 0.74 });

  // bust (female) — paired spheres blended onto the chest
  if (fem) {
    for (const d of [-1, 1]) {
      sph(torso, skinMat, [d * 0.082 * chestK, L * 0.52, 0.072],
        [0.15 * chestK, 0.145 * chestK, 0.14 * chestK]);
    }
    // base-layer bandeau
    cyl(torso, baseMat, [0, L * 0.525, 0.012], [0.158 * chestK, 0.135, 0.125 * chestK]);
    for (const d of [-1, 1])
      box(torso, baseMat, [d * 0.10, L * 0.66, 0.02], [0.03, 0.16, 0.04], [0, 0, d * 0.15]);
  } else {
    // male base tank
    lathe(torso, baseMat, [
      [0.150 * shK, L * 0.18], [0.150 * chestK, L * 0.45],
      [0.165 * chestK, L * 0.54], [0.168 * shK, L * 0.70],
    ], { depthScale: 0.74 });
  }

  const backAnchor = group(torso, [0, L * 0.76 - 0.05, -0.16]);

  // ================================== ARMS ====================================
  function arm(dir) {
    const joint = group(torso, [dir * shw, L * 0.76, 0]);
    sph(joint, skinMat, [0, 0.01, 0], [0.135, 0.135, 0.135]);            // shoulder ball
    cap(joint, skinMat, [0, -0.17, 0], 0.05 * armK, 0.10);              // upper arm
    sph(joint, skinMat, [0, -0.31, 0], [0.088, 0.088, 0.088]);          // elbow
    cap(joint, skinMat, [0, -0.44, 0], 0.043 * armK, 0.10);            // forearm
    sph(joint, skinMat, [0, -0.55, 0], [0.062, 0.062, 0.062]);          // wrist
    sph(joint, skinMat, [0, -0.61, 0.01], [0.072 * cfg.hands, 0.11 * cfg.hands, 0.05]); // hand
    return joint;
  }
  const shoulderL = arm(-1), shoulderR = arm(1);

  // ================================== LEGS ====================================
  function leg(dir) {
    const joint = group(root, [dir * 0.1 * cfg.hips, hipY, 0]);
    sph(joint, skinMat, [0, -0.04, 0], [0.21 * thighsK, 0.22, 0.21 * thighsK]); // hip/thigh top
    cap(joint, skinMat, [0, -0.20, 0], 0.093 * thighsK, 0.11);          // thigh
    sph(joint, skinMat, [0, -0.40, 0], [0.115, 0.12, 0.12]);            // knee
    cap(joint, skinMat, [0, -0.57, 0], 0.07 * calvesK, 0.11);          // calf
    sph(joint, skinMat, [0, -0.70, 0], [0.072, 0.075, 0.078]);          // ankle
    const footY = -(hipY - 0.045);
    box(joint, skinMat, [0, footY, 0.05], [0.1 * cfg.feet, 0.07, 0.235 * cfg.feet]); // foot
    return joint;
  }
  const hipL = leg(-1), hipR = leg(1);

  // ================================== HEAD ====================================
  const headGroup = group(torso, [0, headY - (hipY + 0.06), 0]);
  sph(headGroup, skinMat, [0, headR * 0.05, 0], [headR * 1.66, headR * 1.95, headR * 1.78]); // skull
  // tapered anime jaw → pointed chin
  lathe(headGroup, skinMat, [
    [headR * 0.80, -headR * 0.95], [headR * 1.04, -headR * 0.55],
    [headR * 1.16, -headR * 0.1], [headR * 1.0, headR * 0.3],
  ], { depthScale: 0.92 });
  for (const d of [-1, 1]) // ears
    sph(headGroup, skinMat, [d * headR * 1.0, 0, -headR * 0.05], [headR * 0.3, headR * 0.42, headR * 0.32]);

  // anime face plane (unlit so the eyes always read bright). Curved around
  // the skull so it wraps the face instead of going edge-on when the head turns.
  const faceTex = makeFaceTexture(faceKey, fem);
  const fgeo = new THREE.PlaneGeometry(headR * 2.0, headR * 1.55, 16, 6);
  {
    const pos = fgeo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), y = pos.getY(i);
      pos.setZ(i, pos.getZ(i) - (x * x) * 2.6 - (y * y) * 0.7); // wrap sideways + a little vertically
    }
    fgeo.computeVertexNormals();
  }
  const facePlane = new THREE.Mesh(
    fgeo,
    new THREE.MeshBasicMaterial({ map: faceTex, transparent: true, depthWrite: false })
  );
  facePlane.renderOrder = 2;
  facePlane.position.set(0, headR * 0.04, headR * 0.86);
  facePlane.rotation.x = -0.05;
  headGroup.add(facePlane);

  const faceAnchor = group(headGroup, [0, 0.01, headR * 0.92]);
  const hairAnchor = group(headGroup, [0, 0, 0]);

  root.scale.setScalar(cfg.scale);

  const rig = {
    root, torso, pelvis, headGroup, faceAnchor, hairAnchor, backAnchor, cfg,
    joints: { shoulderL, shoulderR, hipL, hipR },
    dims: { hipY, shoulderY, torsoLen, headR, shw, hipw },
    fem, skinHex, walkPhase: 0, walkSpeed: 0,
    equipped: new Map(),

    equip(item) {
      if (!item) return;
      rig.unequip(item.slot);
      rig.equipped.set(item.slot, { item, pieces: equipItem(rig, item) });
    },
    unequip(slot) {
      const cur = rig.equipped.get(slot);
      if (cur) {
        for (const piece of cur.pieces) piece.parent?.remove(piece);
        rig.equipped.delete(slot);
      }
    },
    isEquipped(item) {
      return rig.equipped.get(item.slot)?.item.id === item.id;
    },
    outfitIds() {
      const out = {};
      for (const [slot, { item }] of rig.equipped) out[slot] = item.id;
      return out;
    },
    dispose() { root.parent?.remove(root); },
  };
  return rig;
}
