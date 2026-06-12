import { buildAvatar } from '../avatar/builder.js';
import { bodyFor, PRESETS, FACES } from '../avatar/presets.js';
import { byCategory } from '../clothing/catalog.js';
import { updateWalk } from '../avatar/walk.js';

// Ambient shopper AI: drift between browse points, linger at racks like
// they're judging the inventory, then move on. Keeps the store alive.

function mulberry(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function randomFit(rig, rnd) {
  const maybe = (cat, chance) => {
    if (rnd() > chance) return;
    const items = byCategory(cat);
    rig.equip(items[Math.floor(rnd() * items.length)]);
  };
  maybe('hair', 1); maybe('tops', 1); maybe('bottoms', 1); maybe('shoes', 1);
  maybe('outerwear', 0.5); maybe('jewelry', 0.5); maybe('headwear', 0.3); maybe('accessories', 0.4);
}

export function spawnNPCs(scene, count, roam) {
  const rnd = mulberry(1337);
  const presetKeys = Object.keys(PRESETS);
  const faceKeys = Object.keys(FACES);
  const npcs = [];

  for (let i = 0; i < count; i++) {
    const pk = presetKeys[Math.floor(rnd() * presetKeys.length)];
    const rig = buildAvatar({
      preset: pk, body: bodyFor(pk),
      faceKey: faceKeys[Math.floor(rnd() * faceKeys.length)],
      skin: Math.floor(rnd() * 5),
    });
    randomFit(rig, rnd);
    rig.root.position.set(
      roam.minX + rnd() * (roam.maxX - roam.minX), 0,
      roam.minZ + rnd() * (roam.maxZ - roam.minZ));
    scene.add(rig.root);

    npcs.push({
      rig,
      speed: 1.2 + rnd() * 0.9,
      target: null,
      pauseUntil: rnd() * 3,
      bored: 0,
      rnd,
    });
  }

  function pick(npc, time) {
    npc.target = {
      x: roam.minX + npc.rnd() * (roam.maxX - roam.minX),
      z: roam.minZ + npc.rnd() * (roam.maxZ - roam.minZ),
    };
    npc.bored = time + 8 + npc.rnd() * 6;
  }

  let time = 0;
  return {
    npcs,
    update(dt) {
      time += dt;
      for (const npc of npcs) {
        const { rig } = npc;
        if (time < npc.pauseUntil) { rig.walkSpeed = 0; updateWalk(rig, dt); continue; }
        if (!npc.target) pick(npc, time);

        const dx = npc.target.x - rig.root.position.x;
        const dz = npc.target.z - rig.root.position.z;
        const dist = Math.hypot(dx, dz);
        if (dist < 0.35 || time > npc.bored) {
          npc.pauseUntil = time + 1.5 + npc.rnd() * 3.5; // "browse" the rack
          pick(npc, time);
          rig.walkSpeed = 0;
        } else {
          const nx = dx / dist, nz = dz / dist;
          rig.root.position.x += nx * npc.speed * dt;
          rig.root.position.z += nz * npc.speed * dt;
          const targetYaw = Math.atan2(nx, nz);
          rig.root.rotation.y = dampAngle(rig.root.rotation.y, targetYaw, 6 * dt);
          rig.walkSpeed = 0.55;
        }
        updateWalk(rig, dt);
      }
    },
  };
}

export function dampAngle(a, b, t) {
  let d = b - a;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  return a + d * Math.min(1, t);
}
