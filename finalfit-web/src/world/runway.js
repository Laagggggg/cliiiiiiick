import * as THREE from 'three';
import { buildAvatar } from '../avatar/builder.js';
import { bodyFor } from '../avatar/presets.js';
import { findItem } from '../clothing/catalog.js';
import { updateWalk } from '../avatar/walk.js';
import { dampAngle } from './npc.js';

// ---------------------------------------------------------------------------
// Runway systems: (1) the looping ambient preview show with an NPC model and
// paddle-raising judges, and (2) the player's cinematic presentation sequence
// that ends in the judges' verdict.
// ---------------------------------------------------------------------------

export function createAmbientShow(scene, store) {
  const rig = buildAvatar({ preset: 'femaleRunway', body: bodyFor('femaleRunway'), faceKey: 'elegantRunway', skin: 1 });
  for (const id of ['top_mesh', 'bot_leather', 'sho_platform', 'hair_ponytail', 'jwl_choker'])
    rig.equip(findItem(id));
  rig.root.position.copy(store.runway.start);
  scene.add(rig.root);

  let phase = 'out', t = 0, spin = 0;
  const show = {
    rig,
    paused: false,
    update(dt) {
      if (show.paused) { rig.root.visible = false; return; }
      rig.root.visible = true;
      t += dt;
      const target = phase === 'out' ? store.runway.end : store.runway.start;

      if (phase === 'out' || phase === 'back') {
        const done = moveOnRunway(rig, target, phase === 'out' ? 1.5 : 1.9, dt);
        if (done) { phase = phase === 'out' ? 'pose' : 'rest'; t = 0; spin = rig.root.rotation.y; }
      } else if (phase === 'pose') {
        rig.walkSpeed = 0;
        spin += dt * 2.1;
        rig.root.rotation.y = spin;
        if (t > 3) {
          for (const paddle of store.paddles)
            paddle.userData.setText((7 + Math.random() * 3).toFixed(1), '#33205c');
          phase = 'back'; t = 0;
        }
      } else { // rest
        rig.walkSpeed = 0;
        if (t > 2.5) {
          for (const paddle of store.paddles) paddle.userData.setText('—', '#33205c');
          phase = 'out'; t = 0;
        }
      }
      updateWalk(rig, dt);
    },
  };
  return show;
}

function moveOnRunway(rig, target, speed, dt) {
  const dx = target.x - rig.root.position.x;
  const dz = target.z - rig.root.position.z;
  const dist = Math.hypot(dx, dz);
  if (dist < 0.15) return true;
  rig.root.position.x += (dx / dist) * speed * dt;
  rig.root.position.z += (dz / dist) * speed * dt;
  rig.root.rotation.y = dampAngle(rig.root.rotation.y, Math.atan2(dx / dist, dz / dist), 8 * dt);
  rig.walkSpeed = 0.7;
  return false;
}

// ---------------------------------------------------------------------------
// Player presentation: cinematic camera phases, then judge paddles reveal the
// real scores from the judging system.
// ---------------------------------------------------------------------------

export function presentPlayer({ camera, playerRig, store, result, onDone }) {
  const R = store.runway;
  const mid = new THREE.Vector3((R.start.x + R.end.x) / 2, R.start.y, 0);
  playerRig.root.position.copy(R.start);
  playerRig.root.rotation.y = Math.atan2(R.end.x - R.start.x, 0); // face down the runway

  const judgeScores = [
    Math.max(1, Math.min(10, result.total / 10 + (Math.random() - 0.5))),
    Math.max(1, Math.min(10, result.total / 10 + (Math.random() - 0.5))),
    Math.max(1, Math.min(10, result.total / 10 + (Math.random() - 0.5))),
  ];

  const look = new THREE.Vector3();
  const phases = [
    { // 1. wide full-body reveal — model walks out
      dur: 4.6,
      update(k, dt) {
        moveOnRunway(playerRig, R.end, 1.6, dt);
        camera.position.lerp(new THREE.Vector3(mid.x - 1.5, 1.7, 5.4), 0.06);
        look.set(playerRig.root.position.x, 1.1, playerRig.root.position.z);
      },
    },
    { // 2. low-angle shoe shot
      dur: 2.2,
      update(k, dt) {
        playerRig.walkSpeed = 0;
        camera.position.lerp(new THREE.Vector3(R.end.x - 1.6, 0.55, 1.1), 0.1);
        look.set(R.end.x, 0.5, R.end.z);
      },
    },
    { // 3. side tracking shot back up the runway
      dur: 3.6,
      update(k, dt) {
        moveOnRunway(playerRig, mid, 1.2, dt);
        camera.position.lerp(
          new THREE.Vector3(playerRig.root.position.x + 0.5, 1.4, 3.2), 0.12);
        look.set(playerRig.root.position.x, 1.2, playerRig.root.position.z);
      },
    },
    { // 4. upper-body / accessory close-up
      dur: 2.4,
      update() {
        playerRig.walkSpeed = 0;
        camera.position.lerp(new THREE.Vector3(mid.x - 0.4, 1.55, 1.6), 0.12);
        look.set(mid.x, 1.45, mid.z);
      },
    },
    { // 5. slow spin
      dur: 3.2,
      update(k, dt) {
        playerRig.walkSpeed = 0;
        playerRig.root.rotation.y += dt * 1.9;
        camera.position.lerp(new THREE.Vector3(mid.x, 1.3, 3.6), 0.08);
        look.set(mid.x, 1.05, mid.z);
      },
    },
    { // 6. final pose facing the judges
      dur: 1.6,
      update(k, dt) {
        playerRig.walkSpeed = 0;
        playerRig.root.rotation.y = dampAngle(playerRig.root.rotation.y, Math.PI, 6 * dt);
        camera.position.lerp(new THREE.Vector3(mid.x + 3.5, 1.5, 2.8), 0.1);
        look.set(mid.x, 1.2, mid.z);
      },
    },
    { // 7. score reveal — paddles go up
      dur: 3.0,
      enter() {
        store.paddles.forEach((paddle, i) =>
          paddle.userData.setText(judgeScores[i].toFixed(1), '#7a1fa8'));
      },
      update() {
        camera.position.lerp(new THREE.Vector3(16, 1.5, 0.6), 0.09);
        look.copy(R.judgesLook);
      },
    },
  ];

  let idx = 0, t = 0, entered = false;
  return {
    done: false,
    update(dt) {
      if (this.done) return;
      window.__FF = { phase: idx, t: +t.toFixed(2) };
      const ph = phases[idx];
      if (!entered) { ph.enter?.(); entered = true; }
      t += dt;
      ph.update?.(t / ph.dur, dt);
      camera.lookAt(look);
      updateWalk(playerRig, dt);
      if (t >= ph.dur) {
        idx++; t = 0; entered = false;
        if (idx >= phases.length) {
          this.done = true;
          store.paddles.forEach((p) => p.userData.setText('—', '#33205c'));
          onDone?.();
        }
      }
    },
  };
}
