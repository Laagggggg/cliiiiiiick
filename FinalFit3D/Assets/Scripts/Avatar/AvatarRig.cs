using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// References into a procedurally-built avatar. Clothing, walk animation
    /// and the body customizer all talk to the rig through this so the
    /// placeholder body can later be replaced by a real skinned anime model.
    /// </summary>
    public class AvatarRig : MonoBehaviour
    {
        public AvatarPresetType Preset;
        public FacePresetType Face;
        public BodyConfig Body;

        [Header("Joints (animated)")]
        public Transform ShoulderJointL;
        public Transform ShoulderJointR;
        public Transform HipJointL;
        public Transform HipJointR;
        public Transform TorsoGroup;
        public Transform HeadGroup;

        [Header("Body parts / clothing anchors")]
        public Transform Pelvis;
        public Transform Chest;
        public Transform Neck;
        public Transform ThighL;
        public Transform ThighR;
        public Transform CalfL;
        public Transform CalfR;
        public Transform FootL;
        public Transform FootR;
        public Transform HandL;
        public Transform HandR;
        public Transform FaceAnchor;   // sunglasses, face accessories
        public Transform HairAnchor;   // hair meshes
        public Transform BackAnchor;   // bags, capes, props

        [Header("Dimensions (world-space-ish, after config)")]
        public float HipY;       // height of hip joints
        public float ShoulderY;
        public float HeadY;
        public float HeadRadius;
        public float ShoulderHalfWidth;
        public float HipHalfWidth;

        public Material SkinMaterial;
        public AvatarEquipmentManager Equipment;
    }
}
