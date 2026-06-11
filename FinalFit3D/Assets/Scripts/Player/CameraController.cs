using UnityEngine;

namespace FinalFit
{
    /// <summary>
    /// Mouse-orbit follow camera. Cursor is locked while shopping; StoreUI
    /// releases it (and sets InputLocked) when a browse panel opens.
    /// </summary>
    public class CameraController : MonoBehaviour
    {
        public Transform Target;
        public float Distance = 3.6f;
        public float Height = 1.55f;
        public float Sensitivity = 3f;
        public float MinPitch = -25f;
        public float MaxPitch = 65f;

        [HideInInspector] public bool InputLocked;

        float _yaw;
        float _pitch = 14f;

        public void SnapBehind(Transform target)
        {
            Target = target;
            _yaw = target.eulerAngles.y;
            LateUpdate();
        }

        void LateUpdate()
        {
            if (Target == null) return;

            if (!InputLocked)
            {
                _yaw += Input.GetAxis("Mouse X") * Sensitivity;
                _pitch -= Input.GetAxis("Mouse Y") * Sensitivity;
                _pitch = Mathf.Clamp(_pitch, MinPitch, MaxPitch);
            }

            Vector3 pivot = Target.position + Vector3.up * Height;
            Quaternion rot = Quaternion.Euler(_pitch, _yaw, 0);
            Vector3 desired = pivot - rot * Vector3.forward * Distance;

            // keep the camera off the floor
            if (desired.y < 0.25f) desired.y = 0.25f;

            transform.position = desired;
            transform.rotation = Quaternion.LookRotation(pivot - transform.position);
        }
    }
}
