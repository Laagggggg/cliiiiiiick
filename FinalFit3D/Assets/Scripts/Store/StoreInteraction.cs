using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Watches for the nearest interactable rack, shows the "Press E" prompt
    /// and opens the browse UI. Lives on the player.
    /// </summary>
    public class StoreInteraction : MonoBehaviour
    {
        public StoreUI UI;

        ClothingRack[] _racks;
        ClothingRack _nearest;

        void Start()
        {
            _racks = Object.FindObjectsByType<ClothingRack>(FindObjectsSortMode.None);
        }

        void Update()
        {
            if (UI == null) return;

            if (UI.IsOpen)
            {
                if (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.E))
                    UI.Close();
                return;
            }

            _nearest = null;
            float best = float.MaxValue;
            foreach (var rack in _racks)
            {
                if (rack == null) continue;
                float d = Vector3.Distance(transform.position, rack.transform.position);
                if (d < rack.InteractRadius && d < best) { best = d; _nearest = rack; }
            }

            UI.ShowPrompt(_nearest != null ? _nearest.Prompt : null);

            if (_nearest != null && Input.GetKeyDown(KeyCode.E))
                UI.Open(_nearest);
        }
    }
}
