using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Round timer scaffold for phase 2: 10:00 real rounds, 0:30 debug rounds,
    /// with halfway / one-minute / final-countdown / expired callbacks.
    /// Not yet wired into the store loop.
    /// </summary>
    public class RoundTimer : MonoBehaviour
    {
        public float RoundSeconds = 600f;
        public bool DebugThirtySecondMode = false;
        public System.Action OnHalfway;
        public System.Action OnOneMinute;
        public System.Action OnFinalCountdown;
        public System.Action OnExpired;

        public float Remaining { get; private set; }
        public bool Running { get; private set; }

        public void StartRound()
        {
            Remaining = DebugThirtySecondMode ? 30f : RoundSeconds;
            Running = true;
        }

        void Update()
        {
            if (!Running) return;
            float before = Remaining;
            Remaining -= Time.deltaTime;
            if (before > RoundSeconds * 0.5f && Remaining <= RoundSeconds * 0.5f) OnHalfway?.Invoke();
            if (before > 60f && Remaining <= 60f) OnOneMinute?.Invoke();
            if (before > 10f && Remaining <= 10f) OnFinalCountdown?.Invoke();
            if (Remaining <= 0f)
            {
                Running = false;
                OnExpired?.Invoke();
            }
        }
    }
}
