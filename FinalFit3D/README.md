# FINAL FIT — 3D Anime Fashion Battle (Vertical Slice)

A real Unity 3D (URP) prototype — **not** an HTML mockup. You walk a neon
fashion store in third person, browse racks, and clothing visibly appears on
your customized adult anime-style avatar. NPC shoppers wander the floor,
mannequins pose in themed alcoves, and a runway preview show loops with
judges raising score paddles.

Everything is generated from C# at runtime — no binary assets to download.

## How to open and play

1. Install **Unity 6 (6000.x)** via Unity Hub (any 6000.x works; the project
   pins 6000.0.32f1 — if you have a different 6000.x patch, just pick it when
   Hub asks).
2. In Unity Hub: **Add → Add project from disk** → select this `FinalFit3D`
   folder → open it.
3. First import takes a couple of minutes. On first load, a setup script
   auto-runs: it creates the URP pipeline assets, generates the five scenes,
   and opens `Assets/Scenes/MainMenu.unity`.
   (If it didn't run, use the menu **Tools ▸ FinalFit ▸ Setup Project**.)
4. Press **Play**.

## Controls

| Input | Action |
|---|---|
| WASD | walk |
| Left Shift | sprint |
| Mouse | orbit camera |
| E | browse rack / close panel |
| Esc | close browse panel |

## Flow

Main Menu → Character Creator (preset, 16 body sliders, face, hair, skin)
→ Fashion Store (browse 9 fixtures, equip visible clothing) → (Runway &
judging arrive in the next phase — scaffolds are already in
`Assets/Scripts/Future/`).

## Docs

- `CLAUDE.md` — rules + architecture map for Claude Code sessions
- `DESIGN_BIBLE.md` — art direction, brands, themes, core loop
- `MVP_REQUIREMENTS.md` — slice checklist and next-phase backlog

## Why placeholder primitives?

The slice proves the *systems*: presets, sliders, equipment slots, store
interaction, ambient AI, runway show. Every system talks to `AvatarRig` /
`AvatarEquipmentManager` abstractions, so real rigged anime models, hair and
clothing meshes can replace the procedural placeholders without rewriting
gameplay code. See the bottom of `CLAUDE.md` for the swap plan.
