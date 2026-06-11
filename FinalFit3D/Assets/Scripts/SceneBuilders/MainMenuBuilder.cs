using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Main menu: a spotlit showcase avatar slowly rotating behind dark-glass
    /// UI with the neon FINAL FIT wordmark.
    /// </summary>
    public class MainMenuBuilder : MonoBehaviour
    {
        void Start()
        {
            GameManager.Ensure();
            SceneKit.MoodLighting(new Color(0.10f, 0.08f, 0.16f), 0.35f);
            SceneKit.CreateCamera(new Vector3(0, 1.5f, -3.4f), new Vector3(0, 1.2f, 0), 50f);

            // showcase stage
            var floor = SceneKit.Box(null, "Floor", new Vector3(0, -0.05f, 0),
                new Vector3(20, 0.1f, 20), MaterialFactory.Solid(FFPalette.FloorDark, 0.3f, 0.85f));
            SceneKit.Cylinder(floor, "Pedestal", new Vector3(0, 1.2f, 0),
                new Vector3(0.09f, 1.0f, 0.09f), MaterialFactory.Solid(FFPalette.WallDark, 0.4f, 0.7f));
            SceneKit.NeonStrip(null, new Vector3(0, 0.06f, 0), new Vector3(2.4f, 0.02f, 2.4f),
                FFPalette.NeonPurple);

            var rnd = new System.Random(System.DateTime.Now.Millisecond);
            var showcase = SceneKit.RandomNPC(null, new Vector3(0, 0.12f, 0), rnd);
            showcase.gameObject.AddComponent<SpinSlow>();

            SceneKit.SpotLight(new Vector3(2.5f, 3.5f, -2f), new Vector3(0, 1.1f, 0),
                FFPalette.NeonPink, 7f);
            SceneKit.SpotLight(new Vector3(-2.5f, 3.5f, -2f), new Vector3(0, 1.1f, 0),
                FFPalette.NeonCyan, 7f);
            SceneKit.SpotLight(new Vector3(0, 4f, 2.5f), new Vector3(0, 1.1f, 0),
                FFPalette.NeonPurple, 6f);

            BuildUI();
        }

        void BuildUI()
        {
            var canvas = UIFactory.CreateCanvas("MenuCanvas");

            var title = UIFactory.Label(canvas.transform, "FINAL FIT", 130,
                FFPalette.TextBright, TextAnchor.MiddleCenter, FontStyle.Bold);
            UIFactory.Place(title.rectTransform, new Vector2(0.5f, 0.80f),
                new Vector2(1200, 150), Vector2.zero);

            var underline = UIFactory.Panel(canvas.transform, "TitleNeon", Color.white);
            underline.sprite = UIFactory.GradientSprite;
            UIFactory.Place(underline.rectTransform, new Vector2(0.5f, 0.725f),
                new Vector2(560, 6), Vector2.zero);
            underline.gameObject.AddComponent<UINeonPulse>();

            var subtitle = UIFactory.Label(canvas.transform,
                "ANIME FASHION BATTLE  ·  STYLE IS THE WEAPON", 26,
                FFPalette.TextDim, TextAnchor.MiddleCenter);
            UIFactory.Place(subtitle.rectTransform, new Vector2(0.5f, 0.685f),
                new Vector2(900, 40), Vector2.zero);

            var startBtn = UIFactory.NeonButton(canvas.transform, "ENTER THE FIT",
                () => SceneLoader.Load(SceneLoader.CharacterCreator), 30, true);
            UIFactory.Place((RectTransform)startBtn.transform, new Vector2(0.5f, 0.30f),
                new Vector2(420, 76), Vector2.zero);

            var quitBtn = UIFactory.NeonButton(canvas.transform, "QUIT",
                () =>
                {
                    Application.Quit();
#if UNITY_EDITOR
                    UnityEditor.EditorApplication.isPlaying = false;
#endif
                }, 24);
            UIFactory.Place((RectTransform)quitBtn.transform, new Vector2(0.5f, 0.20f),
                new Vector2(300, 60), Vector2.zero);

            var version = UIFactory.Label(canvas.transform,
                "vertical slice 0.1 — placeholder visuals, real systems", 18,
                FFPalette.TextDim, TextAnchor.LowerRight);
            UIFactory.Place(version.rectTransform, new Vector2(0.86f, 0.04f),
                new Vector2(600, 30), Vector2.zero);
        }
    }
}
