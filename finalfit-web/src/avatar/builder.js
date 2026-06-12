import * as THREE from 'three';
import { toon, glossy, sph, box, cap, cyl, group } from '../core/materials.js';
import { FACES, SKINS, PRESETS } from './presets.js';
import { equipItem } from '../clothing/factory.js';

// ---------------------------------------------------------------------------
// Procedural anime-styled avatar. Stylized proportions, cel shading and a
// canvas-painted anime face. All external systems talk to the returned rig
// object, so a real GLB/VRoid model can replace this later without touching
// gameplay code.
// ---------------------------------------------------------------------------

const faceTexCache = new Map();

function makeFaceTexture(faceKey, fem) {
  const key = `${faceKey}_${fem}`;
  if (faceTexCache.has(key)) return faceTexCache.get(key);

  const f = FACES[faceKey] || FACES.softAnime;
  const cv = document.createElement('canvas');
  cv.width = 512; cv.height = 300;
  const g = cv.getContext('2d');
  g.clearRect(0, 0, 512, 300);

  const eyeW = 62 * f.eye, eyeH = 50 * f.eye;
  const cy = 130;

  for (const dir of [-1, 1]) {
    const cx = 256 + dir * 95;
    g.save();
    g.translate(cx, cy);

    // eye white
    g.fillStyle = '#ffffff';
    g.beginPath(); g.ellipse(0, 0, eyeW, eyeH, 0, 0, Math.PI * 2); g.fill();

    // iris with vertical gradient + pupil + highlights
    const grad = g.createLinearGradient(0, -eyeH, 0, eyeH);
    grad.addColorStop(0, '#1a1626');
    grad.addColorStop(0.45, f.iris);
    grad.addColorStop(1, lighten(f.iris, 60));
    g.fillStyle = grad;
    g.beginPath(); g.ellipse(0, 4, eyeW * 0.62, eyeH * 0.88, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#14101e';
    g.beginPath(); g.ellipse(0, 4, eyeW * 0.30, eyeH * 0.46, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.95)';
    g.beginPath(); g.ellipse(-eyeW * 0.22, -eyeH * 0.28, eyeW * 0.16, eyeH * 0.14, 0, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.ellipse(eyeW * 0.18, eyeH * 0.22, eyeW * 0.08, eyeH * 0.07, 0, 0, Math.PI * 2); g.fill();

    // upper lash line
    g.strokeStyle = '#181222';
    g.lineWidth = f.lash ? 13 : 8;
    g.lineCap = 'round';
    g.beginPath();
    g.moveTo(-eyeW * 1.02, -eyeH * 0.32);
    g.quadraticCurveTo(0, -eyeH * 1.18, eyeW * 1.05, -eyeH * 0.42);
    g.stroke();
    if (f.lash) {
      g.lineWidth = 6;
      g.beginPath();
      g.moveTo(dir * eyeW * 0.9, -eyeH * 0.62);
      g.lineTo(dir * eyeW * 1.25, -eyeH * 0.95);
      g.stroke();
    }

    // brow
    g.strokeStyle = '#241a30';
    g.lineWidth = 9;
    g.save();
    g.rotate((-dir * f.brow * Math.PI) / 180);
    g.beginPath();
    g.moveTo(-eyeW * 0.85, -eyeH * 1.55);
    g.quadraticCurveTo(0, -eyeH * 1.8, eyeW * 0.85, -eyeH * 1.5);
    g.stroke();
    g.restore();

    g.restore();
  }

  // nose + mouth
  g.strokeStyle = 'rgba(40,28,40,0.55)';
  g.lineWidth = 5; g.lineCap = 'round';
  g.beginPath(); g.moveTo(256, 178); g.lineTo(252, 192); g.stroke();

  g.strokeStyle = f.lips ? '#b8475e' : '#54323a';
  g.lineWidth = f.lips ? 9 : 6;
  g.beginPath();
  g.moveTo(232, 232);
  g.quadraticCurveTo(256, 244, 280, 232);
  g.stroke();

  if (fem) { // soft blush
    g.fillStyle = 'rgba(255,110,140,0.18)';
    for (const dir of [-1, 1]) {
      g.beginPath(); g.ellipse(256 + dir * 150, 195, 38, 20, 0, 0, Math.PI * 2); g.fill();
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

  const skinHex = SKINS[skin] || SKINS[0];
  const skinMat = toon(new THREE.Color(skinHex).getHex());
  const baseMat = toon(0x26242e);

  const root = new THREE.Group();
  const muscleW = THREE.MathUtils.lerp(0.92, 1.18, THREE.MathUtils.inverseLerp(0.6, 1.6, cfg.muscle));

  const legLen = 0.92 * cfg.legLen * cfg.height;
  const hipY = legLen;
  const torsoLen = 0.62 * cfg.height;
  const shoulderY = hipY + torsoLen * 0.82;
  const headR = 0.14 * cfg.headSize;
  const headY = hipY + torsoLen * 0.95 + 0.07 + headR;
  const shw = 0.235 * cfg.shoulders * muscleW;
  const hipw = 0.165 * cfg.hips;

  // pelvis
  const pelvis = group(root, [0, hipY + 0.04, 0]);
  sph(pelvis, baseMat, [0, 0, 0], [0.36 * cfg.hips, 0.23, 0.27 * cfg.hips]);
  sph(pelvis, baseMat, [0, -0.015, -0.07], [0.3 * cfg.hips, 0.2, 0.2 * cfg.glutes]);

  // torso
  const torso = group(root, [0, hipY + 0.06, 0]);
  torso.rotation.x = -cfg.posture * 0.07;
  sph(torso, baseMat, [0, torsoLen * 0.22, 0], [0.27 * cfg.waist, 0.26, 0.21 * cfg.waist]);
  sph(torso, baseMat, [0, torsoLen * 0.58, 0],
    [0.34 * cfg.shoulders * muscleW, 0.3, 0.235 * (fem ? 1 : cfg.chest) * muscleW]);
  if (fem) {
    sph(torso, baseMat, [0, torsoLen * 0.52, 0.055],
      [0.27 * cfg.chest, 0.155 * cfg.chest, 0.17 * cfg.chest]);
  }
  const shY = torsoLen * 0.76;
  sph(torso, baseMat, [-shw, shY, 0], [0.115 * muscleW, 0.115 * muscleW, 0.115 * muscleW]);
  sph(torso, baseMat, [shw, shY, 0], [0.115 * muscleW, 0.115 * muscleW, 0.115 * muscleW]);
  cyl(torso, skinMat, [0, torsoLen * 0.92, 0], [0.042, 0.13, 0.042]);
  const backAnchor = group(torso, [0, shY - 0.05, -0.16]);

  // arms
  function arm(dir) {
    const joint = group(torso, [dir * shw, shY, 0]);
    const th = 0.041 * cfg.arms * muscleW;
    cap(joint, skinMat, [0, -0.15, 0], th, 0.1);
    cap(joint, skinMat, [0, -0.4, 0], th * 0.82, 0.085);
    sph(joint, skinMat, [0, -0.55, 0], [0.085 * cfg.hands, 0.085 * cfg.hands, 0.085 * cfg.hands]);
    return joint;
  }
  const shoulderL = arm(-1), shoulderR = arm(1);

  // legs
  function leg(dir) {
    const joint = group(root, [dir * 0.1 * cfg.hips, hipY, 0]);
    const thighT = 0.061 * cfg.thighs * THREE.MathUtils.lerp(1, cfg.hips, 0.3);
    cap(joint, skinMat, [0, -0.215, 0], thighT, 0.14);
    cap(joint, skinMat, [0, -0.6, 0], 0.046 * cfg.calves, 0.12);
    cap(joint, baseMat, [0, -0.1, 0], thighT * 1.15, 0.07);
    const footY = -(hipY - 0.045);
    box(joint, skinMat, [0, footY, 0.055], [0.1 * cfg.feet, 0.075, 0.235 * cfg.feet]);
    return joint;
  }
  const hipL = leg(-1), hipR = leg(1);

  // head
  const headGroup = group(torso, [0, headY - (hipY + 0.06), 0]);
  sph(headGroup, skinMat, [0, 0, 0], [headR * 1.78, headR * 2.0, headR * 1.85]);
  sph(headGroup, skinMat, [0, -headR * 0.55, headR * 0.18], [headR * 1.45, headR * 1.1, headR * 1.4]);

  // anime face plane
  const faceTex = makeFaceTexture(faceKey, fem);
  const facePlane = new THREE.Mesh(
    new THREE.PlaneGeometry(headR * 1.85, headR * 1.1),
    new THREE.MeshBasicMaterial({ map: faceTex, transparent: true, depthWrite: false })
  );
  facePlane.position.set(0, -headR * 0.08, headR * 0.92);
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
