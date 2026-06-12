import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

import { PAL, glossy, neon, box, cyl } from './core/materials.js';
import { createInput } from './core/input.js';
import { buildAvatar } from './avatar/builder.js';
import { bodyFor, PRESETS } from './avatar/presets.js';
import { byCategory, findItem, THEME } from './clothing/catalog.js';
import { buildStore } from './world/store.js';
import { spawnNPCs, randomFit } from './world/npc.js';
import { createAmbientShow, presentPlayer } from './world/runway.js';
import { createController } from './game/player.js';
import { judgeOutfit } from './game/judging.js';
import { showMenu, showCreator, buildHUD, openBrowse, showResults, clearUI } from './ui/ui.js';

// ---------------------------------------------------------------------------
// FINAL FIT — browser build. Flow: menu → creator → store (timed round) →
// runway presentation → judges' verdict.
// ---------------------------------------------------------------------------

const PARAMS = new URLSearchParams(location.search);
const ROUND_SECONDS = PARAMS.has('fast') ? 30 : 600;
const POTATO = PARAMS.has('potato'); // low-end mode: no bloom, no shadows

const renderer = new THREE.WebGLRenderer({ antialias: !POTATO });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(POTATO ? 1 : Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = !POTATO;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;
document.getElementById('app').append(renderer.domElement);

const camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.1, 120);
let scene = new THREE.Scene();

// metallic/chrome materials need an environment map or they render black
const pmrem = new THREE.PMREMGenerator(renderer);
const envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const composer = new EffectComposer(renderer);
const renderPass = new RenderPass(scene, camera);
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.4, 0.4, 1.15);
composer.addPass(renderPass);
composer.addPass(bloom);
composer.addPass(new OutputPass());

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  composer.setSize(innerWidth, innerHeight);
});

const input = createInput(renderer.domElement);

function freshScene(bg = 0x07060c, fog = 0.016) {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(bg);
  scene.fog = new THREE.FogExp2(bg, fog);
  scene.environment = envTex;
  scene.environmentIntensity = 0.22; // keep the moody night-club grade
  renderPass.scene = scene;
  return scene;
}

// ---- persistent player state ----------------------------------------------
const hairList = byCategory('hair');
const state = {
  preset: 'femaleCurvy',
  body: null,
  faceKey: PRESETS.femaleCurvy.face,
  skin: 0,
  hairId: PRESETS.femaleCurvy.hair,
  outfit: {},
  getBody() {
    if (!this.body) this.body = bodyFor(this.preset);
    return this.body;
  },
  hairName() { return findItem(this.hairId)?.name ?? '—'; },
  cycleHair(d) {
    const i = hairList.findIndex((h) => h.id === this.hairId);
    this.hairId = hairList[(i + d + hairList.length) % hairList.length].id;
  },
};

// ---- mode plumbing ---------------------------------------------------------
let mode = null;          // { update(dt) }
let last = performance.now();

function loop(now) {
  requestAnimationFrame(loop);
  // __FF_TIMESCALE lets the headless smoke test compensate for software-GL
  // frame rates; it is never set during normal play
  const dt = Math.min(0.05, (now - last) / 1000) * (window.__FF_TIMESCALE || 1);
  last = now;
  mode?.update(dt);
  input.endFrame();
  if (POTATO) renderer.render(scene, camera);
  else composer.render();
}
requestAnimationFrame(loop);

// ============================== MAIN MENU ===================================
function enterMenu() {
  input.unlock();
  renderer.domElement.onclick = null;
  const sc = freshScene();
  sc.add(new THREE.HemisphereLight(0x8a7fb8, 0x0a0810, 0.5));

  const floor = box(sc, new THREE.MeshStandardMaterial({ color: PAL.floor, metalness: 0.4, roughness: 0.3 }),
    [0, -0.05, 0], [20, 0.1, 20]);
  floor.receiveShadow = true;
  cyl(sc, glossy(0x221f2b, 0.6), [0, 0.08, 0], [1.1, 0.16, 1.1]);
  box(sc, neon(PAL.neonPurple, 2), [0, 0.17, 0], [2.4, 0.02, 2.4]).castShadow = false;

  const spot = (x, z, c) => {
    const l = new THREE.SpotLight(c, 13, 14, 0.5, 0.5, 1.6);
    l.position.set(x, 3.6, z);
    l.target.position.set(0, 1.1, 0);
    sc.add(l, l.target);
  };
  spot(2.5, 2.5, PAL.neonPink); spot(-2.5, 2.5, PAL.neonCyan); spot(0, -2.6, PAL.neonPurple);

  const keys = Object.keys(PRESETS);
  const pk = keys[Math.floor(Math.random() * keys.length)];
  const rig = buildAvatar({ preset: pk, body: bodyFor(pk), skin: Math.floor(Math.random() * 5) });
  let seed = Math.random;
  randomFit(rig, seed);
  rig.root.position.y = 0.17;
  sc.add(rig.root);

  camera.position.set(0, 1.55, 3.6);
  camera.lookAt(0, 1.15, 0);

  showMenu({ onStart: enterCreator });
  mode = { update(dt) { rig.root.rotation.y += dt * 0.45; } };
}

// ============================ CHARACTER CREATOR =============================
function enterCreator() {
  input.unlock();
  renderer.domElement.onclick = null;
  const sc = freshScene(0x0a0812, 0.02);
  sc.add(new THREE.HemisphereLight(0x9a8fc8, 0x0a0810, 0.55));

  const floor = box(sc, new THREE.MeshStandardMaterial({ color: PAL.floor, metalness: 0.4, roughness: 0.3 }),
    [0, -0.05, 0], [16, 0.1, 16]);
  floor.receiveShadow = true;
  box(sc, glossy(PAL.wall, 0.6), [0, 3, -4], [16, 8, 0.2]);
  box(sc, neon(PAL.neonPink, 1.8), [0, 0.02, 0], [2, 0.015, 2]).castShadow = false;

  const spot = (x, z, c, i = 10) => {
    const l = new THREE.SpotLight(c, i, 14, 0.55, 0.5, 1.6);
    l.position.set(x, 3.4, z);
    l.target.position.set(0, 1.0, 0);
    if (x === 0) l.castShadow = true;
    sc.add(l, l.target);
  };
  spot(2.4, 2.2, PAL.neonPink); spot(-2.4, 2.2, PAL.neonCyan); spot(0, 2.8, 0xffffff, 7);

  camera.position.set(0, 1.45, 3.1);
  camera.lookAt(0, 1.0, 0);

  let rig = null;
  let spin = Math.PI * 0.04;
  let rebuildQueued = 0;

  const rebuild = () => {
    const keepYaw = rig ? rig.root.rotation.y : 0;
    rig?.dispose();
    rig = buildAvatar({ preset: state.preset, body: state.getBody(), faceKey: state.faceKey, skin: state.skin });
    rig.root.position.y = 0.02;
    rig.root.rotation.y = keepYaw;
    rig.equip(findItem(state.hairId));
    for (const id of Object.values(state.outfit)) rig.equip(findItem(id));
    sc.add(rig.root);
  };
  rebuild();

  showCreator(state, {
    onChange(immediate) {
      if (immediate) rebuild();
      else rebuildQueued = 0.1; // throttle slider scrubbing
    },
    onGo() {
      state.outfit.hair = state.hairId;
      enterStore();
    },
  });

  mode = {
    update(dt) {
      if (rebuildQueued > 0) {
        rebuildQueued -= dt;
        if (rebuildQueued <= 0) rebuild();
      }
      if (rig) rig.root.rotation.y += dt * spin * 8;
    },
  };
}

// ================================ STORE =====================================
function enterStore() {
  const sc = freshScene(0x07060c, 0.009);
  const world = buildStore(sc);

  // player
  const rig = buildAvatar({ preset: state.preset, body: state.getBody(), faceKey: state.faceKey, skin: state.skin });
  rig.root.position.set(0, 0, -7);
  if (!state.outfit.hair) state.outfit.hair = state.hairId;
  for (const id of Object.values(state.outfit)) rig.equip(findItem(id));
  sc.add(rig.root);

  const controller = createController(rig, camera, world);
  camera.position.set(0, 2, -11);

  const npcSystem = spawnNPCs(sc, 8, { minX: -17, maxX: 9, minZ: -10, maxZ: 10 });
  const show = createAmbientShow(sc, world);

  const hud = buildHUD(THEME.name);
  hud.updateFit(rig.equipped);

  let browse = null;
  let timeLeft = ROUND_SECONDS;
  let toast = null, toastUntil = 0;
  let cinematic = null;
  let warned = { half: false, minute: false };

  const sayToast = (msg, dur = 2.4) => { toast = msg; toastUntil = timeLeft - dur; };

  const closeBrowse = () => {
    browse?.close(); browse = null;
    controller.locked = false;
    input.lock();
  };

  const openRack = (rack) => {
    controller.locked = true;
    input.unlock();
    browse = openBrowse({
      zone: rack.zone,
      items: byCategory(rack.category),
      isEquipped: (item) => rig.isEquipped(item),
      onToggle(item) {
        if (rig.isEquipped(item)) rig.unequip(item.slot);
        else rig.equip(item);
        state.outfit = rig.outfitIds();
        hud.updateFit(rig.equipped);
      },
      onClose: closeBrowse,
    });
  };

  const startPresentation = () => {
    if (cinematic) return;
    closeBrowse();
    input.unlock();
    controller.locked = true;
    show.paused = true;
    hud.hideForCinematic();
    const items = [...rig.equipped.values()].map((e) => e.item);
    const result = judgeOutfit(items, THEME);
    cinematic = presentPlayer({
      camera, playerRig: rig, store: world, result,
      onDone() {
        showResults(result, {
          onStore: enterStore,
          onMenu: enterMenu,
        });
      },
    });
  };

  renderer.domElement.onclick = () => {
    if (!browse && !cinematic) input.lock();
  };

  mode = {
    update(dt) {
      npcSystem.update(dt);
      show.update(dt);

      if (cinematic) { cinematic.update(dt); return; }
      window.__FF = { store: true, timeLeft: +timeLeft.toFixed(1) };

      // round timer
      timeLeft -= dt;
      hud.setTimer(timeLeft);
      for (const t of world.totemTexts) {
        const m = Math.max(0, Math.floor(timeLeft / 60));
        const s2 = Math.max(0, Math.floor(timeLeft % 60));
        t.userData.setText(`${m}:${String(s2).padStart(2, '0')}`, '#f4f2ff');
      }
      if (!warned.half && timeLeft <= ROUND_SECONDS / 2) { warned.half = true; sayToast('HALFWAY — lock in the silhouette'); }
      if (!warned.minute && timeLeft <= 60) { warned.minute = true; sayToast('ONE MINUTE — final touches!'); }
      if (timeLeft <= 0) { startPresentation(); return; }

      controller.update(dt, input);

      // nearest rack
      let nearest = null, best = 2.6;
      for (const rack of world.racks) {
        const d = Math.hypot(rack.x - rig.root.position.x, rack.z - rig.root.position.z);
        if (d < best) { best = d; nearest = rack; }
      }
      if (toast && timeLeft > toastUntil) hud.setPrompt(toast);
      else {
        toast = null;
        hud.setPrompt(nearest ? `Press E — Browse ${nearest.zone}` : '');
      }

      if (input.justPressed('KeyE')) {
        if (browse) closeBrowse();
        else if (nearest) openRack(nearest);
      }
      if (input.justPressed('Escape') && browse) closeBrowse();
      if (input.justPressed('KeyR') && !browse) startPresentation();
    },
  };
}

enterMenu();
