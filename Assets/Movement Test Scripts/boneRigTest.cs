using UnityEngine;

public class boneRigTest : MonoBehaviour
{
    public Animator maleAvatarAnimator;  // Assign in Inspector

    // Start is called once before the first execution of Update after MonoBehaviour is created
    void Start()
    {
        // // Test #1: Move the Left Arm Up
        // Transform leftUpperArm = maleAvatarAnimator.GetBoneTransform(HumanBodyBones.LeftUpperArm);
        // if (leftUpperArm != null)
        // {
        //     leftUpperArm.rotation *= Quaternion.Euler(45, 0, 0);  // x/y/z where y is up/down, x is left/right, z is in/out
        // }

        // // Test #2: Bend Right Leg
        // Transform rightLowerLeg = maleAvatarAnimator.GetBoneTransform(HumanBodyBones.RightLowerLeg);
        // if (rightLowerLeg != null)
        // {
        //     rightLowerLeg.rotation *= Quaternion.Euler(-90, 0, 0);  // Bend knee
        // }
    }

    // assign/drag the LeftHandTarget GameObject here (in the Inspector)
    // where LeftHandTarget is 
    public Transform leftHandTarget;

    public Transform rightHandTarget;

    // Update is called once per frame
    void Update()
    {
        // Transform leftUpperArm = maleAvatarAnimator.GetBoneTransform(HumanBodyBones.LeftUpperArm);
        // if (leftUpperArm != null)
        // {
        //     leftUpperArm.rotation *= Quaternion.Euler(0, 0, 1);  // Slowly rotates over time
        // }
        // int receivedX = 100;
        // int receivedY = 50;
        // int receivedZ = 4;

        // // Assume we're receiving position from Python
        // Vector3 newLeftHandPosition = new Vector3(receivedX, receivedY, receivedZ);

        // // Apply the position (smoothed for natural movement)
        // leftHandTarget.position = Vector3.Lerp(leftHandTarget.position, newLeftHandPosition, Time.deltaTime * 5);
    }
}
