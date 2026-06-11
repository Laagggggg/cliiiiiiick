namespace FinalFit
{
    public enum ClothingSlot
    {
        Hair,
        Headwear,
        FaceAccessory,
        Earrings,
        Necklace,
        Top,
        Underlayer,
        Outerwear,
        Bottom,
        Belt,
        Shoes,
        Legwear,
        Gloves,
        Bag,
        BackAccessory,
        RunwayProp
    }

    public enum ClothingCategory
    {
        Tops,
        Outerwear,
        Bottoms,
        Shoes,
        Headwear,
        Accessories,
        Jewelry,
        Hair,
        Bags,
        FullOutfits
    }

    public enum Rarity
    {
        Common,
        Uncommon,
        Rare,
        Epic,
        Grail
    }

    /// <summary>Which procedural mesh recipe ClothingMeshFactory uses.</summary>
    public enum MeshStyle
    {
        // tops
        OversizedHoodie, MeshTop, LaceBlouse, TankTop, OversizedTee, TacticalVest,
        // outerwear
        CroppedJacket, TrenchCoat, FurCoat, Puffer, CyberJacket,
        // bottoms
        LeatherPants, CargoPants, BaggyJeans, MiniSkirt, PleatedSkirt,
        // shoes
        PlatformBoots, ChunkySneakers, DesignerBoots, Loafers,
        // headwear
        Beanie, Cap, Halo,
        // accessories / jewelry
        ChromeShades, ChainNecklace, Choker, ChainBelt, CrossbodyBag, HoopEarrings, StudSet,
        // hair
        HairBob, HairLong, HairWolf, HairSpiky, HairSlick, HairCurly,
        HairPonytail, HairTwinTails, HairBraids, HairShortHood
    }
}
