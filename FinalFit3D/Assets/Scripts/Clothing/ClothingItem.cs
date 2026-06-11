using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// One piece of fashion. ScriptableObject so designers can later author
    /// .asset files; the prototype also creates instances in memory via
    /// ClothingDatabase so the game runs with zero hand-made assets.
    /// </summary>
    [CreateAssetMenu(menuName = "FinalFit/Clothing Item")]
    public class ClothingItem : ScriptableObject
    {
        public string Id;
        public string ItemName;
        public string Brand;
        public ClothingCategory Category;
        public ClothingSlot Slot;
        public Rarity Rarity;
        public int Price;
        public string[] ThemeTags = new string[0];
        public Color PrimaryColor = Color.white;
        public Color SecondaryColor = Color.gray;
        public MeshStyle MeshStyle;

        [Header("Judge stats (0-10)")]
        public int SilhouetteScore;
        public int OpiumScore;
        public int StreetwearScore;
        public int LuxuryScore;
        public int GothScore;
        public int FormalScore;
        public int Y2kScore;
        public int RiskScore;
        public int LayeringScore;

        public static ClothingItem Create(string id, string itemName, string brand,
            ClothingCategory category, ClothingSlot slot, Rarity rarity, int price,
            MeshStyle meshStyle, Color primary, Color secondary, string[] tags,
            int silhouette = 5, int opium = 0, int streetwear = 0, int luxury = 0,
            int goth = 0, int formal = 0, int y2k = 0, int risk = 3, int layering = 3)
        {
            var item = CreateInstance<ClothingItem>();
            item.name = id;
            item.Id = id;
            item.ItemName = itemName;
            item.Brand = brand;
            item.Category = category;
            item.Slot = slot;
            item.Rarity = rarity;
            item.Price = price;
            item.MeshStyle = meshStyle;
            item.PrimaryColor = primary;
            item.SecondaryColor = secondary;
            item.ThemeTags = tags ?? new string[0];
            item.SilhouetteScore = silhouette;
            item.OpiumScore = opium;
            item.StreetwearScore = streetwear;
            item.LuxuryScore = luxury;
            item.GothScore = goth;
            item.FormalScore = formal;
            item.Y2kScore = y2k;
            item.RiskScore = risk;
            item.LayeringScore = layering;
            return item;
        }

        public static Color RarityColor(Rarity r)
        {
            switch (r)
            {
                case Rarity.Common: return new Color(0.7f, 0.7f, 0.75f);
                case Rarity.Uncommon: return new Color(0.4f, 0.9f, 0.5f);
                case Rarity.Rare: return new Color(0.35f, 0.6f, 1f);
                case Rarity.Epic: return FFPalette.NeonPurple;
                default: return FFPalette.Gold;
            }
        }
    }
}
