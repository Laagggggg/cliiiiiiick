using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace FinalFit
{
    /// <summary>
    /// In-store HUD and the rack browse panel: dark glass card grid with brand
    /// labels, rarity badges, prices and Equip/Remove — clicking an item makes
    /// it appear on the player's body instantly.
    /// </summary>
    public class StoreUI : MonoBehaviour
    {
        public ThirdPersonController Player;
        public CameraController Cam;
        public AvatarEquipmentManager PlayerEquipment;

        Canvas _canvas;
        Text _prompt;
        Image _panel;
        Text _panelTitle;
        RectTransform _grid;
        Text _equippedList;

        public bool IsOpen { get; private set; }

        public void Build()
        {
            _canvas = UIFactory.CreateCanvas("StoreCanvas");
            _canvas.transform.SetParent(transform, false);

            // interaction prompt (bottom center)
            _prompt = UIFactory.Label(_canvas.transform, "", 30, FFPalette.TextBright,
                TextAnchor.MiddleCenter, FontStyle.Bold);
            UIFactory.Place(_prompt.rectTransform, new Vector2(0.5f, 0.12f),
                new Vector2(900, 50), Vector2.zero);

            // round theme banner (decorative for the vertical slice)
            var banner = UIFactory.GlassPanel(_canvas.transform, "ThemeBanner");
            UIFactory.Place(banner.rectTransform, new Vector2(0.5f, 0.965f),
                new Vector2(640, 54), Vector2.zero);
            var bannerText = UIFactory.Label(banner.transform,
                "ROUND THEME - OPIUM NIGHT      |      10:00", 24,
                FFPalette.NeonPink, TextAnchor.MiddleCenter, FontStyle.Bold);
            UIFactory.Stretch(bannerText.rectTransform);

            // currently equipped (left edge)
            var fitPanel = UIFactory.GlassPanel(_canvas.transform, "FitPanel");
            UIFactory.Place(fitPanel.rectTransform, new Vector2(0.085f, 0.5f),
                new Vector2(280, 460), Vector2.zero);
            var fitTitle = UIFactory.Label(fitPanel.transform, "YOUR FIT", 24,
                FFPalette.NeonPurple, TextAnchor.UpperCenter, FontStyle.Bold);
            UIFactory.Stretch(fitTitle.rectTransform, 14);
            _equippedList = UIFactory.Label(fitPanel.transform, "", 18,
                FFPalette.TextDim, TextAnchor.UpperLeft);
            UIFactory.Stretch(_equippedList.rectTransform, 18);
            _equippedList.rectTransform.offsetMax = new Vector2(-18, -52);

            // browse panel (right side, hidden until a rack opens)
            _panel = UIFactory.GlassPanel(_canvas.transform, "BrowsePanel");
            UIFactory.Place(_panel.rectTransform, new Vector2(0.74f, 0.5f),
                new Vector2(860, 880), Vector2.zero);

            _panelTitle = UIFactory.Label(_panel.transform, "", 30, FFPalette.TextBright,
                TextAnchor.UpperCenter, FontStyle.Bold);
            UIFactory.Stretch(_panelTitle.rectTransform, 16);

            var gridGo = UIFactory.Rect("ItemGrid", _panel.transform);
            gridGo.anchorMin = new Vector2(0, 0); gridGo.anchorMax = new Vector2(1, 1);
            gridGo.offsetMin = new Vector2(20, 70); gridGo.offsetMax = new Vector2(-20, -70);
            var layout = gridGo.gameObject.AddComponent<GridLayoutGroup>();
            layout.cellSize = new Vector2(400, 118);
            layout.spacing = new Vector2(14, 14);
            layout.childAlignment = TextAnchor.UpperCenter;
            _grid = gridGo;

            var closeBtn = UIFactory.NeonButton(_panel.transform, "CLOSE  [E]", Close, 20);
            UIFactory.Place((RectTransform)closeBtn.transform, new Vector2(0.5f, 0f),
                new Vector2(220, 48), new Vector2(0, 38));

            _panel.gameObject.SetActive(false);
            RefreshEquippedList();
        }

        public void ShowPrompt(string text)
        {
            if (_prompt == null) return;
            _prompt.text = text ?? "";
        }

        public void Open(ClothingRack rack)
        {
            IsOpen = true;
            _panel.gameObject.SetActive(true);
            _panelTitle.text = rack.ZoneName.ToUpperInvariant();
            ShowPrompt(null);
            PopulateGrid(rack.Category);
            SetGameplayLocked(true);
        }

        public void Close()
        {
            IsOpen = false;
            _panel.gameObject.SetActive(false);
            SetGameplayLocked(false);
        }

        void SetGameplayLocked(bool locked)
        {
            if (Player != null) Player.InputLocked = locked;
            if (Cam != null) Cam.InputLocked = locked;
            Cursor.lockState = locked ? CursorLockMode.None : CursorLockMode.Locked;
            Cursor.visible = locked;
        }

        void PopulateGrid(ClothingCategory category)
        {
            foreach (Transform child in _grid) Destroy(child.gameObject);

            List<ClothingItem> items = ClothingDatabase.ByCategory(category);
            foreach (var item in items) BuildItemCard(item);
        }

        void BuildItemCard(ClothingItem item)
        {
            var card = UIFactory.Panel(_grid, "Card_" + item.Id,
                new Color(0.10f, 0.09f, 0.16f, 0.97f));
            card.gameObject.AddComponent<UIHoverScale>();

            // rarity stripe
            var stripe = UIFactory.Panel(card.transform, "Rarity", ClothingItem.RarityColor(item.Rarity));
            var srt = stripe.rectTransform;
            srt.anchorMin = new Vector2(0, 0); srt.anchorMax = new Vector2(0, 1);
            srt.offsetMin = Vector2.zero; srt.offsetMax = new Vector2(6, 0);

            // color swatch
            var swatch = UIFactory.Panel(card.transform, "Swatch", item.PrimaryColor);
            UIFactory.Place(swatch.rectTransform, new Vector2(0.12f, 0.62f),
                new Vector2(54, 54), Vector2.zero);
            var swatch2 = UIFactory.Panel(card.transform, "Swatch2", item.SecondaryColor);
            UIFactory.Place(swatch2.rectTransform, new Vector2(0.12f, 0.18f),
                new Vector2(54, 16), Vector2.zero);

            var name = UIFactory.Label(card.transform, item.ItemName, 21,
                ClothingItem.RarityColor(item.Rarity), TextAnchor.UpperLeft, FontStyle.Bold);
            UIFactory.Place(name.rectTransform, new Vector2(0.55f, 0.78f),
                new Vector2(270, 30), Vector2.zero);

            var brand = UIFactory.Label(card.transform,
                $"{item.Brand}  ·  {item.Rarity}  ·  ${item.Price}", 16,
                FFPalette.TextDim, TextAnchor.UpperLeft);
            UIFactory.Place(brand.rectTransform, new Vector2(0.55f, 0.52f),
                new Vector2(270, 24), Vector2.zero);

            bool equipped = PlayerEquipment != null && PlayerEquipment.IsEquipped(item);
            Button btn = null;
            btn = UIFactory.NeonButton(card.transform,
                equipped ? "REMOVE" : "EQUIP",
                () =>
                {
                    if (PlayerEquipment == null) return;
                    if (PlayerEquipment.IsEquipped(item)) PlayerEquipment.Unequip(item.Slot);
                    else PlayerEquipment.Equip(item);
                    var label = btn.GetComponentInChildren<Text>();
                    if (label != null)
                        label.text = PlayerEquipment.IsEquipped(item) ? "REMOVE" : "EQUIP";
                    RefreshEquippedList();
                }, 17, !equipped);
            UIFactory.Place((RectTransform)btn.transform, new Vector2(0.72f, 0.2f),
                new Vector2(150, 36), Vector2.zero);
        }

        public void RefreshEquippedList()
        {
            if (_equippedList == null || PlayerEquipment == null) return;
            var sb = new System.Text.StringBuilder("\n\n");
            foreach (var pair in PlayerEquipment.Equipped)
                sb.AppendLine($"{pair.Key}\n   <b>{pair.Value.ItemName}</b>\n");
            _equippedList.supportRichText = true;
            _equippedList.text = sb.ToString();
        }
    }
}
