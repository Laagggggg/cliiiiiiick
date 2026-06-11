using System.Collections.Generic;
using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Creates URP-safe materials at runtime (falls back to Standard if URP
    /// shaders are unavailable). All placeholder meshes share these so the
    /// whole prototype keeps one coherent look.
    /// </summary>
    public static class MaterialFactory
    {
        static Shader _lit;
        static readonly Dictionary<string, Material> _cache = new Dictionary<string, Material>();

        public static Shader Lit
        {
            get
            {
                if (_lit == null)
                {
                    _lit = Shader.Find("Universal Render Pipeline/Lit");
                    if (_lit == null) _lit = Shader.Find("Standard");
                }
                return _lit;
            }
        }

        public static Material Solid(Color c, float metallic = 0.05f, float smoothness = 0.45f)
        {
            string key = $"s_{c}_{metallic}_{smoothness}";
            if (_cache.TryGetValue(key, out var cached)) return cached;

            var m = new Material(Lit);
            SetColor(m, c);
            if (m.HasProperty("_Metallic")) m.SetFloat("_Metallic", metallic);
            if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", smoothness);
            if (m.HasProperty("_Glossiness")) m.SetFloat("_Glossiness", smoothness);
            _cache[key] = m;
            return m;
        }

        public static Material Chrome(Color tint)
        {
            return Solid(tint, 1f, 0.95f);
        }

        public static Material Emissive(Color c, float intensity = 2.2f)
        {
            string key = $"e_{c}_{intensity}";
            if (_cache.TryGetValue(key, out var cached)) return cached;

            var m = new Material(Lit);
            SetColor(m, c * 0.25f);
            m.EnableKeyword("_EMISSION");
            if (m.HasProperty("_EmissionColor")) m.SetColor("_EmissionColor", c * intensity);
            m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
            _cache[key] = m;
            return m;
        }

        /// <summary>Semi-transparent material for mesh/lace placeholder fabrics.</summary>
        public static Material Sheer(Color c, float alpha = 0.45f)
        {
            var m = new Material(Lit);
            c.a = alpha;
            SetColor(m, c);
            // URP transparent surface setup
            if (m.HasProperty("_Surface")) m.SetFloat("_Surface", 1f);
            if (m.HasProperty("_Blend")) m.SetFloat("_Blend", 0f);
            m.SetOverrideTag("RenderType", "Transparent");
            m.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            if (m.HasProperty("_SrcBlend")) m.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
            if (m.HasProperty("_DstBlend")) m.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            if (m.HasProperty("_ZWrite")) m.SetFloat("_ZWrite", 0f);
            return m;
        }

        static void SetColor(Material m, Color c)
        {
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", c);
            if (m.HasProperty("_Color")) m.SetColor("_Color", c);
        }
    }

    /// <summary>Shared palette for the luxury cyber-anime look.</summary>
    public static class FFPalette
    {
        public static readonly Color NeonPurple = new Color(0.62f, 0.25f, 1f);
        public static readonly Color NeonPink = new Color(1f, 0.30f, 0.72f);
        public static readonly Color NeonCyan = new Color(0.25f, 0.95f, 1f);
        public static readonly Color Gold = new Color(1f, 0.82f, 0.35f);
        public static readonly Color DarkGlass = new Color(0.045f, 0.045f, 0.075f, 0.88f);
        public static readonly Color PanelGlass = new Color(0.08f, 0.07f, 0.13f, 0.92f);
        public static readonly Color FloorDark = new Color(0.07f, 0.07f, 0.09f);
        public static readonly Color WallDark = new Color(0.11f, 0.10f, 0.14f);
        public static readonly Color TextBright = new Color(0.96f, 0.95f, 1f);
        public static readonly Color TextDim = new Color(0.62f, 0.60f, 0.72f);
    }
}
