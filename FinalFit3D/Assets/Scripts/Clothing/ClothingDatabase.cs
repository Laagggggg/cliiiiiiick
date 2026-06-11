using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// In-memory catalog for the vertical slice (~40 pieces across the
    /// fictional brands). Later phases can replace this with authored
    /// ScriptableObject assets without touching consumers — everything goes
    /// through All / ByCategory / Find.
    /// </summary>
    public static class ClothingDatabase
    {
        static List<ClothingItem> _all;

        public static IReadOnlyList<ClothingItem> All
        {
            get { BuildIfNeeded(); return _all; }
        }

        public static List<ClothingItem> ByCategory(ClothingCategory cat)
        {
            BuildIfNeeded();
            return _all.Where(i => i.Category == cat).ToList();
        }

        public static ClothingItem Find(string id)
        {
            BuildIfNeeded();
            return _all.FirstOrDefault(i => i.Id == id);
        }

        static readonly Color Black = new Color(0.09f, 0.09f, 0.10f);
        static readonly Color OffBlack = new Color(0.14f, 0.13f, 0.16f);
        static readonly Color Cream = new Color(0.93f, 0.89f, 0.80f);
        static readonly Color Chrome = new Color(0.85f, 0.88f, 0.95f);
        static readonly Color BloodRed = new Color(0.55f, 0.10f, 0.15f);
        static readonly Color Denim = new Color(0.30f, 0.36f, 0.48f);
        static readonly Color Olive = new Color(0.38f, 0.40f, 0.28f);
        static readonly Color HotPink = new Color(1f, 0.35f, 0.70f);
        static readonly Color NeonCyan = new Color(0.25f, 0.95f, 1f);
        static readonly Color Velvet = new Color(0.28f, 0.08f, 0.20f);

        static void BuildIfNeeded()
        {
            if (_all != null) return;
            _all = new List<ClothingItem>
            {
                // ------------------------- TOPS -------------------------
                ClothingItem.Create("top_hoodie_black", "Shadow Cult Hoodie", "VANTA VEIL",
                    ClothingCategory.Tops, ClothingSlot.Top, Rarity.Uncommon, 240,
                    MeshStyle.OversizedHoodie, Black, OffBlack,
                    new[] { "dark", "oversized", "streetwear", "opium" },
                    7, 8, 7, 2, 6, 0, 1, 4, 6),
                ClothingItem.Create("top_hoodie_cream", "Cloud Money Hoodie", "COTTON GODS",
                    ClothingCategory.Tops, ClothingSlot.Top, Rarity.Common, 150,
                    MeshStyle.OversizedHoodie, Cream, new Color(0.8f, 0.76f, 0.66f),
                    new[] { "cozy", "neutral", "streetwear" },
                    6, 1, 6, 4, 0, 0, 2, 2, 5),
                ClothingItem.Create("top_mesh", "Phantom Mesh Top", "VANTA VEIL",
                    ClothingCategory.Tops, ClothingSlot.Top, Rarity.Rare, 310,
                    MeshStyle.MeshTop, new Color(0.1f, 0.1f, 0.12f), Black,
                    new[] { "dark", "sheer", "opium", "goth", "risky" },
                    8, 9, 4, 3, 8, 0, 2, 8, 4),
                ClothingItem.Create("top_lace", "Midnight Lace Blouse", "ROYAL ROT",
                    ClothingCategory.Tops, ClothingSlot.Top, Rarity.Rare, 380,
                    MeshStyle.LaceBlouse, Velvet, Black,
                    new[] { "gothic", "royal", "elegant", "dark" },
                    8, 6, 1, 6, 9, 6, 0, 6, 5),
                ClothingItem.Create("top_tank_white", "Saint Cotton Tank", "HALO BOULEVARD",
                    ClothingCategory.Tops, ClothingSlot.Top, Rarity.Common, 90,
                    MeshStyle.TankTop, new Color(0.95f, 0.95f, 0.97f), Cream,
                    new[] { "clean", "angelic", "minimal" },
                    4, 0, 3, 5, 0, 1, 3, 1, 2),
                ClothingItem.Create("top_tee_grim", "Grim Oversized Tee", "GRIM LUXE",
                    ClothingCategory.Tops, ClothingSlot.Top, Rarity.Uncommon, 180,
                    MeshStyle.OversizedTee, OffBlack, BloodRed,
                    new[] { "villain", "dark", "oversized", "streetwear" },
                    6, 6, 7, 2, 5, 0, 1, 3, 4),
                ClothingItem.Create("top_vest_nova", "Tactical Panel Vest", "NOVA CARTEL",
                    ClothingCategory.Tops, ClothingSlot.Top, Rarity.Epic, 520,
                    MeshStyle.TacticalVest, new Color(0.16f, 0.18f, 0.20f), NeonCyan,
                    new[] { "cyber", "tactical", "streetwear", "techwear" },
                    8, 4, 9, 3, 3, 0, 4, 7, 8),
                ClothingItem.Create("top_linen", "Old Money Linen Shirt", "LOFT MONEY",
                    ClothingCategory.Tops, ClothingSlot.Top, Rarity.Rare, 420,
                    MeshStyle.LaceBlouse, Cream, new Color(0.85f, 0.80f, 0.70f),
                    new[] { "oldmoney", "quietluxury", "linen", "tailored" },
                    7, 0, 1, 9, 0, 7, 0, 2, 4),

                // ----------------------- OUTERWEAR ----------------------
                ClothingItem.Create("out_cropped", "Razor Cropped Jacket", "VANTA VEIL",
                    ClothingCategory.Outerwear, ClothingSlot.Outerwear, Rarity.Rare, 460,
                    MeshStyle.CroppedJacket, Black, Chrome,
                    new[] { "dark", "leather", "opium", "edgy" },
                    8, 8, 5, 5, 7, 1, 2, 6, 7),
                ClothingItem.Create("out_trench", "Black Parade Trench", "GRIM LUXE",
                    ClothingCategory.Outerwear, ClothingSlot.Outerwear, Rarity.Epic, 740,
                    MeshStyle.TrenchCoat, Black, OffBlack,
                    new[] { "villain", "dramatic", "dark", "formal", "opium" },
                    9, 9, 3, 7, 8, 7, 0, 7, 9),
                ClothingItem.Create("out_fur", "Empress Fur Coat", "ROYAL ROT",
                    ClothingCategory.Outerwear, ClothingSlot.Outerwear, Rarity.Grail, 1200,
                    MeshStyle.FurCoat, new Color(0.20f, 0.14f, 0.18f), Velvet,
                    new[] { "royal", "gothic", "luxury", "statement" },
                    9, 7, 2, 9, 8, 5, 1, 9, 8),
                ClothingItem.Create("out_puffer", "Street King Puffer", "SNEAKR TEMPLE",
                    ClothingCategory.Outerwear, ClothingSlot.Outerwear, Rarity.Uncommon, 330,
                    MeshStyle.Puffer, new Color(0.12f, 0.12f, 0.14f), HotPink,
                    new[] { "streetwear", "oversized", "winter" },
                    7, 3, 9, 3, 1, 0, 4, 4, 7),
                ClothingItem.Create("out_cyber", "Neon Circuit Jacket", "CHROME SAINT",
                    ClothingCategory.Outerwear, ClothingSlot.Outerwear, Rarity.Epic, 680,
                    MeshStyle.CyberJacket, new Color(0.10f, 0.10f, 0.14f), NeonCyan,
                    new[] { "cyber", "chrome", "neon", "futuristic" },
                    8, 4, 7, 6, 2, 0, 6, 8, 7),
                ClothingItem.Create("out_white_trench", "Angel Mantle Trench", "HALO BOULEVARD",
                    ClothingCategory.Outerwear, ClothingSlot.Outerwear, Rarity.Epic, 690,
                    MeshStyle.TrenchCoat, Cream, Chrome,
                    new[] { "angelic", "luxury", "clean", "formal" },
                    9, 1, 2, 9, 0, 8, 1, 6, 8),

                // ------------------------ BOTTOMS -----------------------
                ClothingItem.Create("bot_leather", "Serpent Leather Pants", "VANTA VEIL",
                    ClothingCategory.Bottoms, ClothingSlot.Bottom, Rarity.Rare, 390,
                    MeshStyle.LeatherPants, Black, OffBlack,
                    new[] { "leather", "dark", "opium", "goth" },
                    8, 8, 5, 6, 7, 2, 1, 5, 5),
                ClothingItem.Create("bot_cargo", "Field Ops Cargos", "NOVA CARTEL",
                    ClothingCategory.Bottoms, ClothingSlot.Bottom, Rarity.Uncommon, 220,
                    MeshStyle.CargoPants, Olive, new Color(0.2f, 0.22f, 0.16f),
                    new[] { "tactical", "streetwear", "baggy" },
                    7, 2, 8, 1, 1, 0, 3, 3, 6),
                ClothingItem.Create("bot_baggy", "Y2 Flood Baggy Jeans", "SNEAKR TEMPLE",
                    ClothingCategory.Bottoms, ClothingSlot.Bottom, Rarity.Common, 160,
                    MeshStyle.BaggyJeans, Denim, new Color(0.22f, 0.26f, 0.36f),
                    new[] { "y2k", "baggy", "streetwear", "denim" },
                    6, 1, 8, 1, 0, 0, 8, 3, 5),
                ClothingItem.Create("bot_miniskirt", "Vamp Mini Skirt", "ROYAL ROT",
                    ClothingCategory.Bottoms, ClothingSlot.Bottom, Rarity.Rare, 280,
                    MeshStyle.MiniSkirt, Black, BloodRed,
                    new[] { "goth", "y2k", "dark", "risky" },
                    7, 7, 4, 4, 8, 1, 7, 7, 4),
                ClothingItem.Create("bot_pleated", "Academy Pleated Skirt", "NOIR ACADEMY",
                    ClothingCategory.Bottoms, ClothingSlot.Bottom, Rarity.Uncommon, 190,
                    MeshStyle.PleatedSkirt, new Color(0.13f, 0.13f, 0.18f), BloodRed,
                    new[] { "darkacademia", "elegant", "school" },
                    6, 3, 3, 4, 4, 6, 2, 3, 4),
                ClothingItem.Create("bot_tailored", "Heir Tailored Slacks", "LOFT MONEY",
                    ClothingCategory.Bottoms, ClothingSlot.Bottom, Rarity.Rare, 360,
                    MeshStyle.LeatherPants, new Color(0.75f, 0.70f, 0.60f), Cream,
                    new[] { "oldmoney", "tailored", "quietluxury", "formal" },
                    7, 0, 1, 9, 0, 8, 0, 2, 4),

                // ------------------------- SHOES ------------------------
                ClothingItem.Create("sho_platform", "Gravity Platform Boots", "STAGE DEMON",
                    ClothingCategory.Shoes, ClothingSlot.Shoes, Rarity.Epic, 540,
                    MeshStyle.PlatformBoots, Black, Chrome,
                    new[] { "goth", "platform", "statement", "opium" },
                    9, 8, 5, 5, 9, 2, 4, 8, 5),
                ClothingItem.Create("sho_chunky", "Temple Runner 900s", "SNEAKR TEMPLE",
                    ClothingCategory.Shoes, ClothingSlot.Shoes, Rarity.Rare, 420,
                    MeshStyle.ChunkySneakers, new Color(0.9f, 0.9f, 0.92f), NeonCyan,
                    new[] { "hype", "streetwear", "chunky", "y2k" },
                    7, 1, 9, 4, 0, 0, 7, 5, 4),
                ClothingItem.Create("sho_designer", "Saint Chrome Boots", "CHROME SAINT",
                    ClothingCategory.Shoes, ClothingSlot.Shoes, Rarity.Grail, 980,
                    MeshStyle.DesignerBoots, Chrome, new Color(0.6f, 0.65f, 0.75f),
                    new[] { "chrome", "luxury", "cyber", "statement" },
                    9, 5, 4, 9, 3, 4, 5, 9, 5),
                ClothingItem.Create("sho_loafers", "Regatta Loafers", "LOFT MONEY",
                    ClothingCategory.Shoes, ClothingSlot.Shoes, Rarity.Uncommon, 310,
                    MeshStyle.Loafers, new Color(0.35f, 0.22f, 0.14f), Cream,
                    new[] { "oldmoney", "formal", "quietluxury" },
                    6, 0, 1, 8, 0, 8, 0, 2, 3),

                // ----------------------- HEADWEAR -----------------------
                ClothingItem.Create("hat_beanie", "Crypt Beanie", "VANTA VEIL",
                    ClothingCategory.Headwear, ClothingSlot.Headwear, Rarity.Common, 80,
                    MeshStyle.Beanie, Black, OffBlack,
                    new[] { "dark", "streetwear", "cozy" },
                    4, 5, 6, 1, 4, 0, 1, 2, 3),
                ClothingItem.Create("hat_cap", "Cartel Snapback", "NOVA CARTEL",
                    ClothingCategory.Headwear, ClothingSlot.Headwear, Rarity.Common, 95,
                    MeshStyle.Cap, new Color(0.12f, 0.12f, 0.15f), NeonCyan,
                    new[] { "streetwear", "cyber" },
                    4, 1, 7, 1, 0, 0, 4, 2, 3),
                ClothingItem.Create("hat_halo", "Seraph Halo Ring", "HALO BOULEVARD",
                    ClothingCategory.Headwear, ClothingSlot.Headwear, Rarity.Grail, 1500,
                    MeshStyle.Halo, FFPalette.Gold, Cream,
                    new[] { "angelic", "statement", "luxury", "runway" },
                    9, 2, 1, 9, 1, 3, 2, 10, 4),

                // ---------------------- ACCESSORIES ---------------------
                ClothingItem.Create("acc_shades", "Chrome Saint Shades", "CHROME SAINT",
                    ClothingCategory.Accessories, ClothingSlot.FaceAccessory, Rarity.Rare, 350,
                    MeshStyle.ChromeShades, new Color(0.15f, 0.15f, 0.18f), Chrome,
                    new[] { "chrome", "cyber", "cool", "opium" },
                    6, 6, 6, 6, 3, 1, 5, 5, 3),
                ClothingItem.Create("acc_chainbelt", "Rot Chain Belt", "ROYAL ROT",
                    ClothingCategory.Accessories, ClothingSlot.Belt, Rarity.Uncommon, 210,
                    MeshStyle.ChainBelt, Chrome, Black,
                    new[] { "goth", "y2k", "chrome" },
                    5, 5, 4, 3, 6, 0, 6, 4, 5),
                ClothingItem.Create("acc_bag", "Vault Crossbody", "LOFT MONEY",
                    ClothingCategory.Bags, ClothingSlot.Bag, Rarity.Rare, 460,
                    MeshStyle.CrossbodyBag, new Color(0.35f, 0.25f, 0.18f), FFPalette.Gold,
                    new[] { "luxury", "oldmoney", "leather" },
                    6, 1, 4, 8, 0, 4, 1, 3, 6),

                // ------------------------ JEWELRY -----------------------
                ClothingItem.Create("jwl_chain", "Cuban Eclipse Chain", "GRIM LUXE",
                    ClothingCategory.Jewelry, ClothingSlot.Necklace, Rarity.Epic, 620,
                    MeshStyle.ChainNecklace, FFPalette.Gold, Chrome,
                    new[] { "luxury", "streetwear", "statement" },
                    6, 4, 7, 8, 2, 2, 3, 5, 5),
                ClothingItem.Create("jwl_choker", "Obsidian Choker", "VANTA VEIL",
                    ClothingCategory.Jewelry, ClothingSlot.Necklace, Rarity.Uncommon, 180,
                    MeshStyle.Choker, Black, Chrome,
                    new[] { "goth", "dark", "opium" },
                    5, 7, 3, 3, 8, 1, 3, 4, 4),
                ClothingItem.Create("jwl_hoops", "Gilded Hoops", "HALO BOULEVARD",
                    ClothingCategory.Jewelry, ClothingSlot.Earrings, Rarity.Uncommon, 160,
                    MeshStyle.HoopEarrings, FFPalette.Gold, Cream,
                    new[] { "luxury", "clean", "elegant" },
                    4, 1, 4, 7, 0, 4, 3, 2, 3),
                ClothingItem.Create("jwl_studs", "Void Piercing Set", "STAGE DEMON",
                    ClothingCategory.Jewelry, ClothingSlot.Earrings, Rarity.Rare, 240,
                    MeshStyle.StudSet, Chrome, Black,
                    new[] { "goth", "edgy", "opium", "punk" },
                    5, 7, 5, 2, 8, 0, 3, 6, 3),

                // -------------------------- HAIR ------------------------
                Hair("hair_bob", "Onyx Anime Bob", MeshStyle.HairBob, new Color(0.07f, 0.07f, 0.09f)),
                Hair("hair_long", "Raven Long & Straight", MeshStyle.HairLong, new Color(0.07f, 0.07f, 0.09f)),
                Hair("hair_wolf", "Midnight Wolf Cut", MeshStyle.HairWolf, new Color(0.10f, 0.09f, 0.11f)),
                Hair("hair_spiky", "Hero Spikes", MeshStyle.HairSpiky, new Color(0.08f, 0.07f, 0.10f)),
                Hair("hair_slick", "Slicked Villain", MeshStyle.HairSlick, new Color(0.06f, 0.06f, 0.08f)),
                Hair("hair_curly", "Cloud Curls", MeshStyle.HairCurly, new Color(0.12f, 0.08f, 0.06f)),
                Hair("hair_ponytail", "Editorial Ponytail", MeshStyle.HairPonytail, new Color(0.30f, 0.20f, 0.12f)),
                Hair("hair_twintails", "Neon Twin Tails", MeshStyle.HairTwinTails, new Color(0.16f, 0.07f, 0.20f)),
                Hair("hair_braids", "Crown Braids", MeshStyle.HairBraids, new Color(0.08f, 0.06f, 0.05f)),
                Hair("hair_shorthood", "Hood-Ready Crop", MeshStyle.HairShortHood, new Color(0.09f, 0.09f, 0.10f)),
            };
        }

        static ClothingItem Hair(string id, string name, MeshStyle style, Color color)
        {
            return ClothingItem.Create(id, name, "FINAL FIT SALON",
                ClothingCategory.Hair, ClothingSlot.Hair, Rarity.Common, 0,
                style, color, color * 1.4f,
                new[] { "hair" }, 5, 2, 2, 2, 2, 2, 2, 2, 0);
        }
    }
}
