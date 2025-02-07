using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

/// script listens for UDP messages from Python and updates the position of `LeftHandTarget`.
/// The left hand follows `LeftHandTarget` using Animation Rigging (Two Bone IK). Check hierarchy
public class PoseReceiver : MonoBehaviour
{
    public Transform leftHandTarget; // Reference to 'LeftHandTarget' GameObject
    // this "leftHandTarget" will be a field in character hierarchy, LeftHandTarget (transform) should be assigned to it

    private UdpClient udpClient; // UDP socket to receive data
    private Thread udpReceiveThread; // Background thread for listening to UDP messages
    private Vector3 receivedPosition = Vector3.zero; // Stores the received position data

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

                // Convert JSON string to PoseData object
                PoseData pose = JsonUtility.FromJson<PoseData>(json);

                // Convert received position into Unity's coordinate space
                receivedPosition = new Vector3(pose.x, pose.y, pose.z);
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
        leftHandTarget.position = Vector3.Lerp(leftHandTarget.position, receivedPosition, Time.deltaTime * 5);
    }

    /// Cleans up UDP thread when Unity application closes.
    private void OnApplicationQuit()
    {
        udpReceiveThread.Abort(); // Stop the background thread
        udpClient.Close(); // Close the UDP connection
    }

    /// Data structure for receiving pose data from Python.
    [System.Serializable]
    public class PoseData
    {
        public float x; // X coordinate of hand position
        public float y; // Y coordinate of hand position
        public float z; // Z coordinate (depth)
    }
}
