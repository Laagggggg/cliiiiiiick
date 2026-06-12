# FINAL FIT — Web (Vite + Three.js)

A playable 3D anime fashion battle prototype that runs in your browser.
Walk a neon fashion store in third person, raid the racks under a 10-minute
round timer, equip clothing that **visibly appears on your avatar**, then
present the fit on the runway for a judged score out of 100.

This build is verified end-to-end by an automated headless-browser test
(menu → creator → store → equip → runway → results, zero console errors).

## Run it

```bash
cd finalfit-web
npm install
npm run dev
```

Open the printed URL (usually `http://localhost:5173`). That's it.

Useful URL flags:
- `?fast` — 30-second rounds for quick testing
- `?potato` — disables bloom/shadows for weak machines

## Controls

| Input | Action |
|---|---|
| WASD | walk |
| Shift | sprint |
| Mouse (click canvas first) | orbit camera |
| E | browse rack / close panel |
| R | present your fit on the runway |
| Esc | close browse panel |

## What's in the game

- **Character creator** — 7 adult anime-styled presets (curvy / tall runway /
  streetwear female, lean / hero / streetwear male, androgynous high-fashion),
  16 live body sliders, 8 canvas-painted anime face presets, 10 hairstyles,
  5 skin tones.
- **Walkable store** — 9 interactable fixtures (racks, shoe wall, jewelry
  counter, hair booth), three themed alcoves with dressed mannequins
  (Opium Room / Luxury / Streetwear), a live round-timer totem, neon + bloom.
- **Visible drip** — 40-item catalog across 12 fictional brands; sleeves swing
  on the arm joints while you walk, pants ride the legs, hair sits on the head.
- **Alive, not static** — 8 NPC shoppers wander and browse, and an ambient
  runway show loops: an NPC model struts while three judges raise score
  paddles.
- **Full round loop** — 10:00 timer with halfway/one-minute warnings; at zero
  (or on R) your outfit locks and a 7-shot cinematic plays: wide reveal, low
  shoe shot, side tracking, close-up, slow spin, final pose, paddle reveal —
  then a rule-based judge verdict: total /100, 8 category scores, judge
  comments, strongest/weakest element, improvement tip, rank S–D.

## Testing

```bash
npm run build
npx vite preview --port 4173 &   # serve the build
node test/smoke.mjs              # plays the whole game headlessly
```

## Upgrading the visuals later

The avatar/clothing layer is isolated behind `buildAvatar()` and
`equipItem()`. Swapping the procedural placeholder body for real GLB/VRoid
anime models (via `GLTFLoader`) and real clothing meshes only touches
`src/avatar/builder.js` and `src/clothing/factory.js` — gameplay, UI, NPCs,
judging and the runway director stay as they are.
