using UnityEngine;

namespace FinalFit
{
    public enum AvatarPresetType
    {
        FemaleCurvyAnime,
        FemaleTallRunway,
        FemaleStreetwear,
        MaleLeanModel,
        MaleMuscularHero,
        MaleStreetwear,
        AndroHighFashion
    }

    public enum FacePresetType
    {
        SoftAnime,
        SharpModel,
        SeriousVillain,
        CuteStreetwear,
        ElegantRunway,
        MasculineSharp,
        MasculineSoft,
        AndroEditorial
    }

    /// <summary>
    /// All body slider values. Uses plain multipliers (1 = preset neutral) so
    /// the prototype's transform scaling can later be swapped for blendshapes
    /// on real rigged anime models without changing calling code.
    /// </summary>
    [System.Serializable]
    public class BodyConfig
    {
        public float height = 1f;
        public float headSize = 1f;
        public float shoulderWidth = 1f;
        public float chest = 1f;
        public float waist = 1f;
        public float hips = 1f;
        public float armThickness = 1f;
        public float legLength = 1f;
        public float thighThickness = 1f;
        public float calfThickness = 1f;
        public float glute = 1f;
        public float muscle = 1f;
        public float bodyScale = 1f;
        public float posture = 0f;   // -1 slouch .. +1 upright/model
        public float handSize = 1f;
        public float footSize = 1f;

        public static BodyConfig Default() => new BodyConfig();

        public BodyConfig Clone() => (BodyConfig)MemberwiseClone();
    }

    /// <summary>Static data for the seven launch presets.</summary>
    public static class AvatarPresets
    {
        public static string DisplayName(AvatarPresetType t)
        {
            switch (t)
            {
                case AvatarPresetType.FemaleCurvyAnime: return "Female · Curvy Anime";
                case AvatarPresetType.FemaleTallRunway: return "Female · Tall Runway";
                case AvatarPresetType.FemaleStreetwear: return "Female · Streetwear";
                case AvatarPresetType.MaleLeanModel: return "Male · Lean Model";
                case AvatarPresetType.MaleMuscularHero: return "Male · Anime Hero";
                case AvatarPresetType.MaleStreetwear: return "Male · Streetwear";
                default: return "Androgynous · High Fashion";
            }
        }

        public static bool IsFeminine(AvatarPresetType t)
        {
            return t == AvatarPresetType.FemaleCurvyAnime
                || t == AvatarPresetType.FemaleTallRunway
                || t == AvatarPresetType.FemaleStreetwear;
        }

        public static BodyConfig BodyFor(AvatarPresetType t)
        {
            var c = BodyConfig.Default();
            switch (t)
            {
                case AvatarPresetType.FemaleCurvyAnime:
                    c.shoulderWidth = 0.86f; c.chest = 1.35f; c.waist = 0.74f;
                    c.hips = 1.30f; c.thighThickness = 1.25f; c.glute = 1.35f;
                    c.legLength = 1.02f; c.posture = 0.4f;
                    break;
                case AvatarPresetType.FemaleTallRunway:
                    c.height = 1.08f; c.legLength = 1.12f; c.shoulderWidth = 0.92f;
                    c.chest = 1.05f; c.waist = 0.72f; c.hips = 1.05f;
                    c.thighThickness = 0.9f; c.calfThickness = 0.9f; c.posture = 0.8f;
                    break;
                case AvatarPresetType.FemaleStreetwear:
                    c.shoulderWidth = 0.9f; c.chest = 1.12f; c.waist = 0.82f;
                    c.hips = 1.15f; c.thighThickness = 1.1f; c.glute = 1.15f;
                    c.posture = -0.1f;
                    break;
                case AvatarPresetType.MaleLeanModel:
                    c.height = 1.05f; c.shoulderWidth = 1.12f; c.chest = 0.95f;
                    c.waist = 0.85f; c.hips = 0.88f; c.legLength = 1.08f;
                    c.muscle = 0.95f; c.posture = 0.6f;
                    break;
                case AvatarPresetType.MaleMuscularHero:
                    c.height = 1.07f; c.shoulderWidth = 1.35f; c.chest = 1.2f;
                    c.waist = 0.92f; c.hips = 0.95f; c.armThickness = 1.35f;
                    c.thighThickness = 1.2f; c.calfThickness = 1.15f;
                    c.muscle = 1.5f; c.posture = 0.7f;
                    break;
                case AvatarPresetType.MaleStreetwear:
                    c.shoulderWidth = 1.15f; c.chest = 1.02f; c.waist = 0.95f;
                    c.hips = 0.92f; c.armThickness = 1.1f; c.muscle = 1.1f;
                    c.posture = -0.3f;
                    break;
                case AvatarPresetType.AndroHighFashion:
                    c.height = 1.06f; c.shoulderWidth = 1.0f; c.chest = 0.95f;
                    c.waist = 0.78f; c.hips = 0.98f; c.legLength = 1.1f;
                    c.posture = 0.9f;
                    break;
            }
            return c;
        }

        static readonly Color[] SkinTones =
        {
            new Color(0.98f, 0.86f, 0.76f),
            new Color(0.93f, 0.76f, 0.62f),
            new Color(0.80f, 0.60f, 0.45f),
            new Color(0.62f, 0.44f, 0.32f),
            new Color(0.45f, 0.31f, 0.23f)
        };

        public static Color SkinTone(int index)
        {
            return SkinTones[Mathf.Clamp(index, 0, SkinTones.Length - 1)];
        }

        public static int SkinToneCount => SkinTones.Length;

        public static FacePresetType DefaultFace(AvatarPresetType t)
        {
            switch (t)
            {
                case AvatarPresetType.FemaleCurvyAnime: return FacePresetType.SoftAnime;
                case AvatarPresetType.FemaleTallRunway: return FacePresetType.ElegantRunway;
                case AvatarPresetType.FemaleStreetwear: return FacePresetType.CuteStreetwear;
                case AvatarPresetType.MaleLeanModel: return FacePresetType.SharpModel;
                case AvatarPresetType.MaleMuscularHero: return FacePresetType.MasculineSharp;
                case AvatarPresetType.MaleStreetwear: return FacePresetType.MasculineSoft;
                default: return FacePresetType.AndroEditorial;
            }
        }

        public static string DefaultHairId(AvatarPresetType t)
        {
            switch (t)
            {
                case AvatarPresetType.FemaleCurvyAnime: return "hair_bob";
                case AvatarPresetType.FemaleTallRunway: return "hair_long";
                case AvatarPresetType.FemaleStreetwear: return "hair_twintails";
                case AvatarPresetType.MaleLeanModel: return "hair_slick";
                case AvatarPresetType.MaleMuscularHero: return "hair_spiky";
                case AvatarPresetType.MaleStreetwear: return "hair_wolf";
                default: return "hair_ponytail";
            }
        }
    }

    public static class FacePresets
    {
        public static string DisplayName(FacePresetType t)
        {
            switch (t)
            {
                case FacePresetType.SoftAnime: return "Soft Anime";
                case FacePresetType.SharpModel: return "Sharp Model";
                case FacePresetType.SeriousVillain: return "Serious Villain";
                case FacePresetType.CuteStreetwear: return "Cute Streetwear";
                case FacePresetType.ElegantRunway: return "Elegant Runway";
                case FacePresetType.MasculineSharp: return "Masculine Sharp";
                case FacePresetType.MasculineSoft: return "Masculine Soft";
                default: return "Andro Editorial";
            }
        }

        // eyeScale, browAngleDeg (positive = fierce), irisColor, hasLips
        public static void Get(FacePresetType t, out float eyeScale, out float browAngle,
            out Color iris, out bool lips)
        {
            switch (t)
            {
                case FacePresetType.SoftAnime:
                    eyeScale = 1.3f; browAngle = -4f; iris = new Color(0.35f, 0.65f, 0.95f); lips = true; break;
                case FacePresetType.SharpModel:
                    eyeScale = 0.95f; browAngle = 10f; iris = new Color(0.45f, 0.40f, 0.35f); lips = false; break;
                case FacePresetType.SeriousVillain:
                    eyeScale = 0.85f; browAngle = 18f; iris = new Color(0.75f, 0.15f, 0.25f); lips = false; break;
                case FacePresetType.CuteStreetwear:
                    eyeScale = 1.25f; browAngle = -2f; iris = new Color(0.55f, 0.40f, 0.85f); lips = true; break;
                case FacePresetType.ElegantRunway:
                    eyeScale = 1.1f; browAngle = 6f; iris = new Color(0.30f, 0.55f, 0.50f); lips = true; break;
                case FacePresetType.MasculineSharp:
                    eyeScale = 0.8f; browAngle = 14f; iris = new Color(0.35f, 0.35f, 0.40f); lips = false; break;
                case FacePresetType.MasculineSoft:
                    eyeScale = 0.95f; browAngle = 2f; iris = new Color(0.40f, 0.30f, 0.20f); lips = false; break;
                default: // AndroEditorial
                    eyeScale = 1.1f; browAngle = 8f; iris = new Color(0.80f, 0.70f, 0.30f); lips = true; break;
            }
        }
    }
}
