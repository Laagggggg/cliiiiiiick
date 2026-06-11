using System.Collections.Generic;
using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Builds visible placeholder 3D meshes for every clothing item and
    /// attaches them to the avatar's body slots — tops on the torso, sleeves
    /// on the arm joints (so they swing when walking), pants on the leg
    /// joints, shoes on the feet, hair on the head. Drip must be SEEN.
    /// Returns every spawned piece so the equipment manager can remove them.
    /// </summary>
    public static class ClothingMeshFactory
    {
        public static List<GameObject> Equip(AvatarRig rig, ClothingItem item)
        {
            var pieces = new List<GameObject>();
            Material prim = MaterialFactory.Solid(item.PrimaryColor, 0.08f, 0.45f);
            Material sec = MaterialFactory.Solid(item.SecondaryColor, 0.15f, 0.55f);
            Material chrome = MaterialFactory.Chrome(item.SecondaryColor);
            float torsoLen = (rig.ShoulderY - rig.HipY) / 0.82f;
            float shw = rig.ShoulderHalfWidth;
            float hr = rig.HeadRadius;

            void P(PrimitiveType t, Transform parent, string n, Vector3 pos, Vector3 scale,
                Material m, Vector3? euler = null)
            {
                var part = AvatarBuilder.Part(t, parent, n, pos, scale, m);
                if (euler.HasValue) part.localRotation = Quaternion.Euler(euler.Value);
                pieces.Add(part.gameObject);
            }

            void Sleeves(float thick, float len, Material m)
            {
                P(PrimitiveType.Capsule, rig.ShoulderJointL, "SleeveL",
                    new Vector3(0, -len * 0.5f, 0), new Vector3(thick, len * 0.55f, thick), m);
                P(PrimitiveType.Capsule, rig.ShoulderJointR, "SleeveR",
                    new Vector3(0, -len * 0.5f, 0), new Vector3(thick, len * 0.55f, thick), m);
            }

            void PantsLeg(Transform joint, float thighMul, float calfMul, Material m, bool full)
            {
                P(PrimitiveType.Capsule, joint, "PantThigh",
                    new Vector3(0, -0.215f, 0),
                    new Vector3(0.122f * thighMul, 0.235f, 0.122f * thighMul), m);
                if (full)
                    P(PrimitiveType.Capsule, joint, "PantCalf",
                        new Vector3(0, -0.60f, 0),
                        new Vector3(0.092f * calfMul, 0.19f, 0.092f * calfMul), m);
            }

            void ShoeAt(Transform foot, System.Action<Transform, Vector3> build)
            {
                build(foot.parent, foot.localPosition);
            }

            switch (item.MeshStyle)
            {
                // ============================ TOPS ============================
                case MeshStyle.OversizedHoodie:
                    P(PrimitiveType.Cube, rig.TorsoGroup, "HoodieBody",
                        new Vector3(0, torsoLen * 0.42f, 0),
                        new Vector3(shw * 2.45f, torsoLen * 0.85f, 0.36f), prim);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "KangarooPocket",
                        new Vector3(0, torsoLen * 0.18f, 0.185f),
                        new Vector3(shw * 1.1f, 0.12f, 0.03f), sec);
                    P(PrimitiveType.Sphere, rig.TorsoGroup, "Hood",
                        new Vector3(0, torsoLen * 0.88f, -0.13f),
                        new Vector3(0.24f, 0.20f, 0.22f), prim);
                    Sleeves(0.12f, 0.55f, prim);
                    break;

                case MeshStyle.MeshTop:
                    P(PrimitiveType.Capsule, rig.TorsoGroup, "MeshTop",
                        new Vector3(0, torsoLen * 0.45f, 0),
                        new Vector3(shw * 1.55f, torsoLen * 0.42f, 0.30f),
                        MaterialFactory.Sheer(item.PrimaryColor, 0.4f));
                    P(PrimitiveType.Cylinder, rig.TorsoGroup, "MeshCollar",
                        new Vector3(0, torsoLen * 0.88f, 0),
                        new Vector3(0.11f, 0.015f, 0.11f), sec);
                    break;

                case MeshStyle.LaceBlouse:
                    P(PrimitiveType.Cube, rig.TorsoGroup, "BlouseBody",
                        new Vector3(0, torsoLen * 0.42f, 0),
                        new Vector3(shw * 2.05f, torsoLen * 0.80f, 0.31f), prim);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "Collar",
                        new Vector3(0, torsoLen * 0.84f, 0.06f),
                        new Vector3(shw * 1.1f, 0.05f, 0.14f), sec);
                    Sleeves(0.10f, 0.52f, MaterialFactory.Sheer(item.PrimaryColor, 0.6f));
                    break;

                case MeshStyle.TankTop:
                    P(PrimitiveType.Cube, rig.TorsoGroup, "TankBody",
                        new Vector3(0, torsoLen * 0.42f, 0),
                        new Vector3(shw * 1.75f, torsoLen * 0.78f, 0.285f), prim);
                    break;

                case MeshStyle.OversizedTee:
                    P(PrimitiveType.Cube, rig.TorsoGroup, "TeeBody",
                        new Vector3(0, torsoLen * 0.38f, 0),
                        new Vector3(shw * 2.5f, torsoLen * 0.88f, 0.36f), prim);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "TeeGraphic",
                        new Vector3(0, torsoLen * 0.45f, 0.185f),
                        new Vector3(0.16f, 0.16f, 0.02f), sec);
                    Sleeves(0.125f, 0.22f, prim);
                    break;

                case MeshStyle.TacticalVest:
                    P(PrimitiveType.Cube, rig.TorsoGroup, "VestBody",
                        new Vector3(0, torsoLen * 0.50f, 0),
                        new Vector3(shw * 2.2f, torsoLen * 0.62f, 0.40f), prim);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "PouchL",
                        new Vector3(-shw * 0.55f, torsoLen * 0.38f, 0.21f),
                        new Vector3(0.10f, 0.10f, 0.05f), sec);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "PouchR",
                        new Vector3(shw * 0.55f, torsoLen * 0.38f, 0.21f),
                        new Vector3(0.10f, 0.10f, 0.05f), sec);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "GlowStrap",
                        new Vector3(0, torsoLen * 0.62f, 0.205f),
                        new Vector3(shw * 2.0f, 0.018f, 0.02f),
                        MaterialFactory.Emissive(item.SecondaryColor));
                    break;

                // ========================= OUTERWEAR ==========================
                case MeshStyle.CroppedJacket:
                    P(PrimitiveType.Cube, rig.TorsoGroup, "CropL",
                        new Vector3(-shw * 0.62f, torsoLen * 0.58f, 0),
                        new Vector3(shw * 1.25f, torsoLen * 0.52f, 0.40f), prim);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "CropR",
                        new Vector3(shw * 0.62f, torsoLen * 0.58f, 0),
                        new Vector3(shw * 1.25f, torsoLen * 0.52f, 0.40f), prim);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "CropCollar",
                        new Vector3(0, torsoLen * 0.84f, -0.02f),
                        new Vector3(shw * 1.5f, 0.05f, 0.22f), chrome);
                    Sleeves(0.115f, 0.56f, prim);
                    break;

                case MeshStyle.TrenchCoat:
                    foreach (int d in new[] { -1, 1 })
                        P(PrimitiveType.Cube, rig.TorsoGroup, "TrenchPanel" + d,
                            new Vector3(d * shw * 0.68f, torsoLen * 0.20f - 0.18f, -0.01f),
                            new Vector3(shw * 1.3f, 1.05f, 0.38f), prim);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "TrenchBack",
                        new Vector3(0, torsoLen * 0.20f - 0.18f, -0.135f),
                        new Vector3(shw * 2.2f, 1.05f, 0.10f), prim);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "TrenchBelt",
                        new Vector3(0, torsoLen * 0.18f, 0),
                        new Vector3(shw * 2.65f, 0.05f, 0.42f), sec);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "LapelL",
                        new Vector3(-shw * 0.45f, torsoLen * 0.70f, 0.185f),
                        new Vector3(0.05f, 0.22f, 0.025f), sec, new Vector3(0, 0, 18));
                    P(PrimitiveType.Cube, rig.TorsoGroup, "LapelR",
                        new Vector3(shw * 0.45f, torsoLen * 0.70f, 0.185f),
                        new Vector3(0.05f, 0.22f, 0.025f), sec, new Vector3(0, 0, -18));
                    Sleeves(0.12f, 0.58f, prim);
                    break;

                case MeshStyle.FurCoat:
                    foreach (int d in new[] { -1, 1 })
                        P(PrimitiveType.Cube, rig.TorsoGroup, "FurPanel" + d,
                            new Vector3(d * shw * 0.75f, torsoLen * 0.25f - 0.12f, -0.01f),
                            new Vector3(shw * 1.6f, 0.95f, 0.46f), prim);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "FurBack",
                        new Vector3(0, torsoLen * 0.25f - 0.12f, -0.16f),
                        new Vector3(shw * 2.6f, 0.95f, 0.12f), prim);
                    for (int i = 0; i < 7; i++)
                        P(PrimitiveType.Sphere, rig.TorsoGroup, "FurTuft" + i,
                            new Vector3(Mathf.Lerp(-shw * 1.2f, shw * 1.2f, i / 6f),
                                torsoLen * 0.82f, 0.04f),
                            Vector3.one * 0.11f, sec);
                    Sleeves(0.16f, 0.56f, prim);
                    break;

                case MeshStyle.Puffer:
                    for (int i = 0; i < 4; i++)
                        P(PrimitiveType.Capsule, rig.TorsoGroup, "PufferTube" + i,
                            new Vector3(0, torsoLen * (0.16f + i * 0.18f), 0),
                            new Vector3(shw * 2.45f * 0.5f, shw * 1.25f, 0.215f),
                            prim, new Vector3(0, 0, 90));
                    P(PrimitiveType.Cube, rig.TorsoGroup, "PufferZip",
                        new Vector3(0, torsoLen * 0.45f, 0.20f),
                        new Vector3(0.02f, torsoLen * 0.6f, 0.015f), sec);
                    Sleeves(0.155f, 0.55f, prim);
                    break;

                case MeshStyle.CyberJacket:
                    P(PrimitiveType.Cube, rig.TorsoGroup, "CyberBody",
                        new Vector3(0, torsoLen * 0.52f, 0),
                        new Vector3(shw * 2.35f, torsoLen * 0.62f, 0.40f), prim);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "CyberTrim",
                        new Vector3(0, torsoLen * 0.30f, 0),
                        new Vector3(shw * 2.4f, 0.02f, 0.41f),
                        MaterialFactory.Emissive(item.SecondaryColor));
                    P(PrimitiveType.Sphere, rig.TorsoGroup, "CyberPadL",
                        new Vector3(-shw, torsoLen * 0.78f, 0), Vector3.one * 0.15f, chrome);
                    P(PrimitiveType.Sphere, rig.TorsoGroup, "CyberPadR",
                        new Vector3(shw, torsoLen * 0.78f, 0), Vector3.one * 0.15f, chrome);
                    Sleeves(0.12f, 0.55f, prim);
                    break;

                // ========================== BOTTOMS ===========================
                case MeshStyle.LeatherPants:
                    {
                        var shiny = MaterialFactory.Solid(item.PrimaryColor, 0.2f, 0.85f);
                        PantsLeg(rig.HipJointL, 1.18f, 1.25f, shiny, true);
                        PantsLeg(rig.HipJointR, 1.18f, 1.25f, shiny, true);
                        P(PrimitiveType.Sphere, rig.Pelvis, "PantsHip",
                            Vector3.zero, new Vector3(0.38f, 0.25f, 0.29f), shiny);
                    }
                    break;

                case MeshStyle.CargoPants:
                    PantsLeg(rig.HipJointL, 1.45f, 1.55f, prim, true);
                    PantsLeg(rig.HipJointR, 1.45f, 1.55f, prim, true);
                    P(PrimitiveType.Sphere, rig.Pelvis, "CargoHip",
                        Vector3.zero, new Vector3(0.40f, 0.26f, 0.31f), prim);
                    P(PrimitiveType.Cube, rig.HipJointL, "CargoPocketL",
                        new Vector3(-0.115f, -0.28f, 0), new Vector3(0.05f, 0.12f, 0.10f), sec);
                    P(PrimitiveType.Cube, rig.HipJointR, "CargoPocketR",
                        new Vector3(0.115f, -0.28f, 0), new Vector3(0.05f, 0.12f, 0.10f), sec);
                    break;

                case MeshStyle.BaggyJeans:
                    PantsLeg(rig.HipJointL, 1.7f, 2.1f, prim, true);
                    PantsLeg(rig.HipJointR, 1.7f, 2.1f, prim, true);
                    P(PrimitiveType.Sphere, rig.Pelvis, "JeansHip",
                        Vector3.zero, new Vector3(0.41f, 0.26f, 0.32f), prim);
                    break;

                case MeshStyle.MiniSkirt:
                    P(PrimitiveType.Cylinder, rig.Pelvis, "SkirtTop",
                        new Vector3(0, -0.06f, 0), new Vector3(0.42f, 0.05f, 0.36f), prim);
                    P(PrimitiveType.Cylinder, rig.Pelvis, "SkirtHem",
                        new Vector3(0, -0.13f, 0), new Vector3(0.48f, 0.035f, 0.42f), sec);
                    break;

                case MeshStyle.PleatedSkirt:
                    P(PrimitiveType.Cylinder, rig.Pelvis, "PleatBody",
                        new Vector3(0, -0.10f, 0), new Vector3(0.46f, 0.085f, 0.40f), prim);
                    for (int i = 0; i < 8; i++)
                    {
                        float a = i * Mathf.PI * 2f / 8f;
                        P(PrimitiveType.Cube, rig.Pelvis, "Pleat" + i,
                            new Vector3(Mathf.Cos(a) * 0.215f, -0.165f, Mathf.Sin(a) * 0.185f),
                            new Vector3(0.06f, 0.06f, 0.02f), sec,
                            new Vector3(0, -a * Mathf.Rad2Deg, 0));
                    }
                    break;

                // =========================== SHOES ============================
                case MeshStyle.PlatformBoots:
                    foreach (var foot in new[] { rig.FootL, rig.FootR })
                        ShoeAt(foot, (joint, fp) =>
                        {
                            P(PrimitiveType.Cube, joint, "BootSole",
                                fp + new Vector3(0, -0.005f, 0.01f),
                                new Vector3(0.135f, 0.115f, 0.275f), sec);
                            P(PrimitiveType.Cube, joint, "BootBody",
                                fp + new Vector3(0, 0.10f, 0.01f),
                                new Vector3(0.125f, 0.10f, 0.26f), prim);
                            P(PrimitiveType.Cylinder, joint, "BootShaft",
                                fp + new Vector3(0, 0.22f, -0.04f),
                                new Vector3(0.115f, 0.085f, 0.115f), prim);
                        });
                    break;

                case MeshStyle.ChunkySneakers:
                    foreach (var foot in new[] { rig.FootL, rig.FootR })
                        ShoeAt(foot, (joint, fp) =>
                        {
                            P(PrimitiveType.Cube, joint, "SneakerBody",
                                fp + new Vector3(0, 0.025f, 0.01f),
                                new Vector3(0.13f, 0.105f, 0.285f), prim);
                            P(PrimitiveType.Cube, joint, "SneakerSole",
                                fp + new Vector3(0, -0.035f, 0.01f),
                                new Vector3(0.14f, 0.05f, 0.30f), sec);
                        });
                    break;

                case MeshStyle.DesignerBoots:
                    foreach (var foot in new[] { rig.FootL, rig.FootR })
                        ShoeAt(foot, (joint, fp) =>
                        {
                            P(PrimitiveType.Cube, joint, "DBootBody",
                                fp + new Vector3(0, 0.02f, 0.02f),
                                new Vector3(0.105f, 0.095f, 0.29f), chrome);
                            P(PrimitiveType.Cylinder, joint, "DBootShaft",
                                fp + new Vector3(0, 0.16f, -0.04f),
                                new Vector3(0.10f, 0.07f, 0.10f), chrome);
                        });
                    break;

                case MeshStyle.Loafers:
                    foreach (var foot in new[] { rig.FootL, rig.FootR })
                        ShoeAt(foot, (joint, fp) =>
                        {
                            P(PrimitiveType.Cube, joint, "LoaferBody",
                                fp + new Vector3(0, 0.005f, 0.01f),
                                new Vector3(0.11f, 0.085f, 0.26f), prim);
                            P(PrimitiveType.Cube, joint, "LoaferBit",
                                fp + new Vector3(0, 0.05f, 0.06f),
                                new Vector3(0.05f, 0.012f, 0.02f), MaterialFactory.Chrome(item.SecondaryColor));
                        });
                    break;

                // ========================== HEADWEAR ==========================
                case MeshStyle.Beanie:
                    P(PrimitiveType.Sphere, rig.HeadGroup, "BeanieDome",
                        new Vector3(0, hr * 0.65f, -hr * 0.1f),
                        new Vector3(hr * 1.95f, hr * 1.35f, hr * 2.0f), prim);
                    P(PrimitiveType.Cylinder, rig.HeadGroup, "BeanieBrim",
                        new Vector3(0, hr * 0.35f, -hr * 0.1f),
                        new Vector3(hr * 1.92f, hr * 0.18f, hr * 1.97f), sec);
                    break;

                case MeshStyle.Cap:
                    P(PrimitiveType.Sphere, rig.HeadGroup, "CapDome",
                        new Vector3(0, hr * 0.70f, -hr * 0.05f),
                        new Vector3(hr * 1.92f, hr * 1.1f, hr * 1.95f), prim);
                    P(PrimitiveType.Cube, rig.HeadGroup, "CapBrim",
                        new Vector3(0, hr * 0.55f, hr * 1.25f),
                        new Vector3(hr * 1.5f, 0.015f, hr * 1.1f), sec);
                    break;

                case MeshStyle.Halo:
                    for (int i = 0; i < 12; i++)
                    {
                        float a = i * Mathf.PI * 2f / 12f;
                        P(PrimitiveType.Sphere, rig.HeadGroup, "HaloBead" + i,
                            new Vector3(Mathf.Cos(a) * hr * 1.1f, hr * 1.9f, Mathf.Sin(a) * hr * 1.1f),
                            Vector3.one * 0.035f, MaterialFactory.Emissive(item.PrimaryColor, 3f));
                    }
                    break;

                // ==================== ACCESSORIES / JEWELRY ===================
                case MeshStyle.ChromeShades:
                    P(PrimitiveType.Cube, rig.FaceAnchor, "ShadeLens",
                        new Vector3(0, 0.012f, 0.012f),
                        new Vector3(hr * 1.75f, 0.035f, 0.02f), chrome);
                    foreach (int d in new[] { -1, 1 })
                        P(PrimitiveType.Cube, rig.FaceAnchor, "ShadeArm" + d,
                            new Vector3(d * hr * 0.88f, 0.012f, -hr * 0.5f),
                            new Vector3(0.008f, 0.012f, hr * 1.1f), prim);
                    break;

                case MeshStyle.ChainNecklace:
                    for (int i = 0; i < 9; i++)
                    {
                        // arc across the chest: ends ride high near the neck,
                        // center link hangs lowest
                        float a = Mathf.Lerp(-1.25f, 1.25f, i / 8f);
                        P(PrimitiveType.Sphere, rig.TorsoGroup, "ChainLink" + i,
                            new Vector3(Mathf.Sin(a) * 0.14f,
                                torsoLen * 0.70f + Mathf.Abs(Mathf.Sin(a)) * 0.10f,
                                0.145f - Mathf.Abs(Mathf.Sin(a)) * 0.03f),
                            Vector3.one * 0.028f, MaterialFactory.Chrome(item.PrimaryColor));
                    }
                    P(PrimitiveType.Cube, rig.TorsoGroup, "Pendant",
                        new Vector3(0, torsoLen * 0.70f - 0.045f, 0.155f),
                        new Vector3(0.035f, 0.045f, 0.012f), MaterialFactory.Chrome(item.PrimaryColor));
                    break;

                case MeshStyle.Choker:
                    P(PrimitiveType.Cylinder, rig.TorsoGroup, "ChokerBand",
                        new Vector3(0, torsoLen * 0.92f, 0),
                        new Vector3(0.105f, 0.014f, 0.105f), prim);
                    P(PrimitiveType.Sphere, rig.TorsoGroup, "ChokerStud",
                        new Vector3(0, torsoLen * 0.92f, 0.095f),
                        Vector3.one * 0.022f, chrome);
                    break;

                case MeshStyle.ChainBelt:
                    for (int i = 0; i < 10; i++)
                    {
                        float a = i * Mathf.PI * 2f / 10f;
                        P(PrimitiveType.Sphere, rig.Pelvis, "BeltLink" + i,
                            new Vector3(Mathf.Cos(a) * 0.20f, -0.02f - Mathf.Sin(a) * 0.025f,
                                Mathf.Sin(a) * 0.155f),
                            Vector3.one * 0.030f, MaterialFactory.Chrome(item.PrimaryColor));
                    }
                    break;

                case MeshStyle.CrossbodyBag:
                    P(PrimitiveType.Cube, rig.TorsoGroup, "BagStrap",
                        new Vector3(0, torsoLen * 0.50f, 0.175f),
                        new Vector3(0.045f, torsoLen * 0.75f, 0.015f), sec,
                        new Vector3(0, 0, 35));
                    P(PrimitiveType.Cube, rig.TorsoGroup, "BagBody",
                        new Vector3(shw * 0.95f, torsoLen * 0.12f, 0.05f),
                        new Vector3(0.09f, 0.14f, 0.19f), prim);
                    P(PrimitiveType.Cube, rig.TorsoGroup, "BagClasp",
                        new Vector3(shw * 0.95f, torsoLen * 0.16f, 0.15f),
                        new Vector3(0.03f, 0.02f, 0.01f), MaterialFactory.Chrome(item.SecondaryColor));
                    break;

                case MeshStyle.HoopEarrings:
                    foreach (int d in new[] { -1, 1 })
                        P(PrimitiveType.Cylinder, rig.HeadGroup, "Hoop" + d,
                            new Vector3(d * hr * 0.92f, -hr * 0.35f, 0),
                            new Vector3(0.038f, 0.004f, 0.038f),
                            MaterialFactory.Chrome(item.PrimaryColor), new Vector3(0, 0, 90));
                    break;

                case MeshStyle.StudSet:
                    foreach (int d in new[] { -1, 1 })
                        P(PrimitiveType.Sphere, rig.HeadGroup, "EarStud" + d,
                            new Vector3(d * hr * 0.92f, -hr * 0.15f, 0),
                            Vector3.one * 0.016f, chrome);
                    P(PrimitiveType.Sphere, rig.HeadGroup, "BrowStud",
                        new Vector3(hr * 0.45f, hr * 0.32f, hr * 0.82f),
                        Vector3.one * 0.012f, chrome);
                    break;

                // ============================ HAIR ============================
                default:
                    BuildHair(rig, item, prim, sec, pieces);
                    break;
            }
            return pieces;
        }

        static void BuildHair(AvatarRig rig, ClothingItem item, Material prim, Material sec,
            List<GameObject> pieces)
        {
            float hr = rig.HeadRadius;
            Transform a = rig.HairAnchor;

            void H(PrimitiveType t, string n, Vector3 pos, Vector3 scale, Vector3? euler = null)
            {
                var part = AvatarBuilder.Part(t, a, n, pos, scale, prim);
                if (euler.HasValue) part.localRotation = Quaternion.Euler(euler.Value);
                pieces.Add(part.gameObject);
            }

            void Scalp(float size = 1f)
            {
                H(PrimitiveType.Sphere, "Scalp",
                    new Vector3(0, hr * 0.22f, -hr * 0.18f),
                    new Vector3(hr * 2.0f * size, hr * 2.0f * size, hr * 2.05f * size));
            }

            void Bangs()
            {
                H(PrimitiveType.Cube, "Bangs",
                    new Vector3(0, hr * 0.78f, hr * 0.72f),
                    new Vector3(hr * 1.65f, hr * 0.45f, hr * 0.55f));
            }

            switch (item.MeshStyle)
            {
                case MeshStyle.HairBob:
                    Scalp(1.04f); Bangs();
                    foreach (int d in new[] { -1, 1 })
                        H(PrimitiveType.Cube, "SidePanel" + d,
                            new Vector3(d * hr * 0.92f, -hr * 0.15f, hr * 0.15f),
                            new Vector3(hr * 0.38f, hr * 1.5f, hr * 0.85f));
                    break;

                case MeshStyle.HairLong:
                    Scalp(1.03f); Bangs();
                    H(PrimitiveType.Cube, "BackFall",
                        new Vector3(0, -hr * 2.1f, -hr * 0.85f),
                        new Vector3(hr * 1.8f, hr * 4.2f, hr * 0.5f));
                    foreach (int d in new[] { -1, 1 })
                        H(PrimitiveType.Cube, "FrontStrand" + d,
                            new Vector3(d * hr * 0.85f, -hr * 0.9f, hr * 0.35f),
                            new Vector3(hr * 0.30f, hr * 2.4f, hr * 0.30f));
                    break;

                case MeshStyle.HairWolf:
                    Scalp(1.05f); Bangs();
                    var rnd = new System.Random(7);
                    for (int i = 0; i < 6; i++)
                    {
                        float ang = (float)rnd.NextDouble() * 360f;
                        float tilt = 20f + (float)rnd.NextDouble() * 35f;
                        H(PrimitiveType.Cube, "Chunk" + i,
                            Quaternion.Euler(0, ang, 0) * new Vector3(0, hr * 0.1f, hr * 0.95f),
                            new Vector3(hr * 0.35f, hr * 1.1f, hr * 0.25f),
                            new Vector3(tilt, ang, 0));
                    }
                    break;

                case MeshStyle.HairSpiky:
                    Scalp(1.02f);
                    for (int i = 0; i < 8; i++)
                    {
                        float ang = i * 45f;
                        var dir = Quaternion.Euler(-40f, ang, 0) * Vector3.up;
                        H(PrimitiveType.Cube, "Spike" + i,
                            dir * hr * 1.0f + new Vector3(0, hr * 0.35f, 0),
                            new Vector3(hr * 0.30f, hr * 0.95f, hr * 0.30f),
                            new Vector3(Mathf.Cos(ang * Mathf.Deg2Rad) * 35f, 0,
                                        Mathf.Sin(ang * Mathf.Deg2Rad) * 35f));
                    }
                    break;

                case MeshStyle.HairSlick:
                    Scalp(1.0f);
                    H(PrimitiveType.Sphere, "SlickBack",
                        new Vector3(0, hr * 0.1f, -hr * 0.55f),
                        new Vector3(hr * 1.7f, hr * 1.7f, hr * 1.4f));
                    break;

                case MeshStyle.HairCurly:
                    Scalp(1.0f);
                    for (int i = 0; i < 10; i++)
                    {
                        float ang = i * 36f;
                        var dir = Quaternion.Euler(-50f + (i % 3) * 22f, ang, 0) * Vector3.up;
                        H(PrimitiveType.Sphere, "Curl" + i,
                            dir * hr * 0.95f + new Vector3(0, hr * 0.18f, -hr * 0.1f),
                            Vector3.one * hr * 0.62f);
                    }
                    break;

                case MeshStyle.HairPonytail:
                    Scalp(1.0f); Bangs();
                    H(PrimitiveType.Sphere, "TieKnot",
                        new Vector3(0, hr * 0.55f, -hr * 1.05f), Vector3.one * hr * 0.45f);
                    H(PrimitiveType.Capsule, "Tail",
                        new Vector3(0, -hr * 0.4f, -hr * 1.35f),
                        new Vector3(hr * 0.55f, hr * 1.6f, hr * 0.55f),
                        new Vector3(-18f, 0, 0));
                    break;

                case MeshStyle.HairTwinTails:
                    Scalp(1.02f); Bangs();
                    foreach (int d in new[] { -1, 1 })
                    {
                        H(PrimitiveType.Sphere, "TieKnot" + d,
                            new Vector3(d * hr * 1.0f, hr * 0.5f, -hr * 0.3f),
                            Vector3.one * hr * 0.4f);
                        H(PrimitiveType.Capsule, "Tail" + d,
                            new Vector3(d * hr * 1.25f, -hr * 0.85f, -hr * 0.35f),
                            new Vector3(hr * 0.5f, hr * 1.7f, hr * 0.5f),
                            new Vector3(0, 0, -d * 14f));
                    }
                    break;

                case MeshStyle.HairBraids:
                    Scalp(1.02f); Bangs();
                    foreach (int d in new[] { -1, 1 })
                        for (int i = 0; i < 3; i++)
                            H(PrimitiveType.Sphere, $"Braid{d}_{i}",
                                new Vector3(d * hr * 0.85f, -hr * (0.55f + i * 0.55f), hr * 0.30f),
                                new Vector3(hr * 0.34f, hr * 0.45f, hr * 0.34f));
                    break;

                case MeshStyle.HairShortHood:
                default:
                    Scalp(0.98f); Bangs();
                    break;
            }
        }
    }
}
