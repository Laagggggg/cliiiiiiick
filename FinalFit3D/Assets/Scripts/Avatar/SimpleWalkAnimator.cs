using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Procedural walk cycle for the placeholder rig: arm/leg swing plus a
    /// subtle body bob. Drives joint rotations only, so swapping in a rigged
    /// model + Animator later is a drop-in change.
    /// </summary>
    public class SimpleWalkAnimator : MonoBehaviour
    {
        public AvatarRig Rig;
        [Range(0f, 1f)] public float Speed;   // set by controller / NPC each frame
        public float StrideFrequency = 7f;
        public float LegSwing = 32f;
        public float ArmSwing = 26f;

        float _phase;
        float _smoothed;

        public void Bind(AvatarRig rig) { Rig = rig; }

        void Update()
        {
            if (Rig == null || Rig.HipJointL == null) return;

            _smoothed = Mathf.Lerp(_smoothed, Speed, Time.deltaTime * 8f);
            _phase += Time.deltaTime * StrideFrequency * Mathf.Max(_smoothed, 0.0001f);

            float swing = Mathf.Sin(_phase) * _smoothed;
            Rig.HipJointL.localRotation = Quaternion.Euler(swing * LegSwing, 0, 0);
            Rig.HipJointR.localRotation = Quaternion.Euler(-swing * LegSwing, 0, 0);
            Rig.ShoulderJointL.localRotation = Quaternion.Euler(-swing * ArmSwing, 0, 0);
            Rig.ShoulderJointR.localRotation = Quaternion.Euler(swing * ArmSwing, 0, 0);

            // body bob
            float bob = Mathf.Abs(Mathf.Sin(_phase)) * 0.025f * _smoothed;
            var p = Rig.TorsoGroup.localPosition;
            p.y = Rig.HipY + 0.06f + bob;
            Rig.TorsoGroup.localPosition = p;
        }
    }
}
