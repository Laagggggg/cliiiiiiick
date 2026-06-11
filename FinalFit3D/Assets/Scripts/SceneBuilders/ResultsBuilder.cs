using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Phase-2 scene placeholder. Will show total score, category breakdown,
    /// judge comments and rank once JudgeScoringSystem lands.
    /// </summary>
    public class ResultsBuilder : MonoBehaviour
    {
        void Start()
        {
            GameManager.Ensure();
            SceneKit.MoodLighting(new Color(0.08f, 0.07f, 0.13f), 0.3f);
            SceneKit.CreateCamera(new Vector3(0, 1.4f, -4f), new Vector3(0, 1f, 0), 50f);

            var canvas = UIFactory.CreateCanvas("ResultsCanvas");
            var title = UIFactory.Label(canvas.transform, "RESULTS", 90, FFPalette.TextBright,
                TextAnchor.MiddleCenter, FontStyle.Bold);
            UIFactory.Place(title.rectTransform, new Vector2(0.5f, 0.75f), new Vector2(800, 120), Vector2.zero);
            var note = UIFactory.Label(canvas.transform,
                "Scoring breakdown, judge comments and rank arrive with the judging phase.", 24,
                FFPalette.TextDim, TextAnchor.MiddleCenter);
            UIFactory.Place(note.rectTransform, new Vector2(0.5f, 0.6f), new Vector2(1200, 40), Vector2.zero);

            var store = UIFactory.NeonButton(canvas.transform, "RETURN TO STORE",
                () => SceneLoader.Load(SceneLoader.FashionStore), 24, true);
            UIFactory.Place((RectTransform)store.transform, new Vector2(0.5f, 0.35f), new Vector2(380, 64), Vector2.zero);
            var menu = UIFactory.NeonButton(canvas.transform, "MAIN MENU",
                () => SceneLoader.Load(SceneLoader.MainMenu), 22);
            UIFactory.Place((RectTransform)menu.transform, new Vector2(0.5f, 0.25f), new Vector2(300, 56), Vector2.zero);

            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }
    }
}
