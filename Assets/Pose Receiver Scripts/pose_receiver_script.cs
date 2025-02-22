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
    // public Transform leftShoulderTarget, rightShoulderTarget;
    // public Transform spineTarget, hipsTarget, leftElbowTarget, rightElbowTarget;
    // public Transform leftKneeTarget, rightKneeTarget;


    private UdpClient udpClient; // UDP socket to receive data
    private Thread udpReceiveThread; // Background thread for listening to UDP messages
    // private Vector3 receivedPosition = Vector3.zero; // Stores the received position data (for leftHand right now only)
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
                Debug.Log(json);

                // Convert JSON string to PoseData object (parse)
                PoseData tempPose = JsonUtility.FromJson<PoseData>(json);

                // Apply coordinate transformation once, i.e. python-to-unity coordinate system
                receivedPose.leftHand = new Vector3(-tempPose.leftHand.x, tempPose.leftHand.y, -tempPose.leftHand.z);
                receivedPose.rightHand = new Vector3(-tempPose.rightHand.x, tempPose.rightHand.y, -tempPose.rightHand.z);
                receivedPose.leftFoot = new Vector3(-tempPose.leftFoot.x, tempPose.leftFoot.y, -tempPose.leftFoot.z);
                receivedPose.rightFoot = new Vector3(-tempPose.rightFoot.x, tempPose.rightFoot.y, -tempPose.rightFoot.z);
                receivedPose.head = new Vector3(-tempPose.head.x, tempPose.head.y, -tempPose.head.z);

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
        // Smooth movement to avoid sudden jumps
        leftHandTarget.position = Vector3.Lerp(leftHandTarget.position, receivedPose.leftHand, Time.deltaTime * 5);
        // add more body parts here..
        rightHandTarget.position = Vector3.Lerp(rightHandTarget.position, receivedPose.rightHand, Time.deltaTime * 5);
        // rightFootTarget.position = receivedPose.rightFoot;
        // leftFootTarget.position = receivedPose.leftFoot;
        // leftHandTarget.position = receivedPose.leftHand;
        // rightHandTarget.position = receivedPose.rightHand;
        // headTarget.position = receivedPose.head;

        leftFootTarget.position = Vector3.Lerp(leftFootTarget.position, receivedPose.leftFoot, Time.deltaTime * 5);
        rightFootTarget.position = Vector3.Lerp(rightFootTarget.position, receivedPose.rightFoot, Time.deltaTime * 5);

        headTarget.position = Vector3.Lerp(headTarget.position, receivedPose.head, Time.deltaTime * 5);

        // leftShoulderTarget.position = Vector3.Lerp(leftShoulderTarget.position, receivedPose.leftShoulder, Time.deltaTime * 5);
        // rightShoulderTarget.position = Vector3.Lerp(rightShoulderTarget.position, receivedPose.rightShoulder, Time.deltaTime * 5);
        // spineTarget.position = Vector3.Lerp(spineTarget.position, receivedPose.spine, Time.deltaTime * 5);
        // hipsTarget.position = Vector3.Lerp(hipsTarget.position, receivedPose.hips, Time.deltaTime * 5);

        // leftElbowTarget.position = Vector3.Lerp(leftElbowTarget.position, receivedPose.leftElbow, Time.deltaTime * 5);
        // rightElbowTarget.position = Vector3.Lerp(rightElbowTarget.position, receivedPose.rightElbow, Time.deltaTime * 5);
        // leftKneeTarget.position = Vector3.Lerp(leftKneeTarget.position, receivedPose.leftKnee, Time.deltaTime * 5);
        // rightKneeTarget.position = Vector3.Lerp(rightKneeTarget.position, receivedPose.rightKnee, Time.deltaTime * 5);
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
        // public float x; // X coordinate of hand position
        // public float y; // Y coordinate of hand position
        // public float z; // Z coordinate (depth)
        public Vector3 leftHand, rightHand, leftFoot, rightFoot;
        public Vector3 head;
        // leftShoulder, rightShoulder, spine, hips;
        // public Vector3 leftElbow, rightElbow, leftKnee, rightKnee;
    }
}
