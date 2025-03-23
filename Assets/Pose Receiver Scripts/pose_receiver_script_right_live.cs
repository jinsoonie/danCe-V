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

    /// Unity Start() method runs once when the scene starts.
    /// init UDP connection.
    void Start()
    {
        // Initialize UDP socket on port 5005 (RIGHT LIVE is 5005)
        udpClient = new UdpClient(5005);

        // Start a background thread for receiving UDP data
        udpReceiveThread = new Thread(new ThreadStart(ReceiveData));
        udpReceiveThread.IsBackground = true;
        udpReceiveThread.Start();
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

        while (true)
        {
            try
            {
                // Receive UDP packet
                byte[] data = udpClient.Receive(ref remoteEP);
                string json = Encoding.UTF8.GetString(data);

                // inserted for testing/printing json message (contains testmsg + 3 floats?)
                Debug.Log("Received JSON: " + json);

                // Convert JSON string to PoseData object (parse)
                PoseData tempPose = JsonUtility.FromJson<PoseData>(json);

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
    // void Update()
    // {
    //     // root of avatar, midhip
    //     // Compute MID_HIP dynamically as the midpoint of LEFT_HIP and RIGHT_HIP
    //     Vector3 leftHipPos = ConvertMediaPipeToUnity(receivedPose.LEFT_HIP);
    //     Vector3 rightHipPos = ConvertMediaPipeToUnity(receivedPose.RIGHT_HIP);
    //     Vector3 midHip = (leftHipPos + rightHipPos) / 2;
    //     Debug.Log("LEFT HIP: " + leftHipPos);
    //     Debug.Log("RIGHT HIP: " + rightHipPos);

    //     // Set avatar's root position to MID_HIP
    //     hipsTarget.position = Vector3.Lerp(hipsTarget.position, midHip, Time.deltaTime * 5);
    //     Debug.Log("Hips Target: " + hipsTarget.position);

    //     // shift `avatarHips` to match `hipsTarget`
    //     avatarHips.position = Vector3.Lerp(avatarHips.position, hipsTarget.position, Time.deltaTime * 5);

    //     // // --- Compute Hips Rotation ---
    //     Vector3 hipDirection = (rightHipPos - leftHipPos).normalized;  // Direction vector from left hip to right hip
    //     Quaternion mixamoOffset = Quaternion.Euler(0, -90, 0);  // Adjust for Mixamo's default orientation
    //     //v1
    //     // Vector3 forwardDirection = Vector3.Cross(hipDirection, Vector3.up);
    //     // Quaternion hipRotation = Quaternion.LookRotation(forwardDirection, Vector3.up);
    //     //v2
    //     Quaternion hipRotation = Quaternion.LookRotation(hipDirection, Vector3.up) * mixamoOffset;
    //     avatarHips.rotation = Quaternion.Slerp(avatarHips.rotation, hipRotation, Time.deltaTime * 10);


    //     // FOR SHOULDERS
    //     // --- Compute Torso Rotation ---
    //     Vector3 leftShoulderPos = ConvertMediaPipeToUnity(receivedPose.LEFT_SHOULDER);
    //     Vector3 rightShoulderPos = ConvertMediaPipeToUnity(receivedPose.RIGHT_SHOULDER);

    //     // Compute torso direction using shoulders
    //     Vector3 torsoDirection = (rightShoulderPos - leftShoulderPos).normalized;
    //     Quaternion torsoRotation = Quaternion.LookRotation(torsoDirection, Vector3.up);

    //     Quaternion blendedTorsoRotation = Quaternion.Slerp(avatarSpine.rotation, torsoRotation, Time.deltaTime * 5);
    //     avatarSpine.rotation = blendedTorsoRotation;
    //     avatarSpine1.rotation = Quaternion.Slerp(avatarSpine1.rotation, blendedTorsoRotation, Time.deltaTime * 3);
    //     avatarSpine2.rotation = Quaternion.Slerp(avatarSpine2.rotation, blendedTorsoRotation, Time.deltaTime * 2);


    //     ////// RIGHT NOW THE receivedPose.LEFT_WRIST/LEFT_HIP/RIGHT_HIP's scaled ver is being used, but is this right?

    //     // Smooth movement to avoid sudden jumps
    //     leftHandTarget.position = Vector3.Lerp(leftHandTarget.position, ConvertMediaPipeToUnity(receivedPose.LEFT_WRIST), Time.deltaTime * 5);
    //     // add more body parts here..
    //     rightHandTarget.position = Vector3.Lerp(rightHandTarget.position, ConvertMediaPipeToUnity(receivedPose.RIGHT_WRIST), Time.deltaTime * 5);

    //     leftFootTarget.position = Vector3.Lerp(leftFootTarget.position, ConvertMediaPipeToUnity(receivedPose.LEFT_ANKLE), Time.deltaTime * 5);
    //     rightFootTarget.position = Vector3.Lerp(rightFootTarget.position, ConvertMediaPipeToUnity(receivedPose.RIGHT_ANKLE), Time.deltaTime * 5);

    //     headTarget.position = Vector3.Lerp(headTarget.position, ConvertMediaPipeToUnity(receivedPose.NOSE), Time.deltaTime * 5);

    //     // Debug.Log("Left Foot Target: " + leftFootTarget.position);
    //     // Debug.Log("Left HAND : " + leftHandTarget.position);
    // }
    // LateUpdate
    void LateUpdate()
    {
        // === 1. Move Hips Target ===
        Vector3 leftHipPos = ConvertMediaPipeToUnity(receivedPose.LEFT_HIP);
        Vector3 rightHipPos = ConvertMediaPipeToUnity(receivedPose.RIGHT_HIP);
        Vector3 midHip = (leftHipPos + rightHipPos) * 0.5f;

        hipsTarget.position = Vector3.Lerp(hipsTarget.position, midHip, Time.deltaTime * 5);
        avatarHips.position = Vector3.Lerp(avatarHips.position, hipsTarget.position, Time.deltaTime * 5);

        // Compute stable hip rotation
        Vector3 hipDirection = (rightHipPos - leftHipPos).normalized; // Sideways direction, i.e. XZ axis vector
        Vector3 forwardDirection = -Vector3.Cross(Vector3.up, hipDirection).normalized; // Compute correct forward direction! (i.e. face pos Z axis)
        Quaternion hipRotation = Quaternion.identity; // Default rotation to prevent error
        if (forwardDirection != Vector3.zero)
        {
            hipRotation = Quaternion.LookRotation(forwardDirection, Vector3.up);
        }

        // avatarHips.rotation = Quaternion.Slerp(avatarHips.rotation, hipRotation, Time.deltaTime * 5);
        // Blend hips rotation more aggressively
        float hipBlendFactor = 0.9f; // Increase influence of manual rotation
        avatarHips.rotation = Quaternion.Slerp(avatarHips.rotation, hipRotation, hipBlendFactor);


        // === 2. Compute torso rotation **relative** to the hip's rotation ===
        Vector3 leftShoulderPos = ConvertMediaPipeToUnity(receivedPose.LEFT_SHOULDER);
        Vector3 rightShoulderPos = ConvertMediaPipeToUnity(receivedPose.RIGHT_SHOULDER);
        Vector3 torsoDirection = (rightShoulderPos - leftShoulderPos).normalized;
        // Quaternion torsoRotation = Quaternion.LookRotation(torsoDirection, Vector3.up);
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
        leftHandTarget.position = Vector3.MoveTowards(leftHandTarget.position, ConvertMediaPipeToUnity(receivedPose.LEFT_WRIST), Time.deltaTime * 5);
        rightHandTarget.position = Vector3.MoveTowards(rightHandTarget.position, ConvertMediaPipeToUnity(receivedPose.RIGHT_WRIST), Time.deltaTime * 5);
        leftFootTarget.position = Vector3.MoveTowards(leftFootTarget.position, ConvertMediaPipeToUnity(receivedPose.LEFT_ANKLE, isFoot: true), Time.deltaTime * 5);
        rightFootTarget.position = Vector3.MoveTowards(rightFootTarget.position, ConvertMediaPipeToUnity(receivedPose.RIGHT_ANKLE, isFoot: true), Time.deltaTime * 5);
        headTarget.position = Vector3.MoveTowards(headTarget.position, ConvertMediaPipeToUnity(receivedPose.NOSE), Time.deltaTime * 5);

        // === 4. Set Hand & Foot Rotation (Important for IK) ===
        Vector3 leftElbowPos = ConvertMediaPipeToUnity(receivedPose.LEFT_ELBOW);
        Vector3 leftWristPos = ConvertMediaPipeToUnity(receivedPose.LEFT_WRIST);
        Vector3 leftForearmDir = (leftWristPos - leftElbowPos).normalized;
        leftHandTarget.rotation = Quaternion.identity; // Default rotation to prevent error
        if (leftForearmDir != Vector3.zero)
        {
            leftHandTarget.rotation = Quaternion.LookRotation(leftForearmDir, Vector3.up);
        }

        Vector3 rightElbowPos = ConvertMediaPipeToUnity(receivedPose.RIGHT_ELBOW);
        Vector3 rightWristPos = ConvertMediaPipeToUnity(receivedPose.RIGHT_WRIST);
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
}
