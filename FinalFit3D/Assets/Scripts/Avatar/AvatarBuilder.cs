using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Builds a stylized anime-proportioned placeholder avatar out of
    /// primitives — readable silhouette, big expressive eyes, posable arm/leg
    /// joints and clothing anchors. Intentionally structured so a real rigged
    /// anime model can replace it later: everything external talks to
    /// AvatarRig, never to the primitives directly.
    /// </summary>
    public static class AvatarBuilder
    {
        public static AvatarRig Build(Transform parent, AvatarPresetType preset,
            BodyConfig cfg, FacePresetType face, int skinTone = 0, bool withEquipment = true)
        {
            var root = new GameObject("Avatar_" + preset);
            if (parent != null) root.transform.SetParent(parent, false);

            var rig = root.AddComponent<AvatarRig>();
            rig.Preset = preset;
            rig.Face = face;
            rig.Body = cfg;

            bool fem = AvatarPresets.IsFeminine(preset);
            Color skin = AvatarPresets.SkinTone(skinTone);
            Material skinMat = MaterialFactory.Solid(skin, 0.02f, 0.35f);
            Material baseMat = MaterialFactory.Solid(new Color(0.15f, 0.15f, 0.18f), 0.05f, 0.4f);
            rig.SkinMaterial = skinMat;

            float muscleW = Mathf.Lerp(0.92f, 1.18f, Mathf.InverseLerp(0.6f, 1.6f, cfg.muscle));

            // ---- key heights ----------------------------------------------
            float legLen = 0.92f * cfg.legLength * cfg.height;
            float hipY = legLen;
            float torsoLen = 0.62f * cfg.height;
            float shoulderY = hipY + torsoLen * 0.82f;
            float neckY = hipY + torsoLen * 0.95f;
            float headR = 0.135f * cfg.headSize;
            float headY = neckY + 0.07f + headR;

            rig.HipY = hipY;
            rig.ShoulderY = shoulderY;
            rig.HeadY = headY;
            rig.HeadRadius = headR;
            rig.ShoulderHalfWidth = 0.235f * cfg.shoulderWidth * muscleW;
            rig.HipHalfWidth = 0.165f * cfg.hips;

            // ---- pelvis / hips --------------------------------------------
            var pelvis = Group(root.transform, "Pelvis", new Vector3(0, hipY + 0.04f, 0));
            rig.Pelvis = pelvis;
            Part(PrimitiveType.Sphere, pelvis, "Hips",
                Vector3.zero, new Vector3(0.36f * cfg.hips, 0.23f, 0.27f * cfg.hips), baseMat);
            Part(PrimitiveType.Sphere, pelvis, "Glute",
                new Vector3(0, -0.015f, -0.07f),
                new Vector3(0.30f * cfg.hips, 0.20f, 0.20f * cfg.glute), baseMat);

            // ---- torso -----------------------------------------------------
            var torso = Group(root.transform, "TorsoGroup", new Vector3(0, hipY + 0.06f, 0));
            torso.localRotation = Quaternion.Euler(-cfg.posture * 4f, 0, 0);
            rig.TorsoGroup = torso;

            Part(PrimitiveType.Sphere, torso, "Waist",
                new Vector3(0, torsoLen * 0.22f, 0),
                new Vector3(0.27f * cfg.waist, 0.26f, 0.21f * cfg.waist), baseMat);

            var chest = Part(PrimitiveType.Sphere, torso, "ChestUpper",
                new Vector3(0, torsoLen * 0.58f, 0),
                new Vector3(0.34f * cfg.shoulderWidth * muscleW,
                            0.30f,
                            0.235f * Mathf.Lerp(1f, cfg.chest, fem ? 0.35f : 1f) * muscleW), baseMat);
            rig.Chest = chest;

            if (fem)
            {
                Part(PrimitiveType.Sphere, torso, "Bust",
                    new Vector3(0, torsoLen * 0.52f, 0.055f),
                    new Vector3(0.27f * cfg.chest, 0.155f * cfg.chest, 0.17f * cfg.chest), baseMat);
            }

            // shoulders
            float shY = torsoLen * 0.76f;
            float shX = rig.ShoulderHalfWidth;
            Part(PrimitiveType.Sphere, torso, "ShoulderPadL",
                new Vector3(-shX, shY, 0), Vector3.one * 0.115f * muscleW, baseMat);
            Part(PrimitiveType.Sphere, torso, "ShoulderPadR",
                new Vector3(shX, shY, 0), Vector3.one * 0.115f * muscleW, baseMat);

            var neck = Part(PrimitiveType.Cylinder, torso, "Neck",
                new Vector3(0, torsoLen * 0.92f, 0),
                new Vector3(0.085f, 0.065f, 0.085f), skinMat);
            rig.Neck = neck;

            rig.BackAnchor = Group(torso, "BackAnchor", new Vector3(0, shY - 0.05f, -0.16f));

            // ---- arms ------------------------------------------------------
            rig.ShoulderJointL = BuildArm(torso, "L", -1, shX, shY, cfg, muscleW, skinMat, rig);
            rig.ShoulderJointR = BuildArm(torso, "R", 1, shX, shY, cfg, muscleW, skinMat, rig);

            // ---- legs ------------------------------------------------------
            rig.HipJointL = BuildLeg(root.transform, "L", -1, hipY, cfg, skinMat, baseMat, rig);
            rig.HipJointR = BuildLeg(root.transform, "R", 1, hipY, cfg, skinMat, baseMat, rig);

            // ---- head ------------------------------------------------------
            var headGroup = Group(torso, "HeadGroup",
                new Vector3(0, headY - (hipY + 0.06f), 0));
            rig.HeadGroup = headGroup;

            Part(PrimitiveType.Sphere, headGroup, "Head",
                Vector3.zero, new Vector3(headR * 1.78f, headR * 2.0f, headR * 1.85f), skinMat);
            // soft jaw
            Part(PrimitiveType.Sphere, headGroup, "Jaw",
                new Vector3(0, -headR * 0.55f, headR * 0.18f),
                new Vector3(headR * 1.45f, headR * 1.1f, headR * 1.4f), skinMat);

            BuildFace(headGroup, headR, face, fem);

            rig.FaceAnchor = Group(headGroup, "FaceAnchor", new Vector3(0, 0.01f, headR * 0.92f));
            rig.HairAnchor = Group(headGroup, "HairAnchor", Vector3.zero);

            // overall scale
            root.transform.localScale = Vector3.one * cfg.bodyScale;

            if (withEquipment)
            {
                rig.Equipment = root.AddComponent<AvatarEquipmentManager>();
                rig.Equipment.Init(rig);
            }
            return rig;
        }

        static Transform BuildArm(Transform torso, string side, int dir, float shX, float shY,
            BodyConfig cfg, float muscleW, Material skinMat, AvatarRig rig)
        {
            var joint = Group(torso, "ShoulderJoint" + side, new Vector3(dir * shX, shY, 0));
            float th = 0.082f * cfg.armThickness * muscleW;
            Part(PrimitiveType.Capsule, joint, "UpperArm",
                new Vector3(0, -0.15f, 0), new Vector3(th, 0.15f, th), skinMat);
            float fth = th * 0.82f;
            Part(PrimitiveType.Capsule, joint, "Forearm",
                new Vector3(0, -0.40f, 0), new Vector3(fth, 0.125f, fth), skinMat);
            var hand = Part(PrimitiveType.Sphere, joint, "Hand",
                new Vector3(0, -0.55f, 0), Vector3.one * 0.085f * cfg.handSize, skinMat);
            if (dir < 0) rig.HandL = hand; else rig.HandR = hand;
            return joint;
        }

        static Transform BuildLeg(Transform root, string side, int dir, float hipY,
            BodyConfig cfg, Material skinMat, Material baseMat, AvatarRig rig)
        {
            var joint = Group(root, "HipJoint" + side, new Vector3(dir * 0.10f * cfg.hips, hipY, 0));
            float thighT = 0.122f * cfg.thighThickness * Mathf.Lerp(1f, cfg.hips, 0.3f);
            var thigh = Part(PrimitiveType.Capsule, joint, "Thigh",
                new Vector3(0, -0.215f, 0), new Vector3(thighT, 0.225f, thighT), skinMat);
            float calfT = 0.092f * cfg.calfThickness;
            var calf = Part(PrimitiveType.Capsule, joint, "Calf",
                new Vector3(0, -0.60f, 0), new Vector3(calfT, 0.175f, calfT), skinMat);
            // base-layer shorts panel over the upper thigh
            Part(PrimitiveType.Capsule, joint, "BaseShort",
                new Vector3(0, -0.10f, 0), new Vector3(thighT * 1.15f, 0.11f, thighT * 1.15f), baseMat);

            float footY = -(hipY - 0.045f);
            var foot = Part(PrimitiveType.Cube, joint, "Foot",
                new Vector3(0, footY, 0.055f),
                new Vector3(0.10f * cfg.footSize, 0.075f, 0.235f * cfg.footSize), skinMat);

            if (dir < 0) { rig.ThighL = thigh; rig.CalfL = calf; rig.FootL = foot; }
            else { rig.ThighR = thigh; rig.CalfR = calf; rig.FootR = foot; }
            return joint;
        }

        static void BuildFace(Transform headGroup, float headR, FacePresetType face, bool fem)
        {
            FacePresets.Get(face, out float eyeScale, out float browAngle, out Color iris, out bool lips);

            Material white = MaterialFactory.Solid(new Color(0.97f, 0.97f, 1f), 0f, 0.7f);
            Material irisMat = MaterialFactory.Solid(iris, 0f, 0.8f);
            Material dark = MaterialFactory.Solid(new Color(0.08f, 0.07f, 0.08f), 0f, 0.5f);

            float ex = headR * 0.42f;
            float ez = headR * 0.80f;
            float ey = headR * 0.08f;
            Vector3 eyeSize = new Vector3(0.052f, 0.034f, 0.018f) * eyeScale * (headR / 0.135f);

            foreach (int dir in new[] { -1, 1 })
            {
                Part(PrimitiveType.Sphere, headGroup, "EyeWhite" + dir,
                    new Vector3(dir * ex, ey, ez), eyeSize, white);
                Part(PrimitiveType.Sphere, headGroup, "Iris" + dir,
                    new Vector3(dir * ex, ey, ez + 0.012f), eyeSize * 0.55f, irisMat);
                Part(PrimitiveType.Sphere, headGroup, "Pupil" + dir,
                    new Vector3(dir * ex, ey, ez + 0.020f), eyeSize * 0.28f, dark);

                var brow = Part(PrimitiveType.Cube, headGroup, "Brow" + dir,
                    new Vector3(dir * ex, ey + eyeSize.y + 0.028f, ez + 0.004f),
                    new Vector3(0.062f * eyeScale, 0.009f, 0.012f), dark);
                brow.localRotation = Quaternion.Euler(0, 0, -dir * browAngle);
            }

            // nose hint
            Part(PrimitiveType.Sphere, headGroup, "Nose",
                new Vector3(0, -headR * 0.18f, headR * 0.95f),
                new Vector3(0.018f, 0.025f, 0.02f), MaterialFactory.Solid(
                    new Color(0.9f, 0.72f, 0.62f), 0f, 0.3f));

            if (lips)
            {
                Part(PrimitiveType.Sphere, headGroup, "Lips",
                    new Vector3(0, -headR * 0.52f, headR * 0.82f),
                    new Vector3(0.045f, 0.016f, 0.02f),
                    MaterialFactory.Solid(fem ? new Color(0.85f, 0.35f, 0.45f)
                                              : new Color(0.75f, 0.5f, 0.45f), 0f, 0.6f));
            }
        }

        // ---- helpers -------------------------------------------------------

        public static Transform Group(Transform parent, string name, Vector3 localPos)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            return go.transform;
        }

        public static Transform Part(PrimitiveType type, Transform parent, string name,
            Vector3 localPos, Vector3 localScale, Material mat)
        {
            var go = GameObject.CreatePrimitive(type);
            go.name = name;
            var col = go.GetComponent<Collider>();
            if (col != null) Object.Destroy(col);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            go.transform.localScale = localScale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
            return go.transform;
        }
    }
}
