using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Phase-2 scene. For the vertical slice it shows the player's locked fit
    /// on a cinematic catwalk placeholder and routes back to the store.
    /// Full camera sequence + judging arrives with RunwayController /
    /// RunwayCameraController / JudgeScoringSystem.
    /// </summary>
    public class RunwayBuilder : MonoBehaviour
    {
        void Start()
        {
            var gm = GameManager.Ensure();
            SceneKit.MoodLighting(new Color(0.08f, 0.06f, 0.13f), 0.3f);
            SceneKit.CreateCamera(new Vector3(0, 1.6f, -5.5f), new Vector3(0, 1.1f, 0), 45f);

            SceneKit.Box(null, "Catwalk", new Vector3(0, -0.2f, 4), new Vector3(3, 0.4f, 22),
                MaterialFactory.Solid(new Color(0.05f, 0.05f, 0.07f), 0.3f, 0.9f));
            SceneKit.NeonStrip(null, new Vector3(1.4f, 0.01f, 4), new Vector3(0.06f, 0.02f, 22), FFPalette.NeonPink);
            SceneKit.NeonStrip(null, new Vector3(-1.4f, 0.01f, 4), new Vector3(0.06f, 0.02f, 22), FFPalette.NeonPurple);
            SceneKit.SpotLight(new Vector3(3, 5, -3), new Vector3(0, 1, 0), Color.white, 8f, 35f);
            SceneKit.SpotLight(new Vector3(-3, 5, -3), new Vector3(0, 1, 0), FFPalette.NeonPink, 6f, 40f);

            if (gm.Body == null) gm.Body = AvatarPresets.BodyFor(gm.SelectedPreset);
            var rig = AvatarBuilder.Build(null, gm.SelectedPreset, gm.Body, gm.SelectedFace);
            rig.transform.rotation = Quaternion.Euler(0, 180, 0);
            rig.Equipment.Init(rig, gm.Outfit);
            rig.Equipment.ApplyOutfit(gm.Outfit);
            rig.gameObject.AddComponent<SpinSlow>().DegreesPerSecond = 30f;

            var canvas = UIFactory.CreateCanvas("RunwayCanvas");
            var note = UIFactory.Label(canvas.transform,
                "RUNWAY — full cinematic sequence + judging coming in the next build phase", 24,
                FFPalette.TextDim, TextAnchor.MiddleCenter);
            UIFactory.Place(note.rectTransform, new Vector2(0.5f, 0.92f), new Vector2(1400, 40), Vector2.zero);
            var back = UIFactory.NeonButton(canvas.transform, "RETURN TO STORE",
                () => SceneLoader.Load(SceneLoader.FashionStore), 24, true);
            UIFactory.Place((RectTransform)back.transform, new Vector2(0.5f, 0.08f), new Vector2(380, 64), Vector2.zero);

            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }
    }
}
