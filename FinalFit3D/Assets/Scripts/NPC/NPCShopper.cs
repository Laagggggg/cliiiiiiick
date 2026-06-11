using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Ambient shopper AI: drifts between browse points around the store,
    /// lingers at racks as if judging the inventory, then moves on. Keeps the
    /// store feeling alive without any navmesh dependency.
    /// </summary>
    public class NPCShopper : MonoBehaviour
    {
        public Vector2 RoamMin = new Vector2(-14, -10);
        public Vector2 RoamMax = new Vector2(14, 10);
        public float Speed = 1.6f;

        SimpleWalkAnimator _anim;
        Vector3 _target;
        float _pauseUntil;
        float _bored;

        public void Init(SimpleWalkAnimator anim, Vector2 roamMin, Vector2 roamMax)
        {
            _anim = anim;
            RoamMin = roamMin;
            RoamMax = roamMax;
            Speed = Random.Range(1.2f, 2.1f);
            PickTarget();
            _pauseUntil = Time.time + Random.Range(0f, 3f);
        }

        void PickTarget()
        {
            _target = new Vector3(
                Random.Range(RoamMin.x, RoamMax.x), 0,
                Random.Range(RoamMin.y, RoamMax.y));
            _bored = Time.time + Random.Range(8f, 14f); // give up if blocked
        }

        void Update()
        {
            if (Time.time < _pauseUntil)
            {
                if (_anim != null) _anim.Speed = 0f;
                return;
            }

            Vector3 pos = transform.position;
            Vector3 to = _target - pos; to.y = 0;

            if (to.magnitude < 0.35f || Time.time > _bored)
            {
                _pauseUntil = Time.time + Random.Range(1.5f, 5f); // "browse" the rack
                PickTarget();
                if (_anim != null) _anim.Speed = 0f;
                return;
            }

            Vector3 dir = to.normalized;
            transform.position = pos + dir * Speed * Time.deltaTime;
            transform.rotation = Quaternion.Slerp(transform.rotation,
                Quaternion.LookRotation(dir), Time.deltaTime * 6f);
            if (_anim != null) _anim.Speed = 0.55f;
        }
    }
}
