using UnityEngine.SceneManagement;

namespace FinalFit
{
    public static class SceneLoader
    {
        public const string MainMenu = "MainMenu";
        public const string CharacterCreator = "CharacterCreator";
        public const string FashionStore = "FashionStore";
        public const string Runway = "Runway";
        public const string Results = "Results";

        public static void Load(string sceneName)
        {
            SceneManager.LoadScene(sceneName);
        }
    }
}
