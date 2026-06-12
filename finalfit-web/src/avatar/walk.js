// Procedural walk cycle: leg/arm swing + body bob, driven per frame.
// rig.walkSpeed is set by the player controller / NPC AI (0..1).
export function updateWalk(rig, dt) {
  const target = rig.walkSpeed;
  rig._smooth = (rig._smooth ?? 0) + ((target - (rig._smooth ?? 0)) * Math.min(1, dt * 8));
  const s = rig._smooth;
  rig.walkPhase += dt * 7 * Math.max(s, 0.0001);

  const swing = Math.sin(rig.walkPhase) * s;
  rig.joints.hipL.rotation.x = swing * 0.56;
  rig.joints.hipR.rotation.x = -swing * 0.56;
  rig.joints.shoulderL.rotation.x = -swing * 0.45;
  rig.joints.shoulderR.rotation.x = swing * 0.45;

  const bob = Math.abs(Math.sin(rig.walkPhase)) * 0.025 * s;
  rig.torso.position.y = rig.dims.hipY + 0.06 + bob;
}
