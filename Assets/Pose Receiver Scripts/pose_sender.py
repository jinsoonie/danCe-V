import socket
import json
import time

# configure UDP socket
UDP_IP = "127.0.0.1"    # local host IP as assume running on same device
UDP_PORT = 5005         # as specified in Unity pose_receiver_script
TEST_MESSAGE = "Hello Unity from Python!"

print(f"message: {TEST_MESSAGE}")

# Read and process the .txt file
frames = []
buffer = ""

with open("danny_poses.txt", "r") as file:
    # for line in file:
    #     line = line.strip()
    #     if not line:
    #         continue  # Skip empty lines

    #     buffer += line  # Collect JSON dictionary lines

    #     # Detect full JSON dictionary (closing bracket '}}')
    #     if buffer.endswith("}{") or buffer.endswith("}}"):
    #         try:
    #             pose_frame = json.loads(buffer)  # Parse JSON (handles nested dictionaries)
    #             frames.append(pose_frame)  # Store frame
    #         except json.JSONDecodeError:
    #             print("Skipping malformed frame.")
    #         buffer = ""  # Reset buffer for next frame
    data = file.read()

# Split into separate JSON objects by finding `{` and `}`
frames = []
buffer = ""
depth = 0  # Tracks JSON object depth

for char in data:
    buffer += char
    if char == "{":
        depth += 1
    elif char == "}":
        depth -= 1

    # If depth reaches zero, have a complete JSON object
    if depth == 0 and buffer.strip():
        try:
            frame = json.loads(buffer)  # Parse JSON
            frames.append(frame)
        except json.JSONDecodeError as e:
            print(f"Skipping invalid JSON frame: {e}")
        buffer = ""  # Reset buffer for the next frame

neutral_pose = {
    "LEFT_WRIST": {"x": -0.389, "y": 0.64, "z": 0.152},      # Arms extended horizontally
    "rightHand": {"x": 0.194, "y": 0.496, "z": 0.328},
    "leftFoot": {"x": -0.437, "y": -1.234, "z": 0.1838325},     
    "rightFoot": {"x": 0.607, "y": -0.527, "z": 0.192467},
    "head": {"x": 0.406, "y": 0.413, "z": 0.608},           # Head positioned naturally
}

t_pose = {
    "LEFT_WRIST": {"x": -0.7, "y": 0.64, "z": 0.152},  
    "rightHand": {"x": 0.7, "y": 0.64, "z": 0.152},
    "leftFoot": {"x": -0.3, "y": -1.234, "z": 0.1838325},     
    "rightFoot": {"x": 0.3, "y": -1.234, "z": 0.192467},
    "head": {"x": 0.0, "y": 0.5, "z": 0.0}
}

neutral_pose_mirror = {
    "LEFT_WRIST": {"x": -0.194, "y": 0.496, "z": 0.328},      
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
# for pose in poses:
    # sock.sendto(json.dumps(pose).encode(), (UDP_IP, UDP_PORT))
    # print(f"Sent pose: {json.dumps(pose, indent=2)}")
    #time.sleep(2)  # Adjust timing for realistic animation feel

# for i in range(5):
#     sock.sendto(json.dumps(neutral_pose).encode(), (UDP_IP, UDP_PORT))
#     time.sleep(1)
#     sock.sendto(json.dumps(t_pose).encode(), (UDP_IP, UDP_PORT))
#     time.sleep(1)
#     sock.sendto(json.dumps(neutral_pose_mirror).encode(), (UDP_IP, UDP_PORT))
#     time.sleep(1)
#     print(f"Sent: {json.dumps(neutral_pose_mirror).encode()}")

# Function to convert uppercase XYZ to lowercase xyz for Unity
def convert_to_lowercase_xyz(keypoint):
    return {
        "x": keypoint["X"],
        "y": keypoint["Y"],
        "z": keypoint["Z"]
    }

frame_count = 0
# Send frames one by one
frame_rate = 1 / 22  # Simulating ~22 FPS
for frame in frames:
    # Extract only the required keypoints
    pose_data = {
        "LEFT_WRIST": convert_to_lowercase_xyz(frame["LEFT_WRIST"]),
        "RIGHT_WRIST": convert_to_lowercase_xyz(frame["RIGHT_WRIST"]),
        "LEFT_ANKLE": convert_to_lowercase_xyz(frame["LEFT_ANKLE"]),
        "RIGHT_ANKLE": convert_to_lowercase_xyz(frame["RIGHT_ANKLE"]),
        "NOSE": convert_to_lowercase_xyz(frame["NOSE"]),
        "LEFT_HIP": convert_to_lowercase_xyz(frame["LEFT_HIP"]),
        "RIGHT_HIP": convert_to_lowercase_xyz(frame["RIGHT_HIP"])
    }

    # Convert to JSON
    json_data = json.dumps(pose_data)

    # Send over UDP
    sock.sendto(json_data.encode(), (UDP_IP, UDP_PORT))
    
    print(f"Sent: {json_data}")
    time.sleep(frame_rate)  # Maintain real-time playback speed

    frame_count += 1
