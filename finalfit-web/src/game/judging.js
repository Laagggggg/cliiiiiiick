import { THEME } from '../clothing/catalog.js';

// Rule-based judging over clothing tags and item stats — no AI, fully
// deterministic and explainable.

const RARITY_VALUE = { common: 2, uncommon: 4, rare: 6, epic: 8, grail: 10 };

const CATS = [
  ['theme', 'THEME ACCURACY'],
  ['color', 'COLOR HARMONY'],
  ['silhouette', 'SILHOUETTE'],
  ['layering', 'LAYERING'],
  ['accessory', 'ACCESSORY BALANCE'],
  ['originality', 'ORIGINALITY'],
  ['risk', 'RISK LEVEL'],
  ['cohesion', 'COHESION'],
];

export function judgeOutfit(items, theme = THEME) {
  const wearables = items.filter((i) => i.category !== 'hair');
  const s = {};

  if (wearables.length === 0) {
    return {
      total: 4, rank: 'D',
      cats: Object.fromEntries(CATS.map(([k]) => [k, 0])),
      catLabels: CATS,
      comments: ['You walked the OPIUM NIGHT runway in the base layer. Bold. Insane, but bold.'],
      best: 'COURAGE', worst: 'EVERYTHING ELSE',
      tip: 'Equip a top, bottom and shoes before presenting.',
    };
  }

  // theme accuracy
  let themePts = 0;
  for (const it of wearables) {
    for (const t of it.tags) {
      if (theme.required.includes(t)) themePts += 2.4;
      else if (theme.bonus.includes(t)) themePts += 1.2;
      else if (theme.penalty.includes(t)) themePts -= 2.2;
    }
  }
  s.theme = clamp((themePts / (wearables.length * 2.2)) * 50 + 30);

  // color harmony — hue spread of primary colors (dark/mono reads harmonic)
  const hues = wearables.map((i) => hueOf(i.c1)).filter((h) => h !== null);
  if (hues.length <= 1) s.color = 82;
  else {
    const spread = hueSpread(hues);
    s.color = clamp(95 - spread * 0.55);
  }

  const avg = (k) => wearables.reduce((a, i) => a + i.stats[k], 0) / wearables.length;
  s.silhouette = clamp(avg('sil') * 10.5);

  // layering — slot coverage + layering stats
  const slots = new Set(wearables.map((i) => i.slot));
  const coreSlots = ['top', 'bottom', 'shoes'];
  const coreCovered = coreSlots.filter((c) => slots.has(c)).length;
  const extras = ['outerwear', 'necklace', 'headwear', 'face', 'belt', 'bag', 'earrings']
    .filter((c) => slots.has(c)).length;
  s.layering = clamp(coreCovered * 18 + extras * 8 + avg('layer') * 2.5);

  // accessory balance — sweet spot is 2-4 accessories
  const accCount = wearables.filter((i) =>
    ['necklace', 'earrings', 'face', 'belt', 'bag', 'headwear'].includes(i.slot)).length;
  s.accessory = accCount === 0 ? 25 : accCount <= 4 ? 70 + accCount * 7 : 88 - (accCount - 4) * 14;
  s.accessory = clamp(s.accessory);

  // originality — rarity + brand variety
  const brands = new Set(wearables.map((i) => i.brand));
  const rare = wearables.reduce((a, i) => a + RARITY_VALUE[i.rarity], 0) / wearables.length;
  s.originality = clamp(rare * 7 + Math.min(brands.size, 4) * 6);

  s.risk = clamp(avg('risk') * 10.5);

  // cohesion — shared tags across the fit + brand focus
  const tagCounts = {};
  for (const it of wearables) for (const t of it.tags) tagCounts[t] = (tagCounts[t] || 0) + 1;
  const shared = Object.values(tagCounts).filter((n) => n >= Math.max(2, wearables.length * 0.4)).length;
  const brandFocus = brands.size <= 2 ? 14 : brands.size === 3 ? 6 : 0;
  s.cohesion = clamp(34 + shared * 11 + brandFocus);

  const weights = { theme: 0.22, color: 0.12, silhouette: 0.13, layering: 0.14,
    accessory: 0.1, originality: 0.1, risk: 0.07, cohesion: 0.12 };
  const total = Math.round(CATS.reduce((a, [k]) => a + s[k] * weights[k], 0));

  const sorted = [...CATS].sort((a, b) => s[b[0]] - s[a[0]]);
  const best = sorted[0][1], worst = sorted[sorted.length - 1][1];

  const rank = total >= 88 ? 'S' : total >= 75 ? 'A' : total >= 60 ? 'B' : total >= 42 ? 'C' : 'D';

  const comments = buildComments(s, theme, wearables);
  const tip = buildTip(sorted[sorted.length - 1][0], slots);

  return {
    total, rank, cats: Object.fromEntries(CATS.map(([k]) => [k, Math.round(s[k])])),
    catLabels: CATS, comments, best, worst, tip,
  };
}

function buildComments(s, theme, items) {
  const out = [];
  out.push(s.theme >= 70
    ? `<b>Vex Noir (GRIM LUXE):</b> "This UNDERSTANDS ${theme.name}. The darkness is intentional. I'm moved."`
    : s.theme >= 45
      ? `<b>Vex Noir (GRIM LUXE):</b> "I see the idea of ${theme.name}… from a distance. Commit harder."`
      : `<b>Vex Noir (GRIM LUXE):</b> "Did you read the theme card? ${theme.name}. This is a brunch fit."`);
  out.push(s.cohesion >= 60
    ? '<b>Saint Aurelia (HALO BLVD):</b> "Every piece is having the same conversation. Cohesion: divine."'
    : '<b>Saint Aurelia (HALO BLVD):</b> "The pieces are arguing with each other, darling."');
  out.push(s.risk >= 65
    ? '<b>Kazuo Rin (NOVA CARTEL):</b> "There\'s a statement piece doing real damage here. Respect."'
    : '<b>Kazuo Rin (NOVA CARTEL):</b> "Safe. Clean, but safe. Where is the piece that scares me?"');
  return out;
}

function buildTip(worstKey, slots) {
  switch (worstKey) {
    case 'theme': return 'Lean into the theme tags — for OPIUM NIGHT think dark, leather, chrome, oversized layers.';
    case 'color': return 'Tighten the palette: pick one accent color and keep the rest tonal.';
    case 'layering': return !slots.has('outerwear')
      ? 'Add an outer layer — a trench or jacket instantly upgrades the silhouette.'
      : 'Cover the core slots (top, bottom, shoes) before stacking accessories.';
    case 'accessory': return 'Two to four accessories is the sweet spot — a chain, shades, and one wildcard.';
    case 'originality': return 'Hunt rarer pieces — epic and grail items carry runway weight.';
    case 'risk': return 'Add one statement piece: platforms, a halo, a fur coat. Make the judges blink.';
    case 'cohesion': return 'Pick a lane — match brands or aesthetics so the fit reads as one idea.';
    default: return 'Balance the proportions: oversized top with a sharper bottom, or the reverse.';
  }
}

function clamp(v) { return Math.max(0, Math.min(100, v)); }

function hueOf(c) {
  const r = (c >> 16) / 255, g = ((c >> 8) & 255) / 255, b = (c & 255) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  if (max - min < 0.09) return null; // achromatic — doesn't fight any palette
  let h;
  if (max === r) h = ((g - b) / (max - min)) % 6;
  else if (max === g) h = (b - r) / (max - min) + 2;
  else h = (r - g) / (max - min) + 4;
  return ((h * 60) + 360) % 360;
}

function hueSpread(hues) {
  let worst = 0;
  for (let i = 0; i < hues.length; i++)
    for (let j = i + 1; j < hues.length; j++) {
      let d = Math.abs(hues[i] - hues[j]);
      if (d > 180) d = 360 - d;
      worst = Math.max(worst, d);
    }
  return worst;
}
