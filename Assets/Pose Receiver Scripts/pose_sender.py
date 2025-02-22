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
    "leftHand": {"x": -0.389, "y": 0.64, "z": 0.152},      # Arms extended horizontally
    "rightHand": {"x": 0.194, "y": 0.496, "z": 0.328},
    "leftFoot": {"x": -0.437, "y": -1.234, "z": 0.1838325},     
    "rightFoot": {"x": 0.607, "y": -0.527, "z": 0.192467},
    "head": {"x": 0.406, "y": 0.413, "z": 0.608},           # Head positioned naturally
}

t_pose = {
    "leftHand": {"x": -0.7, "y": 0.64, "z": 0.152},  
    "rightHand": {"x": 0.7, "y": 0.64, "z": 0.152},
    "leftFoot": {"x": -0.3, "y": -1.234, "z": 0.1838325},     
    "rightFoot": {"x": 0.3, "y": -1.234, "z": 0.192467},
    "head": {"x": 0.0, "y": 0.5, "z": 0.0}
}

neutral_pose_mirror = {
    "leftHand": {"x": -0.194, "y": 0.496, "z": 0.328},      
    "rightHand": {"x": 0.389, "y": 0.64, "z": 0.152},
    "leftFoot": {"x": 0.437, "y": -1.234, "z": 0.1838325},     
    "rightFoot": {"x": -0.607, "y": -0.527, "z": 0.192467},
    "head": {"x": -0.406, "y": 0.413, "z": 0.608}
}



'''"leftShoulder": {"x": -0.4, "y": 1.6, "z": 0.0},  
    "rightShoulder": {"x": 0.4, "y": 1.6, "z": 0.0},
    "spine": {"x": 0.0, "y": 1.3, "z": 0.0},          # Torso aligned
    "hips": {"x": 0.0, "y": 1.0, "z": 0.0},           # Hips neutral position
    "leftElbow": {"x": -0.6, "y": 1.5, "z": 0.0},     # Elbows at shoulder height
    "rightElbow": {"x": 0.6, "y": 1.5, "z": 0.0},
    "leftKnee": {"x": -0.15, "y": 0.5, "z": 0.0},     # Legs straight
    "rightKnee": {"x": 0.15, "y": 0.5, "z": 0.0}'''

'''"leftHand": {"x": 3.782351e-10, "y": 0.2527094, "z": 5.080531e-10},      # Arms extended horizontally
    "rightHand": {"x": -3.577438e-10, "y": 0.2527121, "z": -2.266648e-11},
    "leftFoot": {"x": 1.099628e-10, "y": 0.07426425, "z": 0.0},     # Feet aligned with body
    "rightFoot": {"x": -1.265703e-10, "y": 0.07426425, "z": -2.383091e-11},
    "head": {"x": 0.0, "y": 0.06762298, "z": 0.03044908},           # Head positioned naturally
    "leftShoulder": {"x": -0.4, "y": 1.6, "z": 0.0},  # Shoulder width position
    "rightShoulder": {"x": 0.4, "y": 1.6, "z": 0.0},
    "spine": {"x": 0.0, "y": 1.3, "z": 0.0},          # Torso aligned
    "hips": {"x": 0.0, "y": 1.0, "z": 0.0},           # Hips neutral position
    "leftElbow": {"x": -0.6, "y": 1.5, "z": 0.0},     # Elbows at shoulder height
    "rightElbow": {"x": 0.6, "y": 1.5, "z": 0.0},
    "leftKnee": {"x": -0.15, "y": 0.5, "z": 0.0},     # Legs straight
    "rightKnee": {"x": 0.15, "y": 0.5, "z": 0.0} '''
    


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

for i in range(5):
    sock.sendto(json.dumps(neutral_pose).encode(), (UDP_IP, UDP_PORT))
    time.sleep(1.7)
    sock.sendto(json.dumps(t_pose).encode(), (UDP_IP, UDP_PORT))
    time.sleep(1.7)
    sock.sendto(json.dumps(neutral_pose_mirror).encode(), (UDP_IP, UDP_PORT))
    time.sleep(1.7)

