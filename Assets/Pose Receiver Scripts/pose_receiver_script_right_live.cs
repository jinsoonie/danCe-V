using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;


/// script listens for UDP messages from Python and updates the position of `LeftHandTarget`.
/// The left hand follows `LeftHandTarget` using Animation Rigging (Two Bone IK). Check hierarchy
public class PoseReceiverRightLive : MonoBehaviour
{
    // specifying a public Transform here gives the Pose Receiver (script) that specified field in hierarchy
    public Transform leftHandTarget, rightHandTarget; // For this field in hierarchy, set reference to 'LeftHandTarget', 'RightHandTarget' GameObject
    // this "leftHandTarget" will be a field in character hierarchy, LeftHandTarget (transform) should be assigned to it    public Transform leftHandTarget, rightHandTarget;
    public Transform leftFootTarget, rightFootTarget;
    public Transform headTarget;

    public Transform hipsTarget;  // store the Hips transform
    public Transform avatarHips;  // Assign "mixamorig:Hips" in Unity
    public Transform avatarSpine;   // Assign mixamorig:Spine in Inspector
    public Transform avatarSpine1;  // Assign mixamorig:Spine1 in Inspector
    public Transform avatarSpine2;  // Assign mixamorig:Spine2 in Inspector


    // public Transform leftShoulderTarget, rightShoulderTarget;
    // public Transform spineTarget, hipsTarget, leftElbowTarget, rightElbowTarget;
    // public Transform leftKneeTarget, rightKneeTarget;


    private UdpClient udpClient; // UDP socket to receive data
    private Thread udpReceiveThread; // Background thread for listening to UDP messages
    private PoseData receivedPose = new PoseData();
    private volatile bool _shouldExit = false; // Flag to signal the thread to exit (needed in case ReceiveData() is blocking)

    // Public variables to store score data
    public float overallSimilarity;
    public float leftArm;
    public float rightArm;
    public float leftLeg;
    public float rightLeg;
    public float torso;
    public float head;



    /// Unity Start() method runs once when the scene starts.
    /// init UDP connection.
    void Start()
    {
        // Initialize UDP socket on port 5005 (RIGHT LIVE is 5005)
        udpClient = new UdpClient(5005);
        _shouldExit = false;

        // Start a background thread for receiving UDP data
        udpReceiveThread = new Thread(new ThreadStart(ReceiveData));
        udpReceiveThread.IsBackground = true;
        udpReceiveThread.Start();
    }
    void OnDestroy()
    {
        Debug.Log("Destroyed RIGHT LIVE!!! Cleaning up UDP resources.");
        // Signal the thread to exit
        _shouldExit = true;

        // Close the UDP client. This will cause the blocking Receive() to throw a SocketException.
        if (udpClient != null)
        {
            udpClient.Close();
            udpClient = null;
        }

        // Wait for the receiving thread to finish
        if (udpReceiveThread != null)
        {
            // Wait up to 1 second for the thread to exit gracefully
            udpReceiveThread.Join(1000);
            udpReceiveThread = null;
        }
    }

    // convert mediapipe xyz to unity world coords
    Vector3 ConvertMediaPipeToUnity(Vector3 landmark, bool isFoot = false, float baseDepth = 0.0f)
    {
        Camera mainCamera = Camera.main;

        // // Convert the mediapipe Z value into a positive distance from the camera.
        // // Since mediapipe Z is negative for objects in front of the camera,
        // // Use -landmark.z and then scale it. add the nearClipPlane to ensure
        // // the computed distance is always in front of the camera.
        // float distanceFromCamera = mainCamera.nearClipPlane + (-landmark.z * depthScale);

        // // Convert the viewport coordinates to a world position.
        // return mainCamera.ViewportToWorldPoint(new Vector3(viewportX, viewportY, distanceFromCamera));

        // Convert MediaPipe (0,1) coordinate system to Unity's world space
        float viewportX = landmark.x;          // MediaPipe X is normalized [0,1]
        float viewportY = 1.0f - landmark.y;   // Flip Y for Unity (0,0 at bottom-left)

        // Use different depth parameters for feet.
        // For foot landmarks, use a larger base depth and stronger multiplier so target moves further away
        float depthMultiplier = isFoot ? 1.0f : 0.85f;
        float effectiveBaseDepth = isFoot ? 0.5f : baseDepth;

        // Compute Depth (MediaPipe Z is relative, so map it to a useful depth of 0 bc avatar at 0,0,0)
        float unityZ = effectiveBaseDepth + (-landmark.z * depthMultiplier); // Convert negative depth (1.7/2 = 0.85)

        // Apply scaling factors
        float unityX = -(viewportX - 0.5f) * 3.4f;  // Scale X to match shoulder width (1.7m/2) 0.85 = 1.0f
        float unityY = (viewportY - 0.5f) * 2.5f;     // Scale Y to match avatar height (1.7m) = 3.0f


        return new Vector3(unityX, unityY, unityZ);
    }


    /// Continuously listens for UDP messages and updates the received position.
    /// Runs on a separate thread.
    void ReceiveData()
    {
        IPEndPoint remoteEP = new IPEndPoint(IPAddress.Any, 5005);

        while (!_shouldExit)
        {
            try
            {
                // Receive UDP packet
                byte[] data = udpClient.Receive(ref remoteEP);
                string json = Encoding.UTF8.GetString(data);

                // // inserted for testing/printing json message (contains testmsg + 3 floats?)
                // Debug.Log("Right_Live Received JSON: " + json);

                // // Convert JSON string to PoseData object (parse)
                // PoseData tempPose = JsonUtility.FromJson<PoseData>(json);

                // NEW WAY OF RECEIVING (based on danny pose_sender)
                // Debug.Log("Received Combined JSON: " + json);

                // Deserialize into CombinedData
                CombinedData combined = JsonUtility.FromJson<CombinedData>(json);

                // Extract "comparison"
                // Check for null at each level before accessing nested fields
                if (combined != null &&
                    combined.comparison != null &&
                    combined.comparison.joint_scores != null &&
                    combined.comparison.joint_scores.groups != null)
                {
                    // Safeguard against null arms and legs
                    if (combined.comparison.joint_scores.groups.arms == null)
                    {
                        combined.comparison.joint_scores.groups.arms = new LimbScore { left = 0, right = 0 };
                    }
                    if (combined.comparison.joint_scores.groups.legs == null)
                    {
                        combined.comparison.joint_scores.groups.legs = new LimbScore { left = 0, right = 0 };
                    }

                    // Directly assign the values to the public variables in this script.
                    overallSimilarity = combined.comparison.overall_similarity;
                    leftArm = (combined.comparison.joint_scores.groups.arms != null) ? combined.comparison.joint_scores.groups.arms.left : 0f;
                    rightArm = (combined.comparison.joint_scores.groups.arms != null) ? combined.comparison.joint_scores.groups.arms.right : 0f;
                    leftLeg = (combined.comparison.joint_scores.groups.legs != null) ? combined.comparison.joint_scores.groups.legs.left : 0f;
                    rightLeg = (combined.comparison.joint_scores.groups.legs != null) ? combined.comparison.joint_scores.groups.legs.right : 0f;
                    torso = combined.comparison.joint_scores.groups.torso;
                    head = combined.comparison.joint_scores.groups.head;
                }
                // else
                // {
                //     Debug.LogWarning("Comparison data or one of its nested components is null.");
                // }

                // Extract "pose"
                PoseData tempPose = combined.pose;

                receivedPose.LEFT_WRIST = tempPose.LEFT_WRIST;
                receivedPose.RIGHT_WRIST = tempPose.RIGHT_WRIST;
                receivedPose.LEFT_ANKLE = tempPose.LEFT_ANKLE;
                receivedPose.RIGHT_ANKLE = tempPose.RIGHT_ANKLE;
                receivedPose.NOSE = tempPose.NOSE;

                receivedPose.LEFT_HIP = tempPose.LEFT_HIP;
                receivedPose.RIGHT_HIP = tempPose.RIGHT_HIP;

                receivedPose.LEFT_SHOULDER = tempPose.LEFT_SHOULDER;
                receivedPose.RIGHT_SHOULDER = tempPose.RIGHT_SHOULDER;

                receivedPose.LEFT_ELBOW = tempPose.LEFT_ELBOW;
                receivedPose.RIGHT_ELBOW = tempPose.RIGHT_ELBOW;
            }
            catch (SocketException e)
            {
                Debug.LogError("Socket Exception: " + e.Message);
            }
        }
    }

    /// Updates `LeftHandTarget` position smoothly based on received UDP data.
    /// Runs every frame.
    // LateUpdate
    void LateUpdate()
    {

        // Define the direct offset for the live webcam avatar
        Vector3 offset = new Vector3(-1.5f, 0, 0);

        // === 1. Move Hips Target ===
        Vector3 leftHipPos = ConvertMediaPipeToUnity(receivedPose.LEFT_HIP) + offset;
        Vector3 rightHipPos = ConvertMediaPipeToUnity(receivedPose.RIGHT_HIP) + offset;
        Vector3 midHip = (leftHipPos + rightHipPos) * 0.5f;

        hipsTarget.position = Vector3.Lerp(hipsTarget.position, midHip, Time.deltaTime * 5);
        avatarHips.position = Vector3.Lerp(avatarHips.position, hipsTarget.position, Time.deltaTime * 5);

        // Compute stable hip rotation
        Vector3 hipDirection = (rightHipPos - leftHipPos).normalized; // Sideways direction, i.e. XZ axis vector
        Vector3 forwardDirection = -Vector3.Cross(Vector3.up, hipDirection).normalized; // Compute correct forward direction (face positive Z axis)
        Quaternion hipRotation = Quaternion.identity; // Default rotation to prevent error
        if (forwardDirection != Vector3.zero)
        {
            hipRotation = Quaternion.LookRotation(forwardDirection, Vector3.up);
        }

        // Blend hips rotation more aggressively
        float hipBlendFactor = 0.9f; // Increase influence of manual rotation
        avatarHips.rotation = Quaternion.Slerp(avatarHips.rotation, hipRotation, hipBlendFactor);

        // === 2. Compute torso rotation **relative** to the hip's rotation ===
        Vector3 leftShoulderPos = ConvertMediaPipeToUnity(receivedPose.LEFT_SHOULDER) + offset;
        Vector3 rightShoulderPos = ConvertMediaPipeToUnity(receivedPose.RIGHT_SHOULDER) + offset;
        Vector3 torsoDirection = (rightShoulderPos - leftShoulderPos).normalized;
        Quaternion torsoRotation = Quaternion.identity; // Default rotation to prevent error
        if (forwardDirection != Vector3.zero)
        {
            torsoRotation = Quaternion.LookRotation(forwardDirection, Vector3.up);
        }

        // Blend between IK-controlled rotation and computed torso rotation
        float torsoBlendFactor = 0.9f; // Adjust between 0 (IK dominant) and 1 (fully manual rotation)
        avatarSpine.rotation = Quaternion.Slerp(avatarSpine.rotation, torsoRotation, torsoBlendFactor);
        avatarSpine1.rotation = Quaternion.Slerp(avatarSpine1.rotation, torsoRotation, torsoBlendFactor);
        avatarSpine2.rotation = Quaternion.Slerp(avatarSpine2.rotation, torsoRotation, torsoBlendFactor);

        // === 3. Move IK Targets ===
        leftHandTarget.position = Vector3.MoveTowards(leftHandTarget.position, ConvertMediaPipeToUnity(receivedPose.LEFT_WRIST) + offset, Time.deltaTime * 5);
        rightHandTarget.position = Vector3.MoveTowards(rightHandTarget.position, ConvertMediaPipeToUnity(receivedPose.RIGHT_WRIST) + offset, Time.deltaTime * 5);
        leftFootTarget.position = Vector3.MoveTowards(leftFootTarget.position, ConvertMediaPipeToUnity(receivedPose.LEFT_ANKLE, isFoot: true) + offset, Time.deltaTime * 5);
        rightFootTarget.position = Vector3.MoveTowards(rightFootTarget.position, ConvertMediaPipeToUnity(receivedPose.RIGHT_ANKLE, isFoot: true) + offset, Time.deltaTime * 5);
        headTarget.position = Vector3.MoveTowards(headTarget.position, ConvertMediaPipeToUnity(receivedPose.NOSE) + offset, Time.deltaTime * 5);

        // === 4. Set Hand & Foot Rotation (Important for IK) ===
        Vector3 leftElbowPos = ConvertMediaPipeToUnity(receivedPose.LEFT_ELBOW) + offset;
        Vector3 leftWristPos = ConvertMediaPipeToUnity(receivedPose.LEFT_WRIST) + offset;
        Vector3 leftForearmDir = (leftWristPos - leftElbowPos).normalized;
        leftHandTarget.rotation = Quaternion.identity; // Default rotation to prevent error
        if (leftForearmDir != Vector3.zero)
        {
            leftHandTarget.rotation = Quaternion.LookRotation(leftForearmDir, Vector3.up);
        }

        Vector3 rightElbowPos = ConvertMediaPipeToUnity(receivedPose.RIGHT_ELBOW) + offset;
        Vector3 rightWristPos = ConvertMediaPipeToUnity(receivedPose.RIGHT_WRIST) + offset;
        Vector3 rightForearmDir = (rightWristPos - rightElbowPos).normalized;
        rightHandTarget.rotation = Quaternion.identity; // Default rotation to prevent error
        if (rightForearmDir != Vector3.zero)
        {
            rightHandTarget.rotation = Quaternion.LookRotation(rightForearmDir, Vector3.up);
        }
    }


    /// Cleans up UDP thread when Unity application closes.
    private void OnApplicationQuit()
    {
        udpReceiveThread.Abort(); // Stop the background thread
        udpClient.Close(); // Close the UDP connection
    }

    /// Data structure for receiving pose data from Python. Need to add multiple bones/joints data now
    [System.Serializable]
    public class PoseData
    {
        // public Vector3 leftHand, rightHand, leftFoot, rightFoot;
        public Vector3 LEFT_WRIST, RIGHT_WRIST, LEFT_ANKLE, RIGHT_ANKLE, NOSE;

        public Vector3 LEFT_HIP, RIGHT_HIP; // used for computing root of avatar

        public Vector3 LEFT_SHOULDER, RIGHT_SHOULDER;

        // left_elbow, right_elbow for direction in lateUpdate
        public Vector3 LEFT_ELBOW, RIGHT_ELBOW;
    }

    // added for danny's updated pose_sender json
    [System.Serializable]
    public class CombinedData
    {
        public PoseData pose;
        public ComparisonData comparison; // the actual feedback to be shown on Unity UI
    }

    // Represents the comparison portion of the JSON (The way danny has packaged ComaprisonData)
    [System.Serializable]
    public class ComparisonData
    {
        public float overall_similarity;
        public JointScores joint_scores; // Contains both individual scores and group scores.
    }

    // Represents joint scores, which include both individual parts and grouped parts.
    [System.Serializable]
    public class JointScores
    {
        public GroupScores groups;
    }

    // Represents the grouped scores for different parts of the body.
    [System.Serializable]
    public class GroupScores
    {
        public LimbScore arms;   // arms has two sub-scores: left and right
        public LimbScore legs;   // legs has two sub-scores: left and right
        public float torso;
        public float head;
    }

    // Represents the score for limbs which has a left and right component.
    [System.Serializable]
    public class LimbScore
    {
        public float left;
        public float right;
    }
}
