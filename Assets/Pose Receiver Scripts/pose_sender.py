import socket
import json
import time

# configure UDP socket
UDP_IP = "127.0.0.1"    # local host IP as assume running on same device
UDP_PORT = 5005         # as specified in Unity pose_receiver_script
TEST_MESSAGE = "Hello Unity from Python!"

print(f"message: {TEST_MESSAGE}")

# Simulated movements
poses = [
    # **Neutral Standing Pose (T-Pose)**
    {
        "leftHand": {"x": -0.5, "y": 1.5, "z": 0.0},
        "rightHand": {"x": 0.5, "y": 1.5, "z": 0.0},
        "leftFoot": {"x": -0.3, "y": 0.0, "z": 0.0},
        "rightFoot": {"x": 0.3, "y": 0.0, "z": 0.0},
        "head": {"x": 0.0, "y": 1.8, "z": 0.0},
        "leftShoulder": {"x": -0.4, "y": 1.5, "z": 0.0},
        "rightShoulder": {"x": 0.4, "y": 1.5, "z": 0.0},
        "spine": {"x": 0.0, "y": 1.2, "z": 0.0},
        "hips": {"x": 0.0, "y": 1.0, "z": 0.0},
        "leftElbow": {"x": -0.6, "y": 1.3, "z": 0.0},
        "rightElbow": {"x": 0.6, "y": 1.3, "z": 0.0},
        "leftKnee": {"x": -0.3, "y": 0.5, "z": 0.0},
        "rightKnee": {"x": 0.3, "y": 0.5, "z": 0.0},
    },
    # **Walking (Left Foot Forward)**
    {
        "leftHand": {"x": -0.5, "y": 1.4, "z": 0.0},
        "rightHand": {"x": 0.5, "y": 1.6, "z": 0.0},
        "leftFoot": {"x": -0.3, "y": 0.0, "z": 0.1},
        "rightFoot": {"x": 0.3, "y": 0.1, "z": -0.1},
        "head": {"x": 0.0, "y": 1.8, "z": 0.0},
        "leftShoulder": {"x": -0.4, "y": 1.5, "z": 0.0},
        "rightShoulder": {"x": 0.4, "y": 1.5, "z": 0.0},
        "spine": {"x": 0.0, "y": 1.2, "z": 0.0},
        "hips": {"x": 0.0, "y": 1.0, "z": 0.0},
        "leftElbow": {"x": -0.6, "y": 1.2, "z": 0.0},
        "rightElbow": {"x": 0.6, "y": 1.4, "z": 0.0},
        "leftKnee": {"x": -0.3, "y": 0.4, "z": 0.1},
        "rightKnee": {"x": 0.3, "y": 0.5, "z": -0.1},
    },
    # **Jumping Motion (Mid-Air)**
    {
        "leftHand": {"x": -0.5, "y": 1.7, "z": 0.0},
        "rightHand": {"x": 0.5, "y": 1.7, "z": 0.0},
        "leftFoot": {"x": -0.3, "y": 0.4, "z": 0.0},
        "rightFoot": {"x": 0.3, "y": 0.4, "z": 0.0},
        "head": {"x": 0.0, "y": 2.0, "z": 0.0},
        "leftShoulder": {"x": -0.4, "y": 1.6, "z": 0.0},
        "rightShoulder": {"x": 0.4, "y": 1.6, "z": 0.0},
        "spine": {"x": 0.0, "y": 1.4, "z": 0.0},
        "hips": {"x": 0.0, "y": 1.2, "z": 0.0},
        "leftElbow": {"x": -0.6, "y": 1.5, "z": 0.0},
        "rightElbow": {"x": 0.6, "y": 1.5, "z": 0.0},
        "leftKnee": {"x": -0.3, "y": 0.6, "z": 0.0},
        "rightKnee": {"x": 0.3, "y": 0.6, "z": 0.0},
    }
]

neutral_pose = {
    "leftHand": {"x": -0.5, "y": 1.5, "z": 0.0},      # Arms out
    "rightHand": {"x": 0.5, "y": 1.5, "z": 0.0},
    "leftFoot": {"x": -0.3, "y": 0.0, "z": 0.0},      # Feet flat
    "rightFoot": {"x": 0.3, "y": 0.0, "z": 0.0},
    "head": {"x": 0.0, "y": 0, "z": 0.0},           # Head upright
    "leftShoulder": {"x": -0.4, "y": 1.5, "z": 0.0},  # Shoulders aligned
    "rightShoulder": {"x": 0.4, "y": 1.5, "z": 0.0},
    "spine": {"x": 0.0, "y": 1.2, "z": 0.0},          # Straight torso
    "hips": {"x": 0.0, "y": 1.0, "z": 0.0},           # Centered hips
    "leftElbow": {"x": -0.6, "y": 1.3, "z": 0.0},     # Elbows slightly bent
    "rightElbow": {"x": 0.6, "y": 1.3, "z": 0.0},
    "leftKnee": {"x": -0.3, "y": 0.5, "z": 0.0},      # Legs straight
    "rightKnee": {"x": 0.3, "y": 0.5, "z": 0.0}
}


# init UDP socket
sock = socket.socket(socket.AF_INET,    # INTERNET
                     socket.SOCK_DGRAM) # UDP

# test sending message - works
# sock.sendto(TEST_MESSAGE.encode(), (UDP_IP, UDP_PORT))

# while True:
# pose_data = {"x": 0.5, "y": 1.0, "z": 0.0}  # Example (Replace with real tracking)
# pose_data = poses[0]  # Example (Replace with real tracking)
# sock.sendto(json.dumps(pose_data).encode(), (UDP_IP, UDP_PORT))

# Loop through poses with delays to simulate real-time movement
for pose in poses:
    # sock.sendto(json.dumps(pose).encode(), (UDP_IP, UDP_PORT))
    print(f"Sent pose: {json.dumps(pose, indent=2)}")
    #time.sleep(2)  # Adjust timing for realistic animation feel

sock.sendto(json.dumps(neutral_pose).encode(), (UDP_IP, UDP_PORT))
