using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Shared helpers for runtime scene construction: cameras, moody lighting,
    /// architecture boxes (with colliders), neon strips, 3D signage and
    /// randomized NPC avatars.
    /// </summary>
    public static class SceneKit
    {
        public static Camera CreateCamera(Vector3 pos, Vector3 lookAt, float fov = 55f)
        {
            var go = new GameObject("Main Camera");
            go.tag = "MainCamera";
            var cam = go.AddComponent<Camera>();
            go.AddComponent<AudioListener>();
            cam.fieldOfView = fov;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.03f, 0.025f, 0.05f);
            go.transform.position = pos;
            go.transform.LookAt(lookAt);
            return cam;
        }

        public static void MoodLighting(Color ambient, float directionalIntensity = 0.5f)
        {
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = ambient;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Exponential;
            RenderSettings.fogColor = new Color(0.04f, 0.03f, 0.07f);
            RenderSettings.fogDensity = 0.012f;

            var sun = new GameObject("KeyLight");
            var l = sun.AddComponent<Light>();
            l.type = LightType.Directional;
            l.intensity = directionalIntensity;
            l.color = new Color(0.85f, 0.8f, 1f);
            sun.transform.rotation = Quaternion.Euler(55f, -35f, 0);
        }

        public static Light PointLight(Vector3 pos, Color color, float intensity = 2.4f, float range = 9f)
        {
            var go = new GameObject("PointLight");
            go.transform.position = pos;
            var l = go.AddComponent<Light>();
            l.type = LightType.Point;
            l.color = color;
            l.intensity = intensity;
            l.range = range;
            return l;
        }

        public static Light SpotLight(Vector3 pos, Vector3 lookAt, Color color,
            float intensity = 5f, float angle = 45f, float range = 12f)
        {
            var go = new GameObject("SpotLight");
            go.transform.position = pos;
            go.transform.LookAt(lookAt);
            var l = go.AddComponent<Light>();
            l.type = LightType.Spot;
            l.color = color;
            l.intensity = intensity;
            l.spotAngle = angle;
            l.range = range;
            return l;
        }

        /// <summary>Architecture box — keeps its collider so players collide.</summary>
        public static Transform Box(Transform parent, string name, Vector3 pos, Vector3 scale,
            Material mat)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
            return go.transform;
        }

        public static Transform Cylinder(Transform parent, string name, Vector3 pos, Vector3 scale,
            Material mat, Vector3? euler = null)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localScale = scale;
            if (euler.HasValue) go.transform.localRotation = Quaternion.Euler(euler.Value);
            go.GetComponent<Renderer>().sharedMaterial = mat;
            return go.transform;
        }

        public static Transform NeonStrip(Transform parent, Vector3 pos, Vector3 scale, Color color)
        {
            var t = Box(parent, "NeonStrip", pos, scale, MaterialFactory.Emissive(color, 2.6f));
            Object.Destroy(t.GetComponent<Collider>());
            return t;
        }

        public static TextMesh Sign(Transform parent, string text, Vector3 pos, Color color,
            float charSize = 0.12f, Vector3? euler = null)
        {
            var go = new GameObject("Sign_" + text);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            if (euler.HasValue) go.transform.localRotation = Quaternion.Euler(euler.Value);
            var tm = go.AddComponent<TextMesh>();
            tm.text = text;
            tm.fontSize = 64;
            tm.characterSize = charSize;
            tm.anchor = TextAnchor.MiddleCenter;
            tm.alignment = TextAlignment.Center;
            tm.color = color;
            tm.font = UIFactory.DefaultFont;
            var mr = go.GetComponent<MeshRenderer>();
            if (tm.font != null) mr.sharedMaterial = tm.font.material;
            return tm;
        }

        static readonly AvatarPresetType[] AllPresets =
            (AvatarPresetType[])System.Enum.GetValues(typeof(AvatarPresetType));

        /// <summary>Random styled NPC avatar with a random fit already equipped.</summary>
        public static AvatarRig RandomNPC(Transform parent, Vector3 pos, System.Random rnd)
        {
            var preset = AllPresets[rnd.Next(AllPresets.Length)];
            var cfg = AvatarPresets.BodyFor(preset);
            var face = (FacePresetType)rnd.Next(System.Enum.GetValues(typeof(FacePresetType)).Length);
            var rig = AvatarBuilder.Build(parent, preset, cfg, face, rnd.Next(AvatarPresets.SkinToneCount));
            rig.transform.position = pos;

            EquipRandom(rig, ClothingCategory.Hair, rnd, 1f);
            EquipRandom(rig, ClothingCategory.Tops, rnd, 1f);
            EquipRandom(rig, ClothingCategory.Bottoms, rnd, 1f);
            EquipRandom(rig, ClothingCategory.Shoes, rnd, 1f);
            EquipRandom(rig, ClothingCategory.Outerwear, rnd, 0.5f);
            EquipRandom(rig, ClothingCategory.Jewelry, rnd, 0.5f);
            EquipRandom(rig, ClothingCategory.Headwear, rnd, 0.3f);
            EquipRandom(rig, ClothingCategory.Accessories, rnd, 0.4f);
            return rig;
        }

        static void EquipRandom(AvatarRig rig, ClothingCategory cat, System.Random rnd, float chance)
        {
            if (rnd.NextDouble() > chance) return;
            var items = ClothingDatabase.ByCategory(cat);
            if (items.Count == 0) return;
            rig.Equipment.Equip(items[rnd.Next(items.Count)]);
        }
    }

    /// <summary>Slow Y rotation for showcase pedestals.</summary>
    public class SpinSlow : MonoBehaviour
    {
        public float DegreesPerSecond = 22f;
        void Update() { transform.Rotate(0, DegreesPerSecond * Time.deltaTime, 0); }
    }
}
