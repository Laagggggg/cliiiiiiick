using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// WASD third-person movement with gravity, camera-relative steering and
    /// smooth turn-to-face. Movement is suspended while store UI is open.
    /// </summary>
    [RequireComponent(typeof(CharacterController))]
    public class ThirdPersonController : MonoBehaviour
    {
        public float WalkSpeed = 3.2f;
        public float SprintSpeed = 5.6f;
        public float TurnSmoothing = 12f;
        public Transform CameraTransform;
        public SimpleWalkAnimator WalkAnimator;

        [HideInInspector] public bool InputLocked;

        CharacterController _cc;
        float _verticalVel;

        void Awake() { _cc = GetComponent<CharacterController>(); }

        void Update()
        {
            Vector3 move = Vector3.zero;
            float speedNorm = 0f;

            if (!InputLocked)
            {
                float h = Input.GetAxisRaw("Horizontal");
                float v = Input.GetAxisRaw("Vertical");
                Vector3 input = new Vector3(h, 0, v);
                if (input.sqrMagnitude > 1f) input.Normalize();

                if (input.sqrMagnitude > 0.01f && CameraTransform != null)
                {
                    Vector3 fwd = CameraTransform.forward; fwd.y = 0; fwd.Normalize();
                    Vector3 right = CameraTransform.right; right.y = 0; right.Normalize();
                    Vector3 dir = fwd * input.z + right * input.x;

                    bool sprint = Input.GetKey(KeyCode.LeftShift);
                    float speed = sprint ? SprintSpeed : WalkSpeed;
                    move = dir * speed;
                    speedNorm = sprint ? 1f : 0.65f;

                    Quaternion target = Quaternion.LookRotation(dir);
                    transform.rotation = Quaternion.Slerp(transform.rotation, target,
                        Time.deltaTime * TurnSmoothing);
                }
            }

            if (_cc.isGrounded) _verticalVel = -1f;
            else _verticalVel -= 18f * Time.deltaTime;
            move.y = _verticalVel;

            _cc.Move(move * Time.deltaTime);

            if (WalkAnimator != null) WalkAnimator.Speed = speedNorm;
        }
    }
}
