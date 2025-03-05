using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;


/// script listens for UDP messages from Python and updates the position of `LeftHandTarget`.
/// The left hand follows `LeftHandTarget` using Animation Rigging (Two Bone IK). Check hierarchy
public class PoseReceiver : MonoBehaviour
{
    // specifying a public Transform here gives the Pose Receiver (script) that specified field in hierarchy
    public Transform leftHandTarget, rightHandTarget; // For this field in hierarchy, set reference to 'LeftHandTarget', 'RightHandTarget' GameObject
    // this "leftHandTarget" will be a field in character hierarchy, LeftHandTarget (transform) should be assigned to it    public Transform leftHandTarget, rightHandTarget;
    public Transform leftFootTarget, rightFootTarget;
    public Transform headTarget;

    public Transform hipsTarget;  // store the Hips transform

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
        // Initialize UDP socket on port 5005
        udpClient = new UdpClient(5005);

        // Start a background thread for receiving UDP data
        udpReceiveThread = new Thread(new ThreadStart(ReceiveData));
        udpReceiveThread.IsBackground = true;
        udpReceiveThread.Start();
    }

    // convert mediapipe xyz to unity world coords
    Vector3 ConvertMediaPipeToUnity(Vector3 landmark, float baseDepth = 0.0f)
    {
        // // apply scaling
        // return new Vector3(mpPosition.x * dynamicScale, mpPosition.y * dynamicScale, -mpPosition.z * dynamicScale);

        Camera mainCamera = Camera.main;

        // // Mediapipe provides X in [0,1] with (0,0) at top-left.
        // // In Unity's viewport, (0,0) is bottom-left. So flip Y.
        // float viewportX = landmark.x;
        // float viewportY = 1.0f - landmark.y;

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

        // Compute Depth (MediaPipe Z is relative, so map it to a useful depth of 0 bc avatar at 0,0,0)
        float unityZ = baseDepth + (-landmark.z * 1.7f); // Convert negative depth (1.7/2 = 0.85)

        // Apply scaling factors
        float unityX = -(viewportX - 0.5f) * 3.4f;  // Scale X to match shoulder width (1.7m/2) 0.85 = 1.0f
        float unityY = (viewportY - 0.5f) * 3.4f;     // Scale Y to match avatar height (1.7m) = 3.0f


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
                // Debug.Log("Received JSON: " + json);

                // Convert JSON string to PoseData object (parse)
                PoseData tempPose = JsonUtility.FromJson<PoseData>(json);

                // receivedPose.LEFT_WRIST = ConvertMediaPipeToUnity(tempPose.LEFT_WRIST);
                // receivedPose.RIGHT_WRIST = ConvertMediaPipeToUnity(tempPose.RIGHT_WRIST);
                // receivedPose.LEFT_ANKLE = ConvertMediaPipeToUnity(tempPose.LEFT_ANKLE);
                // receivedPose.RIGHT_ANKLE = ConvertMediaPipeToUnity(tempPose.RIGHT_ANKLE);
                // receivedPose.NOSE = ConvertMediaPipeToUnity(tempPose.NOSE);

                // receivedPose.LEFT_HIP = ConvertMediaPipeToUnity(tempPose.LEFT_HIP);
                // receivedPose.RIGHT_HIP = ConvertMediaPipeToUnity(tempPose.RIGHT_HIP);
                receivedPose.LEFT_WRIST = tempPose.LEFT_WRIST;
                receivedPose.RIGHT_WRIST = tempPose.RIGHT_WRIST;
                receivedPose.LEFT_ANKLE = tempPose.LEFT_ANKLE;
                receivedPose.RIGHT_ANKLE = tempPose.RIGHT_ANKLE;
                receivedPose.NOSE = tempPose.NOSE;

                receivedPose.LEFT_HIP = tempPose.LEFT_HIP;
                receivedPose.RIGHT_HIP = tempPose.RIGHT_HIP;

                // Debug.Log(receivedPose.LEFT_WRIST.x);
                // Debug.Log("Z");
                // Debug.Log(receivedPose.LEFT_WRIST.z);
                // Debug.Log(receivedPose.LEFT_HIP.x);
                // Debug.Log("Z");
                // Debug.Log(receivedPose.LEFT_HIP.z);
            }
            catch (SocketException e)
            {
                Debug.LogError("Socket Exception: " + e.Message);
            }
        }
    }

    /// Updates `LeftHandTarget` position smoothly based on received UDP data.
    /// Runs every frame.
    void Update()
    {
        // root of avatar, midhip
        // Compute MID_HIP dynamically as the midpoint of LEFT_HIP and RIGHT_HIP
        Vector3 midHip = (ConvertMediaPipeToUnity(receivedPose.LEFT_HIP) + ConvertMediaPipeToUnity(receivedPose.RIGHT_HIP)) / 2;
        Debug.Log("LEFT HIP: " + ConvertMediaPipeToUnity(receivedPose.LEFT_HIP));
        Debug.Log("RIGHT HIP: " + ConvertMediaPipeToUnity(receivedPose.RIGHT_HIP));

        // Set avatar's root position to MID_HIP
        hipsTarget.position = Vector3.Lerp(hipsTarget.position, midHip, Time.deltaTime * 5);
        Debug.Log("Hips Target: " + hipsTarget.position);


        ////// RIGHT NOW THE receivedPose.LEFT_WRIST/LEFT_HIP/RIGHT_HIP's scaled ver is being used, but is this right?

        // Smooth movement to avoid sudden jumps
        leftHandTarget.position = Vector3.Lerp(leftHandTarget.position, ConvertMediaPipeToUnity(receivedPose.LEFT_WRIST), Time.deltaTime * 5);
        // add more body parts here..
        rightHandTarget.position = Vector3.Lerp(rightHandTarget.position, ConvertMediaPipeToUnity(receivedPose.RIGHT_WRIST), Time.deltaTime * 5);

        leftFootTarget.position = Vector3.Lerp(leftFootTarget.position, ConvertMediaPipeToUnity(receivedPose.LEFT_ANKLE), Time.deltaTime * 5);
        rightFootTarget.position = Vector3.Lerp(rightFootTarget.position, ConvertMediaPipeToUnity(receivedPose.RIGHT_ANKLE), Time.deltaTime * 5);

        headTarget.position = Vector3.Lerp(headTarget.position, ConvertMediaPipeToUnity(receivedPose.NOSE), Time.deltaTime * 5);

        // Debug.Log("Left Foot Target: " + leftFootTarget.position);
        // Debug.Log("Left HAND : " + leftHandTarget.position);
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
        // public Vector3 head leftShoulder, rightShoulder, spine, hips;
        // public Vector3 leftElbow, rightElbow, leftKnee, rightKnee;
    }
}
