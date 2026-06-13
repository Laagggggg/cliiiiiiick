import { toon, neon, chrome, glossy, sheer, sph, box, cap, cyl, torus } from '../core/materials.js';

// ---------------------------------------------------------------------------
// Builds visible 3D meshes for every catalog item and attaches them to the
// avatar's body: sleeves ride the arm joints (they swing while walking),
// pants ride the leg joints, hair sits on the head. Returns every spawned
// piece so unequip can remove them. Drip must be SEEN.
// ---------------------------------------------------------------------------

export function equipItem(rig, item) {
  const pieces = [];
  const track = (mesh) => { pieces.push(mesh); return mesh; };
  const prim = toon(item.c1);
  const sec = toon(item.c2);
  const chromeSec = chrome(item.c2);
  const { torsoLen, shw, headR } = rig.dims;
  const T = rig.torso, P = rig.pelvis, H = rig.headGroup;

  // body-aware fit metrics — mirror the builder so clothes wrap the curvy body
  const cfg = rig.cfg || {};
  const lerp = (a, b, t) => a + (b - a) * t;
  const invlerp = (a, b, v) => Math.min(1, Math.max(0, (v - a) / (b - a)));
  const muscleW = lerp(0.92, 1.18, invlerp(0.6, 1.6, cfg.muscle ?? 1));
  const hipsK = cfg.hips ?? 1;
  const thighsK = (cfg.thighs ?? 1) * lerp(1, hipsK, 0.3);
  const bodyThighR = 0.093 * thighsK;     // body thigh radius (builder)
  const bodyCalfR = 0.07 * (cfg.calves ?? 1);
  const bodyArmR = 0.05 * (cfg.arms ?? 1) * muscleW;

  const sleeves = (extra, len, mat) => {
    const r = bodyArmR + 0.018 + extra;
    for (const j of [rig.joints.shoulderL, rig.joints.shoulderR]) {
      track(cap(j, mat, [0, 0.01, 0], r * 1.25, 0.05));     // cover shoulder ball
      track(cap(j, mat, [0, -len * 0.5, 0], r, len * 0.32));
    }
  };
  const pantsLeg = (widthMul, calfMul, mat, full = true) => {
    for (const j of [rig.joints.hipL, rig.joints.hipR]) {
      track(cap(j, mat, [0, -0.05, 0], bodyThighR * widthMul + 0.014, 0.06)); // upper-thigh/hip cover
      track(cap(j, mat, [0, -0.21, 0], bodyThighR * widthMul + 0.012, 0.13)); // thigh
      if (full) track(cap(j, mat, [0, -0.57, 0], bodyCalfR * calfMul + 0.012, 0.13)); // calf
    }
  };
  const hipWrap = (mat, s = 1) =>
    track(sph(P, mat, [0, -0.02, 0], [(0.36 * hipsK + 0.03) * s, 0.27, (0.30 * hipsK + 0.03) * s]));
  const eachFoot = (fn) => {
    for (const j of [rig.joints.hipL, rig.joints.hipR]) {
      const footY = -(rig.dims.hipY - 0.045);
      fn(j, footY);
    }
  };

  switch (item.style) {
    // ============================== tops ==============================
    case 'hoodie':
      track(box(T, prim, [0, torsoLen * 0.42, 0], [shw * 2.45, torsoLen * 0.85, 0.36]));
      track(box(T, sec, [0, torsoLen * 0.18, 0.185], [shw * 1.1, 0.12, 0.03]));
      track(sph(T, prim, [0, torsoLen * 0.88, -0.13], [0.24, 0.2, 0.22]));
      sleeves(0.022, 0.55, prim);
      break;
    case 'mesh':
      track(cap(T, sheer(item.c1, 0.4), [0, torsoLen * 0.45, 0], shw * 0.78, 0.14));
      track(cyl(T, sec, [0, torsoLen * 0.88, 0], [0.055, 0.03, 0.055]));
      break;
    case 'blouse':
      track(box(T, prim, [0, torsoLen * 0.42, 0], [shw * 2.05, torsoLen * 0.8, 0.35]));
      track(box(T, sec, [0, torsoLen * 0.84, 0.06], [shw * 1.1, 0.05, 0.14]));
      sleeves(0.006, 0.52, sheer(item.c1, 0.6));
      break;
    case 'tank':
      track(box(T, prim, [0, torsoLen * 0.42, 0], [shw * 1.75, torsoLen * 0.78, 0.34]));
      break;
    case 'tee':
      track(box(T, prim, [0, torsoLen * 0.38, 0], [shw * 2.5, torsoLen * 0.88, 0.36]));
      track(box(T, sec, [0, torsoLen * 0.45, 0.185], [0.16, 0.16, 0.02]));
      sleeves(0.022, 0.22, prim);
      break;
    case 'vest':
      track(box(T, prim, [0, torsoLen * 0.5, 0], [shw * 2.2, torsoLen * 0.62, 0.4]));
      track(box(T, sec, [-shw * 0.55, torsoLen * 0.38, 0.21], [0.1, 0.1, 0.05]));
      track(box(T, sec, [shw * 0.55, torsoLen * 0.38, 0.21], [0.1, 0.1, 0.05]));
      track(box(T, neon(item.c2), [0, torsoLen * 0.62, 0.205], [shw * 2.0, 0.018, 0.02]));
      break;

    // =========================== outerwear ============================
    case 'cropped':
      for (const d of [-1, 1])
        track(box(T, prim, [d * shw * 0.62, torsoLen * 0.58, 0], [shw * 1.25, torsoLen * 0.52, 0.4]));
      track(box(T, chromeSec, [0, torsoLen * 0.84, -0.02], [shw * 1.5, 0.05, 0.22]));
      sleeves(0.014, 0.56, prim);
      break;
    case 'trench':
      for (const d of [-1, 1])
        track(box(T, prim, [d * shw * 0.68, torsoLen * 0.2 - 0.18, -0.01], [shw * 1.3, 1.05, 0.38]));
      track(box(T, prim, [0, torsoLen * 0.2 - 0.18, -0.135], [shw * 2.2, 1.05, 0.1]));
      track(box(T, sec, [0, torsoLen * 0.18, 0], [shw * 2.65, 0.05, 0.42]));
      track(box(T, sec, [-shw * 0.45, torsoLen * 0.7, 0.185], [0.05, 0.22, 0.025], [0, 0, 0.31]));
      track(box(T, sec, [shw * 0.45, torsoLen * 0.7, 0.185], [0.05, 0.22, 0.025], [0, 0, -0.31]));
      sleeves(0.018, 0.58, prim);
      break;
    case 'fur':
      for (const d of [-1, 1])
        track(box(T, prim, [d * shw * 0.75, torsoLen * 0.25 - 0.12, -0.01], [shw * 1.6, 0.95, 0.46]));
      track(box(T, prim, [0, torsoLen * 0.25 - 0.12, -0.16], [shw * 2.6, 0.95, 0.12]));
      for (let i = 0; i < 7; i++)
        track(sph(T, sec, [-shw * 1.2 + (i / 6) * shw * 2.4, torsoLen * 0.82, 0.04], [0.11, 0.11, 0.11]));
      sleeves(0.042, 0.56, prim);
      break;
    case 'puffer':
      for (let i = 0; i < 4; i++)
        track(cap(T, prim, [0, torsoLen * (0.16 + i * 0.18), 0], 0.105, shw * 0.95, [0, 0, Math.PI / 2]));
      track(box(T, sec, [0, torsoLen * 0.45, 0.2], [0.02, torsoLen * 0.6, 0.015]));
      sleeves(0.04, 0.55, prim);
      break;
    case 'cyber':
      track(box(T, prim, [0, torsoLen * 0.52, 0], [shw * 2.35, torsoLen * 0.62, 0.4]));
      track(box(T, neon(item.c2), [0, torsoLen * 0.3, 0], [shw * 2.4, 0.02, 0.41]));
      track(sph(T, chromeSec, [-shw, torsoLen * 0.78, 0], [0.15, 0.15, 0.15]));
      track(sph(T, chromeSec, [shw, torsoLen * 0.78, 0], [0.15, 0.15, 0.15]));
      sleeves(0.018, 0.55, prim);
      break;

    // ============================ bottoms =============================
    case 'leather': {
      const shiny = glossy(item.c1, 0.18);
      pantsLeg(1.12, 1.12, shiny); hipWrap(shiny);
      break;
    }
    case 'cargo':
      pantsLeg(1.5, 1.6, prim); hipWrap(prim, 1.05);
      track(box(rig.joints.hipL, sec, [-0.115, -0.28, 0], [0.05, 0.12, 0.1]));
      track(box(rig.joints.hipR, sec, [0.115, -0.28, 0], [0.05, 0.12, 0.1]));
      break;
    case 'baggy':
      pantsLeg(1.9, 2.5, prim); hipWrap(prim, 1.1);
      break;
    case 'miniskirt':
      track(cyl(P, prim, [0, -0.06, 0], [0.21 * hipsK, 0.1, 0.18 * hipsK]));
      track(cyl(P, sec, [0, -0.13, 0], [0.24 * hipsK, 0.07, 0.21 * hipsK]));
      break;
    case 'pleated':
      track(cyl(P, prim, [0, -0.1, 0], [0.23 * hipsK, 0.17, 0.2 * hipsK]));
      for (let i = 0; i < 8; i++) {
        const a = (i * Math.PI * 2) / 8;
        track(box(P, sec, [Math.cos(a) * 0.215, -0.165, Math.sin(a) * 0.185],
          [0.06, 0.06, 0.02], [0, -a, 0]));
      }
      break;

    // ============================= shoes ==============================
    case 'platform':
      eachFoot((j, fy) => {
        track(box(j, sec, [0, fy - 0.005, 0.01], [0.135, 0.115, 0.275]));
        track(box(j, prim, [0, fy + 0.1, 0.01], [0.125, 0.1, 0.26]));
        track(cyl(j, prim, [0, fy + 0.22, -0.04], [0.058, 0.17, 0.058]));
      });
      break;
    case 'chunky':
      eachFoot((j, fy) => {
        track(box(j, prim, [0, fy + 0.025, 0.01], [0.13, 0.105, 0.285]));
        track(box(j, sec, [0, fy - 0.035, 0.01], [0.14, 0.05, 0.3]));
      });
      break;
    case 'designer':
      eachFoot((j, fy) => {
        track(box(j, chrome(item.c1), [0, fy + 0.02, 0.02], [0.105, 0.095, 0.29]));
        track(cyl(j, chrome(item.c1), [0, fy + 0.16, -0.04], [0.05, 0.14, 0.05]));
      });
      break;
    case 'loafers':
      eachFoot((j, fy) => {
        track(box(j, prim, [0, fy + 0.005, 0.01], [0.11, 0.085, 0.26]));
        track(box(j, chromeSec, [0, fy + 0.05, 0.06], [0.05, 0.012, 0.02]));
      });
      break;

    // ============================ headwear ============================
    case 'beanie':
      track(sph(H, prim, [0, headR * 0.65, -headR * 0.1], [headR * 1.95, headR * 1.35, headR * 2.0]));
      track(cyl(H, sec, [0, headR * 0.35, -headR * 0.1], [headR * 0.96, headR * 0.18, headR * 0.985]));
      break;
    case 'cap':
      track(sph(H, prim, [0, headR * 0.7, -headR * 0.05], [headR * 1.92, headR * 1.1, headR * 1.95]));
      track(box(H, sec, [0, headR * 0.55, headR * 1.25], [headR * 1.5, 0.015, headR * 1.1]));
      break;
    case 'halo':
      track(torus(H, neon(item.c1, 3.4), [0, headR * 1.9, 0], headR * 1.1, 0.02, [Math.PI / 2, 0, 0]));
      break;

    // ======================= accessories/jewelry ======================
    case 'shades':
      track(box(rig.faceAnchor, chrome(item.c2), [0, 0.012, 0.012], [headR * 1.75, 0.035, 0.02]));
      for (const d of [-1, 1])
        track(box(rig.faceAnchor, prim, [d * headR * 0.88, 0.012, -headR * 0.5], [0.008, 0.012, headR * 1.1]));
      break;
    case 'chain': {
      const m = chrome(item.c1);
      for (let i = 0; i < 9; i++) {
        const a = -1.25 + (i / 8) * 2.5;
        track(sph(T, m, [Math.sin(a) * 0.14,
          torsoLen * 0.7 + Math.abs(Math.sin(a)) * 0.1,
          0.145 - Math.abs(Math.sin(a)) * 0.03], [0.028, 0.028, 0.028]));
      }
      track(box(T, m, [0, torsoLen * 0.7 - 0.045, 0.155], [0.035, 0.045, 0.012]));
      break;
    }
    case 'choker':
      track(torus(T, prim, [0, torsoLen * 0.92, 0], 0.055, 0.011, [Math.PI / 2, 0, 0]));
      track(sph(T, chromeSec, [0, torsoLen * 0.92, 0.062], [0.022, 0.022, 0.022]));
      break;
    case 'chainbelt': {
      const m = chrome(item.c1);
      for (let i = 0; i < 10; i++) {
        const a = (i * Math.PI * 2) / 10;
        track(sph(P, m, [Math.cos(a) * 0.2, -0.02 - Math.sin(a) * 0.025, Math.sin(a) * 0.155],
          [0.03, 0.03, 0.03]));
      }
      break;
    }
    case 'crossbody':
      track(box(T, sec, [0, torsoLen * 0.5, 0.175], [0.045, torsoLen * 0.75, 0.015], [0, 0, 0.61]));
      track(box(T, prim, [shw * 0.95, torsoLen * 0.12, 0.05], [0.09, 0.14, 0.19]));
      track(box(T, chromeSec, [shw * 0.95, torsoLen * 0.16, 0.15], [0.03, 0.02, 0.01]));
      break;
    case 'hoops':
      for (const d of [-1, 1])
        track(torus(H, chrome(item.c1), [d * headR * 0.92, -headR * 0.35, 0], 0.028, 0.005,
          [0, Math.PI / 2, 0]));
      break;
    case 'studs':
      for (const d of [-1, 1])
        track(sph(H, chrome(item.c1), [d * headR * 0.92, -headR * 0.15, 0], [0.016, 0.016, 0.016]));
      track(sph(H, chrome(item.c1), [headR * 0.45, headR * 0.32, headR * 0.82], [0.012, 0.012, 0.012]));
      break;

    // ============================== hair ==============================
    default:
      buildHair(rig, item, prim, track);
      break;
  }
  return pieces;
}

function buildHair(rig, item, prim, track) {
  const { headR: hr } = rig.dims;
  const A = rig.hairAnchor;

  const scalp = (size = 1) =>
    track(sph(A, prim, [0, hr * 0.22, -hr * 0.18], [hr * 2.0 * size, hr * 2.0 * size, hr * 2.05 * size]));
  const bangs = () =>
    track(box(A, prim, [0, hr * 0.78, hr * 0.72], [hr * 1.65, hr * 0.45, hr * 0.55]));

  switch (item.style) {
    case 'hairBob':
      scalp(1.04); bangs();
      for (const d of [-1, 1])
        track(box(A, prim, [d * hr * 0.92, -hr * 0.15, hr * 0.15], [hr * 0.38, hr * 1.5, hr * 0.85]));
      break;
    case 'hairLong':
      scalp(1.03); bangs();
      track(box(A, prim, [0, -hr * 2.1, -hr * 0.85], [hr * 1.8, hr * 4.2, hr * 0.5]));
      for (const d of [-1, 1])
        track(box(A, prim, [d * hr * 0.85, -hr * 0.9, hr * 0.35], [hr * 0.3, hr * 2.4, hr * 0.3]));
      break;
    case 'hairWolf': {
      scalp(1.05); bangs();
      let seed = 7;
      const rand = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
      for (let i = 0; i < 6; i++) {
        const ang = rand() * Math.PI * 2, tilt = 0.35 + rand() * 0.6;
        track(box(A, prim, [Math.sin(ang) * hr * 0.95, hr * 0.1, Math.cos(ang) * hr * 0.95],
          [hr * 0.35, hr * 1.1, hr * 0.25], [tilt, ang, 0]));
      }
      break;
    }
    case 'hairSpiky':
      scalp(1.02);
      for (let i = 0; i < 8; i++) {
        const ang = (i * Math.PI * 2) / 8;
        track(box(A, prim,
          [Math.sin(ang) * hr * 0.75, hr * 0.95, Math.cos(ang) * hr * 0.75],
          [hr * 0.3, hr * 0.95, hr * 0.3],
          [Math.cos(ang) * 0.6, 0, -Math.sin(ang) * 0.6]));
      }
      break;
    case 'hairSlick':
      scalp(1.0);
      track(sph(A, prim, [0, hr * 0.1, -hr * 0.55], [hr * 1.7, hr * 1.7, hr * 1.4]));
      break;
    case 'hairCurly':
      scalp(1.0);
      for (let i = 0; i < 10; i++) {
        const ang = (i * Math.PI * 2) / 10, lift = 0.4 + (i % 3) * 0.3;
        track(sph(A, prim,
          [Math.sin(ang) * hr * 0.85, hr * lift, Math.cos(ang) * hr * 0.85 - hr * 0.1],
          [hr * 0.62, hr * 0.62, hr * 0.62]));
      }
      break;
    case 'hairPonytail':
      scalp(1.0); bangs();
      track(sph(A, prim, [0, hr * 0.55, -hr * 1.05], [hr * 0.45, hr * 0.45, hr * 0.45]));
      track(cap(A, prim, [0, -hr * 0.4, -hr * 1.35], hr * 0.28, hr * 0.8, [-0.31, 0, 0]));
      break;
    case 'hairTwintails':
      scalp(1.02); bangs();
      for (const d of [-1, 1]) {
        track(sph(A, prim, [d * hr * 1.0, hr * 0.5, -hr * 0.3], [hr * 0.4, hr * 0.4, hr * 0.4]));
        track(cap(A, prim, [d * hr * 1.25, -hr * 0.85, -hr * 0.35], hr * 0.25, hr * 0.85,
          [0, 0, -d * 0.24]));
      }
      break;
    case 'hairBraids':
      scalp(1.02); bangs();
      for (const d of [-1, 1])
        for (let i = 0; i < 3; i++)
          track(sph(A, prim, [d * hr * 0.85, -hr * (0.55 + i * 0.55), hr * 0.3],
            [hr * 0.34, hr * 0.45, hr * 0.34]));
      break;
    default: // hairCrop
      scalp(0.98); bangs();
      break;
  }
}
