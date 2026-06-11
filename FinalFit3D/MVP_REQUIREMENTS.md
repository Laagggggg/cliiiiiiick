# MVP Requirements — Vertical Slice Checklist

## In this slice (implemented)
- [x] Unity 3D URP project, runnable from MainMenu with zero manual asset work
- [x] MainMenu scene: neon wordmark, rotating showcase avatar, Enter/Quit
- [x] CharacterCreator scene: 7 adult presets (3 female / 3 male / 1 andro),
      16 body sliders with live rebuild, 8 face presets, 10 hairstyles,
      5 skin tones, rotating preview
- [x] FashionStore scene: walkable third-person store with WASD + mouse orbit
- [x] 9 interactable fixtures (racks, shoe wall, jewelry counter, hair booth)
      with "Press E to browse" prompts
- [x] Browse UI: dark-glass cards, brand labels, rarity badges, prices,
      equip/remove, equipped-fit sidebar
- [x] Clothing visibly equips on the avatar's body slots (40-item catalog)
- [x] Outfit persists across scenes via GameManager/OutfitState
- [x] Liveliness: 8 wandering NPC shoppers in random fits, dressed mannequins
      in 3 themed alcoves (Opium Room / Luxury / Streetwear), looping runway
      preview show with a strutting NPC model and 3 judges raising score
      paddles, neon zone lighting and signage

## Next phase (scaffolded, not active)
- [ ] RoundTimer driving the round (10:00 real / 0:30 debug) with warnings
- [ ] Outfit lock at 0:00 → auto-load Runway
- [ ] Runway cinematic camera sequence (wide reveal, shoe shot, tracking,
      close-up, spin, pose, score reveal)
- [ ] Rule-based JudgeScoringSystem over item tags vs RoundTheme
- [ ] Results screen: total /100, category breakdown, comments, rank, buttons
- [ ] Expand catalog to 80+ items; author items/themes as .asset files
- [ ] Filters in browse UI (aesthetic / brand / rarity / color), favorites

## Later
- Real rigged anime models + blendshapes replacing the procedural rig
- Real clothing/hair meshes keyed by MeshStyle
- Multiplayer fashion battles (explicitly out of scope for now)
