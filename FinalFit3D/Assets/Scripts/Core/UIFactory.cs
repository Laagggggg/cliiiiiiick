using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace FinalFit
{
    /// <summary>
    /// Builds the luxury cyber-anime UI entirely from code: dark glass panels,
    /// purple/pink gradient accents, neon outlines and hover animations.
    /// No prefabs needed, so every scene can construct its UI at runtime.
    /// </summary>
    public static class UIFactory
    {
        static Font _font;
        public static Font DefaultFont
        {
            get
            {
                if (_font == null) _font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                return _font;
            }
        }

        static Sprite _gradientSprite;
        public static Sprite GradientSprite
        {
            get
            {
                if (_gradientSprite == null)
                {
                    var tex = new Texture2D(1, 64, TextureFormat.RGBA32, false);
                    for (int y = 0; y < 64; y++)
                    {
                        float t = y / 63f;
                        tex.SetPixel(0, y, Color.Lerp(FFPalette.NeonPink, FFPalette.NeonPurple, t));
                    }
                    tex.Apply();
                    tex.wrapMode = TextureWrapMode.Clamp;
                    _gradientSprite = Sprite.Create(tex, new Rect(0, 0, 1, 64), new Vector2(0.5f, 0.5f));
                }
                return _gradientSprite;
            }
        }

        public static Canvas CreateCanvas(string name = "Canvas")
        {
            var go = new GameObject(name, typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var canvas = go.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = go.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
            EnsureEventSystem();
            return canvas;
        }

        public static void EnsureEventSystem()
        {
            if (Object.FindFirstObjectByType<EventSystem>() == null)
            {
                new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
            }
        }

        public static RectTransform Rect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            return rt;
        }

        public static Image Panel(Transform parent, string name, Color color)
        {
            var rt = Rect(name, parent);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = color;
            return img;
        }

        /// <summary>Dark glass panel with a thin neon edge along the top.</summary>
        public static Image GlassPanel(Transform parent, string name)
        {
            var panel = Panel(parent, name, FFPalette.PanelGlass);
            var edge = Panel(panel.transform, "NeonEdge", Color.white);
            edge.sprite = GradientSprite;
            var ert = edge.rectTransform;
            ert.anchorMin = new Vector2(0, 1); ert.anchorMax = new Vector2(1, 1);
            ert.offsetMin = new Vector2(0, -3); ert.offsetMax = new Vector2(0, 0);
            return panel;
        }

        public static Text Label(Transform parent, string text, int size, Color color,
            TextAnchor anchor = TextAnchor.MiddleCenter, FontStyle style = FontStyle.Normal)
        {
            var rt = Rect("Label", parent);
            var t = rt.gameObject.AddComponent<Text>();
            t.font = DefaultFont;
            t.text = text;
            t.fontSize = size;
            t.color = color;
            t.alignment = anchor;
            t.fontStyle = style;
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            return t;
        }

        public static Button NeonButton(Transform parent, string label, System.Action onClick,
            int fontSize = 26, bool gradient = false)
        {
            var rt = Rect("Btn_" + label, parent);
            var img = rt.gameObject.AddComponent<Image>();
            if (gradient) { img.sprite = GradientSprite; img.color = Color.white; }
            else img.color = new Color(0.13f, 0.11f, 0.20f, 0.95f);

            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = img;
            var colors = btn.colors;
            colors.highlightedColor = new Color(1.25f, 1.2f, 1.45f, 1f);
            colors.pressedColor = new Color(0.8f, 0.7f, 1f, 1f);
            colors.fadeDuration = 0.08f;
            btn.colors = colors;
            if (onClick != null) btn.onClick.AddListener(() => onClick());

            // thin neon underline accent
            var underline = Panel(rt, "Underline", gradient ? Color.black : FFPalette.NeonPurple);
            var urt = underline.rectTransform;
            urt.anchorMin = new Vector2(0.06f, 0); urt.anchorMax = new Vector2(0.94f, 0);
            urt.offsetMin = new Vector2(0, 2); urt.offsetMax = new Vector2(0, 4);
            underline.raycastTarget = false;

            var txt = Label(rt, label, fontSize, gradient ? Color.black : FFPalette.TextBright,
                TextAnchor.MiddleCenter, FontStyle.Bold);
            Stretch(txt.rectTransform);

            rt.gameObject.AddComponent<UIHoverScale>();
            return btn;
        }

        public static Slider NeonSlider(Transform parent, float min, float max, float value,
            UnityEngine.Events.UnityAction<float> onChanged)
        {
            var rt = Rect("Slider", parent);
            var slider = rt.gameObject.AddComponent<Slider>();
            slider.minValue = min;
            slider.maxValue = max;

            var bg = Panel(rt, "Background", new Color(0.05f, 0.05f, 0.09f, 1f));
            var bgRt = bg.rectTransform;
            bgRt.anchorMin = new Vector2(0, 0.5f); bgRt.anchorMax = new Vector2(1, 0.5f);
            bgRt.sizeDelta = new Vector2(0, 8); bgRt.anchoredPosition = Vector2.zero;

            var fillArea = Rect("FillArea", rt);
            fillArea.anchorMin = new Vector2(0, 0.5f); fillArea.anchorMax = new Vector2(1, 0.5f);
            fillArea.sizeDelta = new Vector2(-12, 8); fillArea.anchoredPosition = Vector2.zero;
            var fill = Panel(fillArea, "Fill", Color.white);
            fill.sprite = GradientSprite;
            var fillRt = fill.rectTransform;
            fillRt.anchorMin = Vector2.zero; fillRt.anchorMax = Vector2.one;
            fillRt.offsetMin = Vector2.zero; fillRt.offsetMax = Vector2.zero;

            var handleArea = Rect("HandleArea", rt);
            handleArea.anchorMin = new Vector2(0, 0.5f); handleArea.anchorMax = new Vector2(1, 0.5f);
            handleArea.sizeDelta = new Vector2(-12, 0); handleArea.anchoredPosition = Vector2.zero;
            var handle = Panel(handleArea, "Handle", FFPalette.TextBright);
            handle.rectTransform.sizeDelta = new Vector2(16, 22);

            slider.fillRect = fillRt;
            slider.handleRect = handle.rectTransform;
            slider.targetGraphic = handle;
            slider.direction = Slider.Direction.LeftToRight;
            slider.value = value;
            if (onChanged != null) slider.onValueChanged.AddListener(onChanged);
            return slider;
        }

        public static void Stretch(RectTransform rt, float pad = 0)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = new Vector2(pad, pad);
            rt.offsetMax = new Vector2(-pad, -pad);
        }

        public static void Place(RectTransform rt, Vector2 anchor, Vector2 size, Vector2 offset)
        {
            rt.anchorMin = anchor;
            rt.anchorMax = anchor;
            rt.sizeDelta = size;
            rt.anchoredPosition = offset;
        }
    }

    /// <summary>Subtle scale-up on hover so buttons feel alive.</summary>
    public class UIHoverScale : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
    {
        float _target = 1f;

        public void OnPointerEnter(PointerEventData e) { _target = 1.05f; }
        public void OnPointerExit(PointerEventData e) { _target = 1f; }

        void Update()
        {
            float s = Mathf.Lerp(transform.localScale.x, _target, Time.unscaledDeltaTime * 12f);
            transform.localScale = new Vector3(s, s, 1f);
        }
    }

    /// <summary>Slow alpha pulse for neon accents.</summary>
    public class UINeonPulse : MonoBehaviour
    {
        public float Speed = 2.2f;
        public float Min = 0.55f;
        Graphic _g;

        void Awake() { _g = GetComponent<Graphic>(); }

        void Update()
        {
            if (_g == null) return;
            var c = _g.color;
            c.a = Mathf.Lerp(Min, 1f, (Mathf.Sin(Time.time * Speed) + 1f) * 0.5f);
            _g.color = c;
        }
    }
}
