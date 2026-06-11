using System.Collections.Generic;
using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Owns what an avatar is wearing. Equipping spawns visible meshes via
    /// ClothingMeshFactory and tears down whatever was in the slot before.
    /// Optionally mirrors changes into a shared OutfitState (the player's
    /// persistent outfit); NPC/mannequin avatars just pass null.
    /// </summary>
    public class AvatarEquipmentManager : MonoBehaviour
    {
        AvatarRig _rig;
        OutfitState _trackedOutfit;
        readonly Dictionary<ClothingSlot, ClothingItem> _equipped =
            new Dictionary<ClothingSlot, ClothingItem>();
        readonly Dictionary<ClothingSlot, List<GameObject>> _spawned =
            new Dictionary<ClothingSlot, List<GameObject>>();

        public void Init(AvatarRig rig, OutfitState trackedOutfit = null)
        {
            _rig = rig;
            _trackedOutfit = trackedOutfit;
        }

        public ClothingItem GetEquipped(ClothingSlot slot)
        {
            _equipped.TryGetValue(slot, out var item);
            return item;
        }

        public bool IsEquipped(ClothingItem item)
        {
            return item != null && GetEquipped(item.Slot) == item;
        }

        public IReadOnlyDictionary<ClothingSlot, ClothingItem> Equipped => _equipped;

        public void Equip(ClothingItem item)
        {
            if (item == null || _rig == null) return;
            Unequip(item.Slot);
            _equipped[item.Slot] = item;
            _spawned[item.Slot] = ClothingMeshFactory.Equip(_rig, item);
            _trackedOutfit?.Set(item.Slot, item.Id);
        }

        public void Unequip(ClothingSlot slot)
        {
            if (_spawned.TryGetValue(slot, out var pieces))
            {
                foreach (var go in pieces)
                    if (go != null) Destroy(go);
                _spawned.Remove(slot);
            }
            _equipped.Remove(slot);
            _trackedOutfit?.Clear(slot);
        }

        /// <summary>Re-apply a saved outfit (e.g. after a scene load or rebuild).</summary>
        public void ApplyOutfit(OutfitState outfit)
        {
            if (outfit == null) return;
            foreach (var pair in outfit.Items)
            {
                var item = ClothingDatabase.Find(pair.Value);
                if (item != null) Equip(item);
            }
        }
    }

    /// <summary>Serializable record of which item id sits in each slot.</summary>
    [System.Serializable]
    public class OutfitState
    {
        readonly Dictionary<ClothingSlot, string> _items = new Dictionary<ClothingSlot, string>();

        public IReadOnlyDictionary<ClothingSlot, string> Items => _items;

        public void Set(ClothingSlot slot, string itemId) { _items[slot] = itemId; }
        public void Clear(ClothingSlot slot) { _items.Remove(slot); }

        public string Get(ClothingSlot slot)
        {
            _items.TryGetValue(slot, out var id);
            return id;
        }
    }
}
