// Adult avatar presets, faces and skin tones. BodyConfig values are
// multipliers (1 = neutral) so they can later drive blendshapes on real
// rigged anime models.

export const PRESETS = {
  femaleCurvy: {
    name: 'Female · Curvy Anime', fem: true,
    body: { shoulders: 0.86, chest: 1.35, waist: 0.74, hips: 1.3, thighs: 1.25, glutes: 1.35, legLen: 1.02, posture: 0.4 },
    face: 'softAnime', hair: 'hair_bob',
  },
  femaleRunway: {
    name: 'Female · Tall Runway', fem: true,
    body: { height: 1.08, legLen: 1.12, shoulders: 0.92, chest: 1.05, waist: 0.72, hips: 1.05, thighs: 0.9, calves: 0.9, posture: 0.8 },
    face: 'elegantRunway', hair: 'hair_long',
  },
  femaleStreet: {
    name: 'Female · Streetwear', fem: true,
    body: { shoulders: 0.9, chest: 1.12, waist: 0.82, hips: 1.15, thighs: 1.1, glutes: 1.15, posture: -0.1 },
    face: 'cuteStreet', hair: 'hair_twintails',
  },
  maleLean: {
    name: 'Male · Lean Model', fem: false,
    body: { height: 1.05, shoulders: 1.12, chest: 0.95, waist: 0.85, hips: 0.88, legLen: 1.08, muscle: 0.95, posture: 0.6 },
    face: 'sharpModel', hair: 'hair_slick',
  },
  maleHero: {
    name: 'Male · Anime Hero', fem: false,
    body: { height: 1.07, shoulders: 1.35, chest: 1.2, waist: 0.92, hips: 0.95, arms: 1.35, thighs: 1.2, calves: 1.15, muscle: 1.5, posture: 0.7 },
    face: 'mascSharp', hair: 'hair_spiky',
  },
  maleStreet: {
    name: 'Male · Streetwear', fem: false,
    body: { shoulders: 1.15, chest: 1.02, waist: 0.95, hips: 0.92, arms: 1.1, muscle: 1.1, posture: -0.3 },
    face: 'mascSoft', hair: 'hair_wolf',
  },
  andro: {
    name: 'Androgynous · High Fashion', fem: true,
    body: { height: 1.06, shoulders: 1.0, chest: 0.95, waist: 0.78, hips: 0.98, legLen: 1.1, posture: 0.9 },
    face: 'androEditorial', hair: 'hair_ponytail',
  },
};

export const SLIDERS = [
  ['height', 'Height', 0.85, 1.2],
  ['headSize', 'Head Size', 0.8, 1.25],
  ['shoulders', 'Shoulders', 0.7, 1.5],
  ['chest', 'Chest', 0.7, 1.6],
  ['waist', 'Waist', 0.6, 1.4],
  ['hips', 'Hips', 0.7, 1.55],
  ['arms', 'Arm Thickness', 0.7, 1.6],
  ['legLen', 'Leg Length', 0.85, 1.2],
  ['thighs', 'Thighs', 0.7, 1.55],
  ['calves', 'Calves', 0.7, 1.4],
  ['glutes', 'Glutes', 0.7, 1.6],
  ['muscle', 'Muscle', 0.6, 1.6],
  ['scale', 'Body Scale', 0.9, 1.12],
  ['posture', 'Posture', -1, 1],
  ['hands', 'Hand Size', 0.75, 1.3],
  ['feet', 'Foot Size', 0.75, 1.35],
];

export function defaultBody() {
  return {
    height: 1, headSize: 1, shoulders: 1, chest: 1, waist: 1, hips: 1,
    arms: 1, legLen: 1, thighs: 1, calves: 1, glutes: 1, muscle: 1,
    scale: 1, posture: 0, hands: 1, feet: 1,
  };
}

export function bodyFor(presetKey) {
  return { ...defaultBody(), ...(PRESETS[presetKey]?.body || {}) };
}

// eyeScale, browAngle (deg, + = fierce), iris color, lips, lashes
export const FACES = {
  softAnime:     { name: 'Soft Anime',       eye: 1.35, brow: -5,  iris: '#58a6f0', lips: true,  lash: true },
  sharpModel:    { name: 'Sharp Model',      eye: 0.95, brow: 10,  iris: '#73655a', lips: false, lash: false },
  villain:       { name: 'Serious Villain',  eye: 0.85, brow: 18,  iris: '#c02540', lips: false, lash: false },
  cuteStreet:    { name: 'Cute Streetwear',  eye: 1.28, brow: -2,  iris: '#8d66dd', lips: true,  lash: true },
  elegantRunway: { name: 'Elegant Runway',   eye: 1.12, brow: 6,   iris: '#4d8c80', lips: true,  lash: true },
  mascSharp:     { name: 'Masculine Sharp',  eye: 0.82, brow: 14,  iris: '#5a5a66', lips: false, lash: false },
  mascSoft:      { name: 'Masculine Soft',   eye: 0.95, brow: 2,   iris: '#66503a', lips: false, lash: false },
  androEditorial:{ name: 'Andro Editorial',  eye: 1.12, brow: 8,   iris: '#ccb24d', lips: true,  lash: true },
};

export const SKINS = ['#fadcc2', '#edc29e', '#cc9973', '#9e7052', '#734f3a'];
