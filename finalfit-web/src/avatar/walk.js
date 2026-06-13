// Exaggerated runway sashay: hips lead with a lateral sway + drop, shoulders
// counter-twist against them, legs cross toward the centerline, arms flare,
// and the body bobs. Female presets get extra sway. Driven per frame by
// rig.walkSpeed (0..1). All rotations are set absolutely each frame so nothing
// drifts; torso.rotation.x (posture, set by the builder) is left untouched.
export function updateWalk(rig, dt) {
  const target = rig.walkSpeed;
  rig._smooth = (rig._smooth ?? 0) + ((target - (rig._smooth ?? 0)) * Math.min(1, dt * 8));
  const s = rig._smooth;
  rig.walkPhase += dt * 6.2 * Math.max(s, 0.05);
  const ph = rig.walkPhase;
  const sway = rig.fem ? 1 : 0.5;

  const step = Math.sin(ph);       // forward/back stride
  const lateral = Math.cos(ph);    // side-to-side hip sway

  // legs: stride swing + constant inward cross-step (catwalk look)
  const cross = 0.07 * sway;
  rig.joints.hipL.rotation.set(step * 0.60 * s, 0, cross);
  rig.joints.hipR.rotation.set(-step * 0.60 * s, 0, -cross);

  // arms: opposite swing + a relaxed outward flare so they don't clip the body
  const armOut = 0.12 + 0.05 * sway;
  rig.joints.shoulderL.rotation.set(-step * 0.42 * s, 0, armOut);
  rig.joints.shoulderR.rotation.set(step * 0.42 * s, 0, -armOut);

  // hips lead — lateral sway, roll/drop and twist
  const hipRoll = lateral * 0.17 * sway * s;
  rig.pelvis.rotation.set(0, lateral * 0.12 * s, hipRoll);
  rig.pelvis.position.x = lateral * 0.022 * sway * s;

  // shoulders counter-rotate against the hips — the sexy upper-body twist
  rig.torso.rotation.y = -lateral * 0.14 * s;
  rig.torso.rotation.z = -hipRoll * 0.45;

  // head stays poised, slightly countering the torso
  rig.headGroup.rotation.y = lateral * 0.06 * s;

  // vertical bob at twice the stride frequency
  const bob = Math.abs(Math.sin(ph)) * 0.03 * s;
  rig.torso.position.y = rig.dims.hipY + 0.06 + bob;
  rig.pelvis.position.y = rig.dims.hipY + 0.04 + bob * 0.4;
}
