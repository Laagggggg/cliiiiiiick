namespace FinalFit
{
    /// <summary>
    /// Rule-based judging over clothing tags and item stats — no AI judging.
    /// Phase 2 wiring: theme accuracy, color harmony, silhouette, layering,
    /// accessory balance, originality, risk, overall cohesion.
    /// </summary>
    public static class JudgeScoringSystem
    {
        public struct Result
        {
            public int Total;
            public int ThemeAccuracy, ColorHarmony, Silhouette, Layering;
            public int AccessoryBalance, Originality, Risk, Cohesion;
        }

        public static Result Score(OutfitState outfit, RoundTheme theme)
        {
            // TODO(phase 2): score equipped item tags vs theme Required/Bonus/
            // Penalty tags, count covered slots for layering, compare brands
            // and aesthetics for cohesion, sum item stats for risk/silhouette.
            return new Result();
        }
    }
}
