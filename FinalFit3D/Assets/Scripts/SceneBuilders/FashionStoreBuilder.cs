using System.Collections.Generic;
using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Builds the walkable 3D fashion store: zoned racks along the walls,
    /// themed alcoves (Opium Room / Luxury / Streetwear), a jewelry counter,
    /// a hair booth, mannequins, eight wandering NPC shoppers, and a live
    /// runway preview stage where judges score strutting NPCs.
    /// </summary>
    public class FashionStoreBuilder : MonoBehaviour
    {
        readonly System.Random _rnd = new System.Random(42);

        void Start()
        {
            var gm = GameManager.Ensure();
            SceneKit.MoodLighting(new Color(0.10f, 0.09f, 0.15f), 0.35f);

            BuildArchitecture();
            BuildRacks();
            BuildAlcoves();
            BuildCenterTotem();
            BuildRunwayPreview();
            BuildNPCs();
            BuildPlayer(gm);
        }

        // ------------------------------------------------------------------
        void BuildArchitecture()
        {
            var floorMat = MaterialFactory.Solid(FFPalette.FloorDark, 0.35f, 0.9f);
            var wallMat = MaterialFactory.Solid(FFPalette.WallDark, 0.1f, 0.4f);

            SceneKit.Box(null, "Floor", new Vector3(0, -0.05f, 0), new Vector3(44, 0.1f, 30), floorMat);
            SceneKit.Box(null, "WallN", new Vector3(0, 2.5f, 15), new Vector3(44, 5, 0.4f), wallMat);
            SceneKit.Box(null, "WallS", new Vector3(0, 2.5f, -15), new Vector3(44, 5, 0.4f), wallMat);
            SceneKit.Box(null, "WallE", new Vector3(22, 2.5f, 0), new Vector3(0.4f, 5, 30), wallMat);
            SceneKit.Box(null, "WallW", new Vector3(-22, 2.5f, 0), new Vector3(0.4f, 5, 30), wallMat);

            // neon ceiling trim
            SceneKit.NeonStrip(null, new Vector3(0, 4.6f, 14.7f), new Vector3(43, 0.06f, 0.06f), FFPalette.NeonPurple);
            SceneKit.NeonStrip(null, new Vector3(0, 4.6f, -14.7f), new Vector3(43, 0.06f, 0.06f), FFPalette.NeonPink);
            SceneKit.NeonStrip(null, new Vector3(21.7f, 4.6f, 0), new Vector3(0.06f, 0.06f, 29), FFPalette.NeonCyan);
            SceneKit.NeonStrip(null, new Vector3(-21.7f, 4.6f, 0), new Vector3(0.06f, 0.06f, 29), FFPalette.NeonPurple);

            // glowing floor runner guiding to the runway
            SceneKit.NeonStrip(null, new Vector3(6, 0.02f, 0), new Vector3(24, 0.015f, 0.18f), FFPalette.NeonPink);

            SceneKit.Sign(null, "FINAL FIT — DISTRICT STORE", new Vector3(0, 4.0f, 14.6f),
                FFPalette.NeonPink, 0.30f);
        }

        // ------------------------------------------------------------------
        void BuildRacks()
        {
            // south wall (player sees these first)
            Rack(new Vector3(-17, 0, -13), 180, ClothingCategory.Tops, "Tops");
            Rack(new Vector3(-10, 0, -13), 180, ClothingCategory.Outerwear, "Outerwear");
            Rack(new Vector3(-3, 0, -13), 180, ClothingCategory.Bottoms, "Bottoms");
            ShoeWall(new Vector3(4.5f, 0, -13), 180);
            Rack(new Vector3(11.5f, 0, -13), 180, ClothingCategory.Headwear, "Headwear");

            // north wall
            JewelryCounter(new Vector3(-17, 0, 13), 0);
            Rack(new Vector3(-10, 0, 13), 0, ClothingCategory.Accessories, "Accessories");
            Rack(new Vector3(-3, 0, 13), 0, ClothingCategory.Bags, "Bags");
            HairBooth(new Vector3(4.5f, 0, 13), 0);
        }

        void Rack(Vector3 pos, float yaw, ClothingCategory cat, string zone)
        {
            var root = new GameObject("Rack_" + zone);
            root.transform.position = pos;
            root.transform.rotation = Quaternion.Euler(0, yaw, 0);

            var metal = MaterialFactory.Chrome(new Color(0.65f, 0.65f, 0.72f));
            SceneKit.Cylinder(root.transform, "PostL", new Vector3(-1.1f, 0.85f, 0),
                new Vector3(0.06f, 0.85f, 0.06f), metal);
            SceneKit.Cylinder(root.transform, "PostR", new Vector3(1.1f, 0.85f, 0),
                new Vector3(0.06f, 0.85f, 0.06f), metal);
            SceneKit.Cylinder(root.transform, "Bar", new Vector3(0, 1.62f, 0),
                new Vector3(0.05f, 1.12f, 0.05f), metal, new Vector3(0, 0, 90));

            // hanging garments tinted from the actual catalog
            var items = ClothingDatabase.ByCategory(cat);
            int count = Mathf.Min(6, Mathf.Max(items.Count, 3));
            for (int i = 0; i < count; i++)
            {
                Color c = items.Count > 0 ? items[i % items.Count].PrimaryColor
                                          : new Color(0.3f, 0.3f, 0.35f);
                var hang = SceneKit.Box(root.transform, "Garment" + i,
                    new Vector3(-0.85f + i * (1.7f / (count - 1)), 1.18f, 0),
                    new Vector3(0.26f, 0.78f, 0.07f),
                    MaterialFactory.Solid(c, 0.05f, 0.4f));
                hang.localRotation = Quaternion.Euler(0, Random.Range(-7f, 7f), 0);
                Destroy(hang.GetComponent<Collider>());
            }

            FinishFixture(root.transform, pos, yaw, cat, zone, FFPalette.NeonPurple);
        }

        void ShoeWall(Vector3 pos, float yaw)
        {
            var root = new GameObject("Rack_ShoeWall");
            root.transform.position = pos;
            root.transform.rotation = Quaternion.Euler(0, yaw, 0);

            var shelfMat = MaterialFactory.Solid(new Color(0.16f, 0.15f, 0.20f), 0.2f, 0.6f);
            var items = ClothingDatabase.ByCategory(ClothingCategory.Shoes);
            for (int row = 0; row < 3; row++)
            {
                SceneKit.Box(root.transform, "Shelf" + row,
                    new Vector3(0, 0.55f + row * 0.55f, 0.1f), new Vector3(2.6f, 0.05f, 0.45f), shelfMat);
                for (int i = 0; i < 4; i++)
                {
                    Color c = items.Count > 0 ? items[(row * 4 + i) % items.Count].PrimaryColor : Color.gray;
                    var shoe = SceneKit.Box(root.transform, "Shoe",
                        new Vector3(-0.95f + i * 0.63f, 0.63f + row * 0.55f, 0.1f),
                        new Vector3(0.16f, 0.12f, 0.34f), MaterialFactory.Solid(c, 0.1f, 0.6f));
                    Destroy(shoe.GetComponent<Collider>());
                }
            }
            FinishFixture(root.transform, pos, yaw, ClothingCategory.Shoes, "Shoe Wall", FFPalette.NeonCyan);
        }

        void JewelryCounter(Vector3 pos, float yaw)
        {
            var root = new GameObject("Rack_Jewelry");
            root.transform.position = pos;
            root.transform.rotation = Quaternion.Euler(0, yaw, 0);

            SceneKit.Box(root.transform, "CounterBase", new Vector3(0, 0.5f, 0),
                new Vector3(2.4f, 1.0f, 0.9f), MaterialFactory.Solid(new Color(0.10f, 0.09f, 0.13f), 0.3f, 0.7f));
            var glass = SceneKit.Box(root.transform, "GlassTop", new Vector3(0, 1.13f, 0),
                new Vector3(2.3f, 0.25f, 0.8f), MaterialFactory.Sheer(new Color(0.7f, 0.85f, 1f), 0.18f));
            Destroy(glass.GetComponent<Collider>());
            for (int i = 0; i < 5; i++)
            {
                var gem = SceneKit.Box(root.transform, "Jewel" + i,
                    new Vector3(-0.9f + i * 0.45f, 1.08f, 0),
                    Vector3.one * 0.09f, MaterialFactory.Chrome(i % 2 == 0 ? FFPalette.Gold : Color.white));
                gem.localRotation = Quaternion.Euler(45, 45, 0);
                Destroy(gem.GetComponent<Collider>());
            }
            FinishFixture(root.transform, pos, yaw, ClothingCategory.Jewelry, "Jewelry Counter", FFPalette.Gold);
        }

        void HairBooth(Vector3 pos, float yaw)
        {
            var root = new GameObject("Rack_HairBooth");
            root.transform.position = pos;
            root.transform.rotation = Quaternion.Euler(0, yaw, 0);

            SceneKit.Box(root.transform, "Mirror", new Vector3(0, 1.5f, 0.4f),
                new Vector3(1.6f, 2.2f, 0.08f), MaterialFactory.Chrome(new Color(0.8f, 0.85f, 0.95f)));
            SceneKit.NeonStrip(root.transform, new Vector3(0, 2.65f, 0.4f),
                new Vector3(1.7f, 0.05f, 0.05f), FFPalette.NeonPink);
            SceneKit.Cylinder(root.transform, "Stool", new Vector3(0, 0.45f, -0.5f),
                new Vector3(0.4f, 0.045f, 0.4f), MaterialFactory.Solid(FFPalette.NeonPurple * 0.5f));
            SceneKit.Cylinder(root.transform, "StoolLeg", new Vector3(0, 0.22f, -0.5f),
                new Vector3(0.07f, 0.22f, 0.07f), MaterialFactory.Chrome(Color.gray));
            FinishFixture(root.transform, pos, yaw, ClothingCategory.Hair, "Hair & Makeup Booth", FFPalette.NeonPink);
        }

        void FinishFixture(Transform root, Vector3 pos, float yaw, ClothingCategory cat,
            string zone, Color accent)
        {
            var rack = root.gameObject.AddComponent<ClothingRack>();
            rack.Category = cat;
            rack.ZoneName = zone;

            // rack roots already face the store center, so local identity reads correctly
            SceneKit.Sign(root, zone.ToUpperInvariant(), new Vector3(0, 2.6f, 0), accent, 0.16f);
            SceneKit.NeonStrip(root, new Vector3(0, 0.015f, -0.9f), new Vector3(2.6f, 0.012f, 0.10f), accent);

            Vector3 inward = Quaternion.Euler(0, yaw, 0) * Vector3.back; // toward store center
            SceneKit.SpotLight(pos + inward * 2.2f + Vector3.up * 3.6f, pos + Vector3.up * 1.2f,
                accent, 4.5f, 50f, 9f);
        }

        // ------------------------------------------------------------------
        void BuildAlcoves()
        {
            Alcove(new Vector3(-20, 0, -6), "OPIUM ROOM", new Color(0.45f, 0.1f, 0.55f),
                new[] { "out_trench", "bot_leather", "sho_platform", "jwl_choker", "hair_long" });
            Alcove(new Vector3(-20, 0, 0.5f), "LUXURY", FFPalette.Gold,
                new[] { "out_white_trench", "bot_tailored", "sho_loafers", "jwl_chain", "hair_slick" });
            Alcove(new Vector3(-20, 0, 7), "STREETWEAR", FFPalette.NeonCyan,
                new[] { "top_hoodie_black", "bot_baggy", "sho_chunky", "hat_cap", "hair_wolf" });
        }

        void Alcove(Vector3 pos, string title, Color accent, string[] outfitIds)
        {
            var wallMat = MaterialFactory.Solid(new Color(0.09f, 0.08f, 0.12f), 0.1f, 0.4f);
            SceneKit.Box(null, "AlcoveWall_" + title, pos + new Vector3(0.8f, 1.6f, 2.6f),
                new Vector3(3.2f, 3.2f, 0.25f), wallMat);
            SceneKit.Box(null, "AlcoveWall2_" + title, pos + new Vector3(0.8f, 1.6f, -2.6f),
                new Vector3(3.2f, 3.2f, 0.25f), wallMat);

            SceneKit.Sign(null, title, pos + new Vector3(1.4f, 2.9f, 0), accent, 0.20f,
                new Vector3(0, -90, 0));
            SceneKit.PointLight(pos + new Vector3(1.2f, 2.6f, 0), accent, 3.2f, 7f);

            // pedestal mannequin dressed in the zone's signature fit
            SceneKit.Cylinder(null, "Pedestal_" + title, pos + new Vector3(0.6f, 0.15f, 0),
                new Vector3(0.7f, 0.15f, 0.7f), MaterialFactory.Solid(FFPalette.WallDark, 0.3f, 0.8f));
            SceneKit.NeonStrip(null, pos + new Vector3(0.6f, 0.31f, 0), new Vector3(1.3f, 0.012f, 1.3f), accent);

            var preset = RandomPreset();
            var rig = AvatarBuilder.Build(null, preset, AvatarPresets.BodyFor(preset),
                FacePresetType.ElegantRunway, _rnd.Next(AvatarPresets.SkinToneCount));
            rig.transform.position = pos + new Vector3(0.6f, 0.32f, 0);
            rig.transform.rotation = Quaternion.Euler(0, -90, 0);
            rig.gameObject.AddComponent<SpinSlow>().DegreesPerSecond = 14f;
            foreach (var id in outfitIds)
            {
                var item = ClothingDatabase.Find(id);
                if (item != null) rig.Equipment.Equip(item);
            }
        }

        AvatarPresetType RandomPreset()
        {
            var all = (AvatarPresetType[])System.Enum.GetValues(typeof(AvatarPresetType));
            return all[_rnd.Next(all.Length)];
        }

        // ------------------------------------------------------------------
        void BuildCenterTotem()
        {
            var totem = new GameObject("ThemeTotem");
            totem.transform.position = new Vector3(-3, 0, 0);
            SceneKit.Box(totem.transform, "Pillar", new Vector3(0, 1.6f, 0),
                new Vector3(0.5f, 3.2f, 0.5f), MaterialFactory.Solid(FFPalette.WallDark, 0.4f, 0.7f));
            SceneKit.NeonStrip(totem.transform, new Vector3(0, 3.25f, 0),
                new Vector3(0.7f, 0.04f, 0.7f), FFPalette.NeonPink);
            foreach (float yaw in new[] { 0f, 180f })
            {
                SceneKit.Sign(totem.transform, "ROUND THEME", new Vector3(0, 2.7f, 0),
                    FFPalette.TextDim, 0.09f, new Vector3(0, yaw, 0)).transform
                    .Translate(Quaternion.Euler(0, yaw, 0) * new Vector3(0, 0, -0.27f), Space.World);
                SceneKit.Sign(totem.transform, "OPIUM NIGHT", new Vector3(0, 2.4f, 0),
                    FFPalette.NeonPurple, 0.14f, new Vector3(0, yaw, 0)).transform
                    .Translate(Quaternion.Euler(0, yaw, 0) * new Vector3(0, 0, -0.27f), Space.World);
                SceneKit.Sign(totem.transform, "10:00", new Vector3(0, 2.0f, 0),
                    FFPalette.TextBright, 0.18f, new Vector3(0, yaw, 0)).transform
                    .Translate(Quaternion.Euler(0, yaw, 0) * new Vector3(0, 0, -0.27f), Space.World);
            }
        }

        // ------------------------------------------------------------------
        void BuildRunwayPreview()
        {
            var stageMat = MaterialFactory.Solid(new Color(0.05f, 0.05f, 0.07f), 0.3f, 0.9f);
            SceneKit.Box(null, "RunwayPlatform", new Vector3(16, 0.18f, 0),
                new Vector3(9.5f, 0.36f, 2.3f), stageMat);
            SceneKit.NeonStrip(null, new Vector3(16, 0.37f, 1.12f), new Vector3(9.5f, 0.02f, 0.05f), FFPalette.NeonPink);
            SceneKit.NeonStrip(null, new Vector3(16, 0.37f, -1.12f), new Vector3(9.5f, 0.02f, 0.05f), FFPalette.NeonPink);
            SceneKit.Sign(null, "RUNWAY PREVIEW", new Vector3(16, 3.4f, 1.5f), FFPalette.NeonPink, 0.20f);

            SceneKit.SpotLight(new Vector3(13, 4.5f, 2.5f), new Vector3(14, 0.4f, 0), Color.white, 6f, 38f);
            SceneKit.SpotLight(new Vector3(19, 4.5f, 2.5f), new Vector3(18, 0.4f, 0), FFPalette.NeonPurple, 6f, 38f);

            // judges' desk
            SceneKit.Box(null, "JudgeDesk", new Vector3(16, 0.55f, -2.6f),
                new Vector3(5.2f, 1.1f, 0.8f), MaterialFactory.Solid(new Color(0.10f, 0.09f, 0.14f), 0.2f, 0.6f));
            SceneKit.NeonStrip(null, new Vector3(16, 1.12f, -2.2f), new Vector3(5.2f, 0.03f, 0.03f), FFPalette.Gold);
            SceneKit.Sign(null, "JUDGES", new Vector3(16, 1.5f, -3.05f), FFPalette.Gold, 0.12f,
                new Vector3(0, 180, 0));

            var faces = new[] { FacePresetType.SeriousVillain, FacePresetType.ElegantRunway, FacePresetType.SharpModel };
            var paddles = new List<TextMesh>();
            for (int i = 0; i < 3; i++)
            {
                var preset = RandomPreset();
                var judge = AvatarBuilder.Build(null, preset, AvatarPresets.BodyFor(preset),
                    faces[i], _rnd.Next(AvatarPresets.SkinToneCount));
                judge.transform.position = new Vector3(14.4f + i * 1.6f, 0, -3.3f);
                judge.transform.rotation = Quaternion.identity; // facing the runway (+z)
                judge.Equipment.Equip(ClothingDatabase.Find(i == 1 ? "out_white_trench" : "out_trench"));
                judge.Equipment.Equip(ClothingDatabase.Find("hair_slick"));
                judge.Equipment.Equip(ClothingDatabase.Find(i == 0 ? "acc_shades" : "jwl_chain"));

                // score paddle held up beside the head
                var paddleRoot = new GameObject("Paddle");
                paddleRoot.transform.SetParent(judge.transform, false);
                paddleRoot.transform.localPosition = new Vector3(0.35f, 1.55f, 0.1f);
                SceneKit.Cylinder(paddleRoot.transform, "Stick", new Vector3(0, -0.12f, 0),
                    new Vector3(0.025f, 0.12f, 0.025f), MaterialFactory.Solid(Color.black));
                var board = SceneKit.Box(paddleRoot.transform, "Board", new Vector3(0, 0.1f, 0),
                    new Vector3(0.3f, 0.22f, 0.03f), MaterialFactory.Solid(new Color(0.95f, 0.93f, 0.99f)));
                Destroy(board.GetComponent<Collider>());
                var score = SceneKit.Sign(paddleRoot.transform, "—", new Vector3(0, 0.1f, 0.025f),
                    new Color(0.1f, 0.05f, 0.2f), 0.08f, new Vector3(0, 180, 0));
                paddles.Add(score);
            }

            // the strutting NPC model
            var modelPreset = AvatarPresetType.FemaleTallRunway;
            var model = AvatarBuilder.Build(null, modelPreset, AvatarPresets.BodyFor(modelPreset),
                FacePresetType.ElegantRunway, 1);
            model.transform.position = new Vector3(19.8f, 0.36f, 0);
            foreach (var id in new[] { "top_mesh", "bot_leather", "sho_platform", "hair_ponytail", "jwl_choker" })
                model.Equipment.Equip(ClothingDatabase.Find(id));
            var modelAnim = model.gameObject.AddComponent<SimpleWalkAnimator>();
            modelAnim.Bind(model);

            var director = gameObject.AddComponent<RunwayPreviewDirector>();
            director.Model = model.transform;
            director.ModelAnim = modelAnim;
            director.RunwayStart = new Vector3(19.8f, 0.36f, 0);
            director.RunwayEnd = new Vector3(12.4f, 0.36f, 0);
            director.JudgePaddles = paddles.ToArray();
        }

        // ------------------------------------------------------------------
        void BuildNPCs()
        {
            for (int i = 0; i < 8; i++)
            {
                var rig = SceneKit.RandomNPC(null,
                    new Vector3(Random.Range(-12f, 8f), 0, Random.Range(-8f, 8f)), _rnd);
                var anim = rig.gameObject.AddComponent<SimpleWalkAnimator>();
                anim.Bind(rig);
                var shopper = rig.gameObject.AddComponent<NPCShopper>();
                shopper.Init(anim, new Vector2(-18f, -11f), new Vector2(10f, 11f));
            }
        }

        // ------------------------------------------------------------------
        void BuildPlayer(GameManager gm)
        {
            var player = new GameObject("Player");
            player.transform.position = new Vector3(0, 0.05f, -7);

            var cc = player.AddComponent<CharacterController>();
            cc.height = 1.85f;
            cc.radius = 0.35f;
            cc.center = new Vector3(0, 0.95f, 0);

            if (gm.Body == null) gm.Body = AvatarPresets.BodyFor(gm.SelectedPreset);
            var rig = AvatarBuilder.Build(player.transform, gm.SelectedPreset, gm.Body, gm.SelectedFace);
            rig.Equipment.Init(rig, gm.Outfit);
            if (gm.Outfit.Get(ClothingSlot.Hair) == null)
            {
                var hair = ClothingDatabase.Find(AvatarPresets.DefaultHairId(gm.SelectedPreset));
                if (hair != null) rig.Equipment.Equip(hair);
            }
            rig.Equipment.ApplyOutfit(gm.Outfit);

            var anim = player.AddComponent<SimpleWalkAnimator>();
            anim.Bind(rig);

            var controller = player.AddComponent<ThirdPersonController>();
            controller.WalkAnimator = anim;

            var cam = SceneKit.CreateCamera(new Vector3(0, 2f, -11f), player.transform.position, 55f);
            var camCtrl = cam.gameObject.AddComponent<CameraController>();
            camCtrl.SnapBehind(player.transform);
            controller.CameraTransform = cam.transform;

            var uiGo = new GameObject("StoreUI");
            var ui = uiGo.AddComponent<StoreUI>();
            ui.Player = controller;
            ui.Cam = camCtrl;
            ui.PlayerEquipment = rig.Equipment;
            ui.Build();

            var interact = player.AddComponent<StoreInteraction>();
            interact.UI = ui;

            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
        }
    }
}
