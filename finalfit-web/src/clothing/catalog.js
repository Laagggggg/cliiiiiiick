// The fashion catalog — 40 pieces across the 12 fictional brands.
// stats are 0-10 judge inputs: sil(houette), opium, street, lux(ury), goth,
// formal, y2k, risk, layer(ing).

const BLACK = 0x18171c, OFFBLACK = 0x242129, CREAM = 0xeee3cc, CHROME = 0xd9e0f2,
  BLOOD = 0x8c1a26, DENIM = 0x4d5c7a, OLIVE = 0x616647, PINK = 0xff59b3,
  CYAN = 0x40f2ff, VELVET = 0x471433, GOLD = 0xffd159;

function item(id, name, brand, category, slot, rarity, price, style, c1, c2, tags, stats) {
  const [sil = 5, opium = 0, street = 0, lux = 0, goth = 0, formal = 0, y2k = 0, risk = 3, layer = 3] = stats;
  return { id, name, brand, category, slot, rarity, price, style, c1, c2, tags,
    stats: { sil, opium, street, lux, goth, formal, y2k, risk, layer } };
}

const hair = (id, name, style, c1) =>
  item(id, name, 'FINAL FIT SALON', 'hair', 'hair', 'common', 0, style, c1, c1,
    ['hair'], [5, 2, 2, 2, 2, 2, 2, 2, 0]);

export const CATALOG = [
  // ---- tops ----
  item('top_hoodie_black', 'Shadow Cult Hoodie', 'VANTA VEIL', 'tops', 'top', 'uncommon', 240,
    'hoodie', BLACK, OFFBLACK, ['dark', 'oversized', 'streetwear', 'opium'], [7, 8, 7, 2, 6, 0, 1, 4, 6]),
  item('top_hoodie_cream', 'Cloud Money Hoodie', 'COTTON GODS', 'tops', 'top', 'common', 150,
    'hoodie', CREAM, 0xcfc4a8, ['cozy', 'neutral', 'streetwear'], [6, 1, 6, 4, 0, 0, 2, 2, 5]),
  item('top_mesh', 'Phantom Mesh Top', 'VANTA VEIL', 'tops', 'top', 'rare', 310,
    'mesh', 0x1c1a22, BLACK, ['dark', 'sheer', 'opium', 'goth', 'risky'], [8, 9, 4, 3, 8, 0, 2, 8, 4]),
  item('top_lace', 'Midnight Lace Blouse', 'ROYAL ROT', 'tops', 'top', 'rare', 380,
    'blouse', VELVET, BLACK, ['gothic', 'royal', 'elegant', 'dark'], [8, 6, 1, 6, 9, 6, 0, 6, 5]),
  item('top_tank_white', 'Saint Cotton Tank', 'HALO BOULEVARD', 'tops', 'top', 'common', 90,
    'tank', 0xf2f2f7, CREAM, ['clean', 'angelic', 'minimal'], [4, 0, 3, 5, 0, 1, 3, 1, 2]),
  item('top_tee_grim', 'Grim Oversized Tee', 'GRIM LUXE', 'tops', 'top', 'uncommon', 180,
    'tee', OFFBLACK, BLOOD, ['villain', 'dark', 'oversized', 'streetwear'], [6, 6, 7, 2, 5, 0, 1, 3, 4]),
  item('top_vest_nova', 'Tactical Panel Vest', 'NOVA CARTEL', 'tops', 'top', 'epic', 520,
    'vest', 0x2a2e33, CYAN, ['cyber', 'tactical', 'streetwear', 'techwear'], [8, 4, 9, 3, 3, 0, 4, 7, 8]),
  item('top_linen', 'Old Money Linen Shirt', 'LOFT MONEY', 'tops', 'top', 'rare', 420,
    'blouse', CREAM, 0xd9cfb5, ['oldmoney', 'quietluxury', 'linen', 'tailored'], [7, 0, 1, 9, 0, 7, 0, 2, 4]),

  // ---- outerwear ----
  item('out_cropped', 'Razor Cropped Jacket', 'VANTA VEIL', 'outerwear', 'outerwear', 'rare', 460,
    'cropped', BLACK, CHROME, ['dark', 'leather', 'opium', 'edgy'], [8, 8, 5, 5, 7, 1, 2, 6, 7]),
  item('out_trench', 'Black Parade Trench', 'GRIM LUXE', 'outerwear', 'outerwear', 'epic', 740,
    'trench', BLACK, OFFBLACK, ['villain', 'dramatic', 'dark', 'formal', 'opium'], [9, 9, 3, 7, 8, 7, 0, 7, 9]),
  item('out_fur', 'Empress Fur Coat', 'ROYAL ROT', 'outerwear', 'outerwear', 'grail', 1200,
    'fur', 0x33242e, VELVET, ['royal', 'gothic', 'luxury', 'statement'], [9, 7, 2, 9, 8, 5, 1, 9, 8]),
  item('out_puffer', 'Street King Puffer', 'SNEAKR TEMPLE', 'outerwear', 'outerwear', 'uncommon', 330,
    'puffer', 0x1f1f24, PINK, ['streetwear', 'oversized', 'winter'], [7, 3, 9, 3, 1, 0, 4, 4, 7]),
  item('out_cyber', 'Neon Circuit Jacket', 'CHROME SAINT', 'outerwear', 'outerwear', 'epic', 680,
    'cyber', 0x1a1a24, CYAN, ['cyber', 'chrome', 'neon', 'futuristic'], [8, 4, 7, 6, 2, 0, 6, 8, 7]),
  item('out_white_trench', 'Angel Mantle Trench', 'HALO BOULEVARD', 'outerwear', 'outerwear', 'epic', 690,
    'trench', CREAM, CHROME, ['angelic', 'luxury', 'clean', 'formal'], [9, 1, 2, 9, 0, 8, 1, 6, 8]),

  // ---- bottoms ----
  item('bot_leather', 'Serpent Leather Pants', 'VANTA VEIL', 'bottoms', 'bottom', 'rare', 390,
    'leather', BLACK, OFFBLACK, ['leather', 'dark', 'opium', 'goth'], [8, 8, 5, 6, 7, 2, 1, 5, 5]),
  item('bot_cargo', 'Field Ops Cargos', 'NOVA CARTEL', 'bottoms', 'bottom', 'uncommon', 220,
    'cargo', OLIVE, 0x383b2a, ['tactical', 'streetwear', 'baggy'], [7, 2, 8, 1, 1, 0, 3, 3, 6]),
  item('bot_baggy', 'Y2 Flood Baggy Jeans', 'SNEAKR TEMPLE', 'bottoms', 'bottom', 'common', 160,
    'baggy', DENIM, 0x3a4763, ['y2k', 'baggy', 'streetwear', 'denim'], [6, 1, 8, 1, 0, 0, 8, 3, 5]),
  item('bot_miniskirt', 'Vamp Mini Skirt', 'ROYAL ROT', 'bottoms', 'bottom', 'rare', 280,
    'miniskirt', BLACK, BLOOD, ['goth', 'y2k', 'dark', 'risky'], [7, 7, 4, 4, 8, 1, 7, 7, 4]),
  item('bot_pleated', 'Academy Pleated Skirt', 'NOIR ACADEMY', 'bottoms', 'bottom', 'uncommon', 190,
    'pleated', 0x21212e, BLOOD, ['darkacademia', 'elegant', 'school'], [6, 3, 3, 4, 4, 6, 2, 3, 4]),
  item('bot_tailored', 'Heir Tailored Slacks', 'LOFT MONEY', 'bottoms', 'bottom', 'rare', 360,
    'leather', 0xbfb29a, CREAM, ['oldmoney', 'tailored', 'quietluxury', 'formal'], [7, 0, 1, 9, 0, 8, 0, 2, 4]),

  // ---- shoes ----
  item('sho_platform', 'Gravity Platform Boots', 'STAGE DEMON', 'shoes', 'shoes', 'epic', 540,
    'platform', BLACK, CHROME, ['goth', 'platform', 'statement', 'opium'], [9, 8, 5, 5, 9, 2, 4, 8, 5]),
  item('sho_chunky', 'Temple Runner 900s', 'SNEAKR TEMPLE', 'shoes', 'shoes', 'rare', 420,
    'chunky', 0xe8e8ee, CYAN, ['hype', 'streetwear', 'chunky', 'y2k'], [7, 1, 9, 4, 0, 0, 7, 5, 4]),
  item('sho_designer', 'Saint Chrome Boots', 'CHROME SAINT', 'shoes', 'shoes', 'grail', 980,
    'designer', CHROME, 0x99a6c0, ['chrome', 'luxury', 'cyber', 'statement'], [9, 5, 4, 9, 3, 4, 5, 9, 5]),
  item('sho_loafers', 'Regatta Loafers', 'LOFT MONEY', 'shoes', 'shoes', 'uncommon', 310,
    'loafers', 0x59382a, GOLD, ['oldmoney', 'formal', 'quietluxury'], [6, 0, 1, 8, 0, 8, 0, 2, 3]),

  // ---- headwear ----
  item('hat_beanie', 'Crypt Beanie', 'VANTA VEIL', 'headwear', 'headwear', 'common', 80,
    'beanie', BLACK, OFFBLACK, ['dark', 'streetwear', 'cozy'], [4, 5, 6, 1, 4, 0, 1, 2, 3]),
  item('hat_cap', 'Cartel Snapback', 'NOVA CARTEL', 'headwear', 'headwear', 'common', 95,
    'cap', 0x1f1f26, CYAN, ['streetwear', 'cyber'], [4, 1, 7, 1, 0, 0, 4, 2, 3]),
  item('hat_halo', 'Seraph Halo Ring', 'HALO BOULEVARD', 'headwear', 'headwear', 'grail', 1500,
    'halo', GOLD, CREAM, ['angelic', 'statement', 'luxury', 'runway'], [9, 2, 1, 9, 1, 3, 2, 10, 4]),

  // ---- accessories ----
  item('acc_shades', 'Chrome Saint Shades', 'CHROME SAINT', 'accessories', 'face', 'rare', 350,
    'shades', 0x26262e, CHROME, ['chrome', 'cyber', 'cool', 'opium'], [6, 6, 6, 6, 3, 1, 5, 5, 3]),
  item('acc_chainbelt', 'Rot Chain Belt', 'ROYAL ROT', 'accessories', 'belt', 'uncommon', 210,
    'chainbelt', CHROME, BLACK, ['goth', 'y2k', 'chrome'], [5, 5, 4, 3, 6, 0, 6, 4, 5]),
  item('acc_bag', 'Vault Crossbody', 'LOFT MONEY', 'bags', 'bag', 'rare', 460,
    'crossbody', 0x59402e, GOLD, ['luxury', 'oldmoney', 'leather'], [6, 1, 4, 8, 0, 4, 1, 3, 6]),

  // ---- jewelry ----
  item('jwl_chain', 'Cuban Eclipse Chain', 'GRIM LUXE', 'jewelry', 'necklace', 'epic', 620,
    'chain', GOLD, CHROME, ['luxury', 'streetwear', 'statement'], [6, 4, 7, 8, 2, 2, 3, 5, 5]),
  item('jwl_choker', 'Obsidian Choker', 'VANTA VEIL', 'jewelry', 'necklace', 'uncommon', 180,
    'choker', BLACK, CHROME, ['goth', 'dark', 'opium'], [5, 7, 3, 3, 8, 1, 3, 4, 4]),
  item('jwl_hoops', 'Gilded Hoops', 'HALO BOULEVARD', 'jewelry', 'earrings', 'uncommon', 160,
    'hoops', GOLD, CREAM, ['luxury', 'clean', 'elegant'], [4, 1, 4, 7, 0, 4, 3, 2, 3]),
  item('jwl_studs', 'Void Piercing Set', 'STAGE DEMON', 'jewelry', 'earrings', 'rare', 240,
    'studs', CHROME, BLACK, ['goth', 'edgy', 'opium', 'punk'], [5, 7, 5, 2, 8, 0, 3, 6, 3]),

  // ---- hair ----
  hair('hair_bob', 'Onyx Anime Bob', 'hairBob', 0x141318),
  hair('hair_long', 'Raven Long & Straight', 'hairLong', 0x141318),
  hair('hair_wolf', 'Midnight Wolf Cut', 'hairWolf', 0x1c1a20),
  hair('hair_spiky', 'Hero Spikes', 'hairSpiky', 0x17141d),
  hair('hair_slick', 'Slicked Villain', 'hairSlick', 0x121116),
  hair('hair_curly', 'Cloud Curls', 'hairCurly', 0x241710),
  hair('hair_ponytail', 'Editorial Ponytail', 'hairPonytail', 0x59402b),
  hair('hair_twintails', 'Neon Twin Tails', 'hairTwintails', 0x33163d),
  hair('hair_braids', 'Crown Braids', 'hairBraids', 0x171008),
  hair('hair_shorthood', 'Hood-Ready Crop', 'hairCrop', 0x1a191e),
];

export const RARITY_COLOR = {
  common: '#b3b3bd', uncommon: '#66e680', rare: '#5999ff', epic: '#9e40ff', grail: '#ffd159',
};

export const byCategory = (cat) => CATALOG.filter((i) => i.category === cat);
export const findItem = (id) => CATALOG.find((i) => i.id === id);

export const THEME = {
  name: 'OPIUM NIGHT',
  desc: 'Black-on-black drama. Leather, chrome, layers, gothic luxury.',
  required: ['dark', 'opium', 'goth', 'leather'],
  bonus: ['chrome', 'oversized', 'statement', 'luxury', 'dramatic', 'villain', 'sheer'],
  penalty: ['clean', 'angelic', 'oldmoney', 'cozy', 'y2k', 'linen'],
};
