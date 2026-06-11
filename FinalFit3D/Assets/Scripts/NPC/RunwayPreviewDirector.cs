using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Drives the in-store runway preview show: an NPC model struts down the
    /// catwalk on a loop, spins at the end, and the three judges raise score
    /// paddles. Pure ambience for now — the real judging system arrives with
    /// the Runway scene phase.
    /// </summary>
    public class RunwayPreviewDirector : MonoBehaviour
    {
        public Transform Model;                 // NPC avatar root walking the runway
        public SimpleWalkAnimator ModelAnim;
        public Vector3 RunwayStart;
        public Vector3 RunwayEnd;
        public TextMesh[] JudgePaddles = new TextMesh[0];

        enum Phase { WalkOut, Pose, WalkBack, Reset }
        Phase _phase = Phase.WalkOut;
        float _phaseTime;
        float _poseSpin;

        void Update()
        {
            if (Model == null) return;
            _phaseTime += Time.deltaTime;

            switch (_phase)
            {
                case Phase.WalkOut:
                    if (MoveTowards(RunwayEnd, 1.5f)) Next(Phase.Pose);
                    break;

                case Phase.Pose:
                    if (ModelAnim != null) ModelAnim.Speed = 0f;
                    _poseSpin += Time.deltaTime * 120f;
                    Model.rotation = Quaternion.Euler(0, _poseSpin, 0);
                    if (_phaseTime > 3f)
                    {
                        RevealScores();
                        Next(Phase.WalkBack);
                    }
                    break;

                case Phase.WalkBack:
                    if (MoveTowards(RunwayStart, 1.8f)) Next(Phase.Reset);
                    break;

                case Phase.Reset:
                    if (ModelAnim != null) ModelAnim.Speed = 0f;
                    if (_phaseTime > 2.5f)
                    {
                        ClearScores();
                        Next(Phase.WalkOut);
                    }
                    break;
            }
        }

        bool MoveTowards(Vector3 target, float speed)
        {
            Vector3 to = target - Model.position; to.y = 0;
            if (to.magnitude < 0.15f) return true;
            Vector3 dir = to.normalized;
            Model.position += dir * speed * Time.deltaTime;
            Model.rotation = Quaternion.Slerp(Model.rotation,
                Quaternion.LookRotation(dir), Time.deltaTime * 8f);
            if (ModelAnim != null) ModelAnim.Speed = 0.7f;
            return false;
        }

        void Next(Phase p) { _phase = p; _phaseTime = 0f; _poseSpin = Model.eulerAngles.y; }

        void RevealScores()
        {
            foreach (var paddle in JudgePaddles)
                if (paddle != null)
                    paddle.text = (Random.Range(70, 100) / 10f).ToString("0.0");
        }

        void ClearScores()
        {
            foreach (var paddle in JudgePaddles)
                if (paddle != null) paddle.text = "—";
        }
    }
}
