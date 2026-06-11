using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace FinalFit
{
    /// <summary>
    /// Character creator: preset buttons on the left, body sliders on the
    /// right, live rotating avatar in the middle. Every change rebuilds the
    /// placeholder rig (throttled), which is exactly how a blendshape-driven
    /// real model will later receive the same BodyConfig.
    /// </summary>
    public class CharacterCreatorBuilder : MonoBehaviour
    {
        BodyConfig _cfg;
        AvatarPresetType _preset;
        FacePresetType _face;
        int _skinTone;
        int _hairIndex;
        List<ClothingItem> _hairOptions;

        AvatarRig _avatar;
        float _spin;
        bool _dirty;
        float _lastRebuild;

        readonly List<Slider> _sliders = new List<Slider>();
        (string label, System.Func<float> get, System.Action<float> set, float min, float max)[] _sliderDefs;
        Text _faceLabel;
        Text _hairLabel;

        void Start()
        {
            var gm = GameManager.Ensure();
            _preset = gm.SelectedPreset;
            _face = gm.SelectedFace;
            _cfg = gm.Body ?? AvatarPresets.BodyFor(_preset);
            gm.Body = _cfg;
            _hairOptions = ClothingDatabase.ByCategory(ClothingCategory.Hair);
            _hairIndex = Mathf.Max(0, _hairOptions.FindIndex(
                h => h.Id == (gm.Outfit.Get(ClothingSlot.Hair) ?? AvatarPresets.DefaultHairId(_preset))));

            SceneKit.MoodLighting(new Color(0.12f, 0.10f, 0.18f), 0.4f);
            SceneKit.CreateCamera(new Vector3(0, 1.45f, -3.1f), new Vector3(0, 1.05f, 0), 48f);

            SceneKit.Box(null, "Floor", new Vector3(0, -0.05f, 0), new Vector3(16, 0.1f, 16),
                MaterialFactory.Solid(FFPalette.FloorDark, 0.3f, 0.85f));
            SceneKit.Box(null, "Backdrop", new Vector3(0, 3f, 4f), new Vector3(16, 8f, 0.2f),
                MaterialFactory.Solid(FFPalette.WallDark));
            SceneKit.NeonStrip(null, new Vector3(0, 0.04f, 0), new Vector3(2.0f, 0.02f, 2.0f),
                FFPalette.NeonPink);
            SceneKit.SpotLight(new Vector3(2.4f, 3.2f, -2f), new Vector3(0, 1f, 0), FFPalette.NeonPink, 6f);
            SceneKit.SpotLight(new Vector3(-2.4f, 3.2f, -2f), new Vector3(0, 1f, 0), FFPalette.NeonCyan, 6f);
            SceneKit.SpotLight(new Vector3(0, 4f, -1f), new Vector3(0, 1.2f, 0), Color.white, 4f);

            DefineSliders();
            BuildUI();
            Rebuild(force: true);
        }

        void Update()
        {
            _spin += Time.deltaTime * 18f;
            if (_avatar != null)
                _avatar.transform.rotation = Quaternion.Euler(0, 180f + _spin, 0);

            if (_dirty && Time.time - _lastRebuild > 0.12f)
                Rebuild(force: true);
        }

        void Rebuild(bool force = false)
        {
            if (!force) { _dirty = true; return; }
            _dirty = false;
            _lastRebuild = Time.time;

            float keepSpin = _spin;
            if (_avatar != null) Destroy(_avatar.gameObject);

            var gm = GameManager.I;
            _avatar = AvatarBuilder.Build(null, _preset, _cfg, _face, _skinTone);
            _avatar.transform.position = new Vector3(0, 0.02f, 0);
            _avatar.transform.rotation = Quaternion.Euler(0, 180f + keepSpin, 0);
            _avatar.Equipment.Init(_avatar, gm.Outfit);

            // hair comes from the outfit so it carries into the store
            if (_hairOptions.Count > 0)
                _avatar.Equipment.Equip(_hairOptions[_hairIndex]);
            _avatar.Equipment.ApplyOutfit(gm.Outfit);
        }

        void DefineSliders()
        {
            _sliderDefs = new (string, System.Func<float>, System.Action<float>, float, float)[]
            {
                ("Height",        () => _cfg.height,         v => _cfg.height = v,         0.85f, 1.20f),
                ("Head Size",     () => _cfg.headSize,       v => _cfg.headSize = v,       0.80f, 1.25f),
                ("Shoulders",     () => _cfg.shoulderWidth,  v => _cfg.shoulderWidth = v,  0.70f, 1.50f),
                ("Chest",         () => _cfg.chest,          v => _cfg.chest = v,          0.70f, 1.60f),
                ("Waist",         () => _cfg.waist,          v => _cfg.waist = v,          0.60f, 1.40f),
                ("Hips",          () => _cfg.hips,           v => _cfg.hips = v,           0.70f, 1.55f),
                ("Arm Thickness", () => _cfg.armThickness,   v => _cfg.armThickness = v,   0.70f, 1.60f),
                ("Leg Length",    () => _cfg.legLength,      v => _cfg.legLength = v,      0.85f, 1.20f),
                ("Thighs",        () => _cfg.thighThickness, v => _cfg.thighThickness = v, 0.70f, 1.55f),
                ("Calves",        () => _cfg.calfThickness,  v => _cfg.calfThickness = v,  0.70f, 1.40f),
                ("Glutes",        () => _cfg.glute,          v => _cfg.glute = v,          0.70f, 1.60f),
                ("Muscle",        () => _cfg.muscle,         v => _cfg.muscle = v,         0.60f, 1.60f),
                ("Body Scale",    () => _cfg.bodyScale,      v => _cfg.bodyScale = v,      0.90f, 1.12f),
                ("Posture",       () => _cfg.posture,        v => _cfg.posture = v,       -1.00f, 1.00f),
                ("Hand Size",     () => _cfg.handSize,       v => _cfg.handSize = v,       0.75f, 1.30f),
                ("Foot Size",     () => _cfg.footSize,       v => _cfg.footSize = v,       0.75f, 1.35f),
            };
        }

        void BuildUI()
        {
            var canvas = UIFactory.CreateCanvas("CreatorCanvas");

            var header = UIFactory.Label(canvas.transform, "CHARACTER CREATOR", 44,
                FFPalette.TextBright, TextAnchor.MiddleCenter, FontStyle.Bold);
            UIFactory.Place(header.rectTransform, new Vector2(0.5f, 0.955f),
                new Vector2(800, 60), Vector2.zero);

            BuildPresetPanel(canvas);
            BuildSliderPanel(canvas);

            var go = UIFactory.NeonButton(canvas.transform, "ENTER THE STORE  →",
                () =>
                {
                    var gm = GameManager.I;
                    gm.SelectedPreset = _preset;
                    gm.SelectedFace = _face;
                    gm.Body = _cfg;
                    SceneLoader.Load(SceneLoader.FashionStore);
                }, 26, true);
            UIFactory.Place((RectTransform)go.transform, new Vector2(0.5f, 0.06f),
                new Vector2(440, 70), Vector2.zero);
        }

        void BuildPresetPanel(Canvas canvas)
        {
            var panel = UIFactory.GlassPanel(canvas.transform, "PresetPanel");
            UIFactory.Place(panel.rectTransform, new Vector2(0.135f, 0.5f),
                new Vector2(440, 900), Vector2.zero);

            var title = UIFactory.Label(panel.transform, "PRESETS", 26,
                FFPalette.NeonPurple, TextAnchor.UpperCenter, FontStyle.Bold);
            UIFactory.Stretch(title.rectTransform, 16);

            var presets = (AvatarPresetType[])System.Enum.GetValues(typeof(AvatarPresetType));
            for (int i = 0; i < presets.Length; i++)
            {
                var p = presets[i];
                var btn = UIFactory.NeonButton(panel.transform, AvatarPresets.DisplayName(p),
                    () =>
                    {
                        _preset = p;
                        _cfg = AvatarPresets.BodyFor(p);
                        GameManager.I.Body = _cfg;
                        _face = AvatarPresets.DefaultFace(p);
                        _hairIndex = Mathf.Max(0, _hairOptions.FindIndex(
                            h => h.Id == AvatarPresets.DefaultHairId(p)));
                        RefreshSliderValues();
                        RefreshCycleLabels();
                        Rebuild(force: true);
                    }, 20);
                UIFactory.Place((RectTransform)btn.transform, new Vector2(0.5f, 1f),
                    new Vector2(380, 52), new Vector2(0, -78 - i * 62));
            }

            // skin tones
            var skinLabel = UIFactory.Label(panel.transform, "SKIN TONE", 20,
                FFPalette.TextDim, TextAnchor.MiddleCenter, FontStyle.Bold);
            UIFactory.Place(skinLabel.rectTransform, new Vector2(0.5f, 1f),
                new Vector2(380, 30), new Vector2(0, -530));
            for (int i = 0; i < AvatarPresets.SkinToneCount; i++)
            {
                int tone = i;
                var sw = UIFactory.Panel(panel.transform, "Skin" + i, AvatarPresets.SkinTone(i));
                UIFactory.Place(sw.rectTransform, new Vector2(0.5f, 1f),
                    new Vector2(56, 44), new Vector2(-128 + i * 64, -575));
                var b = sw.gameObject.AddComponent<Button>();
                b.targetGraphic = sw;
                b.onClick.AddListener(() => { _skinTone = tone; Rebuild(force: true); });
                sw.gameObject.AddComponent<UIHoverScale>();
            }

            _faceLabel = BuildCycler(panel.transform, "FACE", -640,
                () => { CycleFace(-1); }, () => { CycleFace(1); });
            _hairLabel = BuildCycler(panel.transform, "HAIR", -740,
                () => { CycleHair(-1); }, () => { CycleHair(1); });
            RefreshCycleLabels();
        }

        Text BuildCycler(Transform parent, string caption, float y,
            System.Action prev, System.Action next)
        {
            var cap = UIFactory.Label(parent, caption, 20, FFPalette.TextDim,
                TextAnchor.MiddleCenter, FontStyle.Bold);
            UIFactory.Place(cap.rectTransform, new Vector2(0.5f, 1f),
                new Vector2(380, 28), new Vector2(0, y));

            var left = UIFactory.NeonButton(parent, "<", prev, 22);
            UIFactory.Place((RectTransform)left.transform, new Vector2(0.5f, 1f),
                new Vector2(54, 44), new Vector2(-165, y - 42));
            var right = UIFactory.NeonButton(parent, ">", next, 22);
            UIFactory.Place((RectTransform)right.transform, new Vector2(0.5f, 1f),
                new Vector2(54, 44), new Vector2(165, y - 42));

            var value = UIFactory.Label(parent, "", 21, FFPalette.TextBright,
                TextAnchor.MiddleCenter, FontStyle.Bold);
            UIFactory.Place(value.rectTransform, new Vector2(0.5f, 1f),
                new Vector2(250, 44), new Vector2(0, y - 42));
            return value;
        }

        void CycleFace(int dir)
        {
            int count = System.Enum.GetValues(typeof(FacePresetType)).Length;
            _face = (FacePresetType)(((int)_face + dir + count) % count);
            RefreshCycleLabels();
            Rebuild(force: true);
        }

        void CycleHair(int dir)
        {
            if (_hairOptions.Count == 0) return;
            _hairIndex = (_hairIndex + dir + _hairOptions.Count) % _hairOptions.Count;
            RefreshCycleLabels();
            Rebuild(force: true);
        }

        void RefreshCycleLabels()
        {
            if (_faceLabel != null) _faceLabel.text = FacePresets.DisplayName(_face);
            if (_hairLabel != null && _hairOptions.Count > 0)
                _hairLabel.text = _hairOptions[_hairIndex].ItemName;
        }

        void BuildSliderPanel(Canvas canvas)
        {
            var panel = UIFactory.GlassPanel(canvas.transform, "SliderPanel");
            UIFactory.Place(panel.rectTransform, new Vector2(0.865f, 0.5f),
                new Vector2(460, 900), Vector2.zero);

            var title = UIFactory.Label(panel.transform, "BODY SLIDERS", 26,
                FFPalette.NeonPink, TextAnchor.UpperCenter, FontStyle.Bold);
            UIFactory.Stretch(title.rectTransform, 16);

            _sliders.Clear();
            for (int i = 0; i < _sliderDefs.Length; i++)
            {
                var def = _sliderDefs[i];
                float y = -72 - i * 50;

                var label = UIFactory.Label(panel.transform, def.label, 18,
                    FFPalette.TextDim, TextAnchor.MiddleLeft);
                UIFactory.Place(label.rectTransform, new Vector2(0.5f, 1f),
                    new Vector2(150, 30), new Vector2(-140, y));

                var slider = UIFactory.NeonSlider(panel.transform, def.min, def.max,
                    def.get(), v => { def.set(v); Rebuild(); });
                UIFactory.Place((RectTransform)slider.transform, new Vector2(0.5f, 1f),
                    new Vector2(230, 30), new Vector2(80, y));
                _sliders.Add(slider);
            }
        }

        void RefreshSliderValues()
        {
            for (int i = 0; i < _sliders.Count && i < _sliderDefs.Length; i++)
                _sliders[i].SetValueWithoutNotify(_sliderDefs[i].get());
        }
    }
}
