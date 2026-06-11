using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Persistent game state: which avatar preset the player chose, their body
    /// slider values, and the outfit they currently have equipped. Survives
    /// scene loads so the store rebuilds the same avatar the creator produced.
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        public static GameManager I { get; private set; }

        public AvatarPresetType SelectedPreset = AvatarPresetType.FemaleCurvyAnime;
        public FacePresetType SelectedFace = FacePresetType.SoftAnime;
        public BodyConfig Body;   // null until the creator (or a scene guard) sets it
        public OutfitState Outfit = new OutfitState();

        public static GameManager Ensure()
        {
            if (I == null)
            {
                var existing = FindFirstObjectByType<GameManager>();
                if (existing != null) I = existing;
                else
                {
                    var go = new GameObject("GameManager");
                    I = go.AddComponent<GameManager>();
                }
            }
            return I;
        }

        void Awake()
        {
            if (I != null && I != this) { Destroy(gameObject); return; }
            I = this;
            DontDestroyOnLoad(gameObject);
        }
    }
}
