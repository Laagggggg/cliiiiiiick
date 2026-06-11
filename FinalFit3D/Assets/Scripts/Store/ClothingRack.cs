using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// An interactable store fixture (rack / shelf / counter / booth) that
    /// opens the browse UI for one clothing category when the player presses E
    /// nearby.
    /// </summary>
    public class ClothingRack : MonoBehaviour
    {
        public ClothingCategory Category;
        public string ZoneName;
        public float InteractRadius = 2.6f;

        public string Prompt => $"Press E — Browse {ZoneName}";
    }
}
