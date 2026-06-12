import * as THREE from 'three';
import { updateWalk } from '../avatar/walk.js';
import { dampAngle } from '../world/npc.js';

// Third-person controller: WASD relative to the camera, shift to sprint,
// mouse-orbit camera, simple AABB collision against store fixtures.

export function createController(rig, camera, world) {
  let yaw = Math.PI;          // camera orbit angle
  let pitch = 0.25;
  const RADIUS = 0.35;

  return {
    rig,
    locked: false,            // UI open → no movement

    update(dt, input) {
      const [mdx, mdy] = input.consumeMouse();
      if (!this.locked) {
        yaw -= mdx * 0.0026;
        pitch = THREE.MathUtils.clamp(pitch + mdy * 0.0022, -0.35, 1.1);
      }

      let vx = 0, vz = 0;
      if (!this.locked) {
        const f = (input.down('KeyW') ? 1 : 0) - (input.down('KeyS') ? 1 : 0);
        const r = (input.down('KeyD') ? 1 : 0) - (input.down('KeyA') ? 1 : 0);
        if (f || r) {
          const sprint = input.down('ShiftLeft') || input.down('ShiftRight');
          const speed = sprint ? 5.4 : 3.2;
          const sin = Math.sin(yaw), cos = Math.cos(yaw);
          // forward = camera→player on the ground plane; right = forward × up
          vx = (-sin * f + cos * r) * speed;
          vz = (-cos * f - sin * r) * speed;
          rig.root.rotation.y = dampAngle(rig.root.rotation.y, Math.atan2(vx, vz), 12 * dt);
          rig.walkSpeed = sprint ? 1 : 0.65;
        } else rig.walkSpeed = 0;
      } else rig.walkSpeed = 0;

      // integrate + collide
      const p = rig.root.position;
      p.x += vx * dt; p.z += vz * dt;
      p.x = THREE.MathUtils.clamp(p.x, world.bounds.minX, world.bounds.maxX);
      p.z = THREE.MathUtils.clamp(p.z, world.bounds.minZ, world.bounds.maxZ);
      for (const o of world.obstacles) {
        const cx = THREE.MathUtils.clamp(p.x, o.minX, o.maxX);
        const cz = THREE.MathUtils.clamp(p.z, o.minZ, o.maxZ);
        const dx = p.x - cx, dz = p.z - cz;
        const d2 = dx * dx + dz * dz;
        if (d2 < RADIUS * RADIUS) {
          if (d2 < 1e-6) { p.x = o.maxX + RADIUS; continue; }
          const d = Math.sqrt(d2);
          p.x = cx + (dx / d) * RADIUS;
          p.z = cz + (dz / d) * RADIUS;
        }
      }

      updateWalk(rig, dt);

      // orbit camera
      const dist = 3.6, height = 1.6;
      const target = new THREE.Vector3(p.x, height, p.z);
      const desired = new THREE.Vector3(
        p.x + Math.sin(yaw) * Math.cos(pitch) * dist,
        height + Math.sin(pitch) * dist,
        p.z + Math.cos(yaw) * Math.cos(pitch) * dist);
      desired.y = Math.max(0.3, desired.y);
      camera.position.lerp(desired, Math.min(1, dt * 10));
      camera.lookAt(target);
    },
  };
}
