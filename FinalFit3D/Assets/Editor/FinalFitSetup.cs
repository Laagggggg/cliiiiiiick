using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace FinalFit.EditorTools
{
    /// <summary>
    /// One-click project setup. Runs automatically on first import (or via
    /// Tools ▸ FinalFit ▸ Setup Project): creates the URP pipeline assets,
    /// switches the project to linear color space, generates the five scenes
    /// with their runtime builders, and registers them in Build Settings.
    /// After it runs once, just open Assets/Scenes/MainMenu.unity and press
    /// Play.
    /// </summary>
    public static class FinalFitSetup
    {
        const string ScenesFolder = "Assets/Scenes";
        const string SettingsFolder = "Assets/Settings";
        const string MarkerScene = ScenesFolder + "/MainMenu.unity";

        [InitializeOnLoadMethod]
        static void AutoSetupOnFirstImport()
        {
            EditorApplication.delayCall += () =>
            {
                if (EditorApplication.isPlayingOrWillChangePlaymode) return;
                if (System.IO.File.Exists(MarkerScene)) return;
                Debug.Log("[FinalFit] First import detected — running project setup…");
                RunSetup();
            };
        }

        [MenuItem("Tools/FinalFit/Setup Project (URP + Scenes)")]
        public static void RunSetup()
        {
            EnsureFolder(ScenesFolder);
            EnsureFolder(SettingsFolder);
            SetupRenderPipeline();
            PlayerSettings.colorSpace = ColorSpace.Linear;

            CreateScene("MainMenu", typeof(MainMenuBuilder));
            CreateScene("CharacterCreator", typeof(CharacterCreatorBuilder));
            CreateScene("FashionStore", typeof(FashionStoreBuilder));
            CreateScene("Runway", typeof(RunwayBuilder));
            CreateScene("Results", typeof(ResultsBuilder));

            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(ScenesFolder + "/MainMenu.unity", true),
                new EditorBuildSettingsScene(ScenesFolder + "/CharacterCreator.unity", true),
                new EditorBuildSettingsScene(ScenesFolder + "/FashionStore.unity", true),
                new EditorBuildSettingsScene(ScenesFolder + "/Runway.unity", true),
                new EditorBuildSettingsScene(ScenesFolder + "/Results.unity", true),
            };

            EditorSceneManager.OpenScene(MarkerScene);
            AssetDatabase.SaveAssets();
            Debug.Log("[FinalFit] Setup complete. Press Play to run the vertical slice. " +
                      "Flow: MainMenu → CharacterCreator → FashionStore.");
        }

        static void SetupRenderPipeline()
        {
            const string rendererPath = SettingsFolder + "/FinalFit_Renderer.asset";
            const string pipelinePath = SettingsFolder + "/FinalFit_URP.asset";

            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(pipelinePath);
            if (pipeline == null)
            {
                var rendererData = ScriptableObject.CreateInstance<UniversalRendererData>();
                AssetDatabase.CreateAsset(rendererData, rendererPath);
                pipeline = UniversalRenderPipelineAsset.Create(rendererData);
                pipeline.supportsHDR = true;
                AssetDatabase.CreateAsset(pipeline, pipelinePath);
            }

            GraphicsSettings.defaultRenderPipeline = pipeline;
            QualitySettings.renderPipeline = pipeline;
        }

        static void CreateScene(string name, System.Type builderType)
        {
            string path = $"{ScenesFolder}/{name}.unity";
            if (System.IO.File.Exists(path)) return;

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var bootstrap = new GameObject("Bootstrap_" + name);
            bootstrap.AddComponent(builderType);
            EditorSceneManager.SaveScene(scene, path);
        }

        static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            var parent = System.IO.Path.GetDirectoryName(path).Replace('\\', '/');
            var leaf = System.IO.Path.GetFileName(path);
            AssetDatabase.CreateFolder(parent, leaf);
        }
    }
}
