using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// A competition theme the judges score against (phase 2). Authored as
    /// .asset files: Opium Night, Old Money Yacht, Cyber Angel, Gothic Runway,
    /// Streetwear Royalty, Red Carpet Villain, Y2K Mall Star, Luxury Airport
    /// Fit, Dark Academia, Chrome Saint.
    /// </summary>
    [CreateAssetMenu(menuName = "FinalFit/Round Theme")]
    public class RoundTheme : ScriptableObject
    {
        public string ThemeName;
        [TextArea] public string Description;
        public string[] RequiredTags;
        public string[] BonusTags;
        public string[] PenaltyTags;
        public Color[] PaletteSuggestions;
    }
}
