import mediapipe as mp
import socket
import json
import time
import os
import sys
import string
from simple_landmark_reader import SimplePoseLandmarkReader
import cv2

# configure UDP socket
UDP_IP = "127.0.0.1"    # local host IP as assume running on same device
UDP_PORT = 5005         # as specified in Unity pose_receiver_script
TEST_MESSAGE = "Hello Unity from Python pose_sender.py!"

print(f"message: {TEST_MESSAGE}")

# init UDP socket
sock = socket.socket(socket.AF_INET,    # INTERNET
                     socket.SOCK_DGRAM) # UDP

# initialize MediaPipe Pose model
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils  # Drawing utility
mp_drawing_styles = mp.solutions.drawing_styles  # Styles
pose = mp_pose.Pose()

# json_to_analyze for akul/danny's json
script_dir = os.path.dirname(os.path.abspath(__file__))  # Get directory of the script
json_to_analyze = os.path.join(script_dir, "danny_poses.txt")  # full path

# when this script invoked, USE_LIVE_CAMERA is arg1, videoPath is arg2 (only used when arg1 = True)
# SELECT WHICH MODE TO USE, USE_LIVE_CAMERA True is for live capture of user CV, False is for reference mp4 .json
def main(USE_LIVE_CAMERA, videoPath=""):
    if USE_LIVE_CAMERA == "true":
        print("Running in REAL-TIME mode (Live Camera)... Press 'q' to quit.")

        # Open webcam for live feed
        cap = cv2.VideoCapture(0)  # 0 = Default webcam
    else:
        print("Running in REPLAY mode (Reading JSON file)...")

        # Open videoPath .mp4
        cap = cv2.VideoCapture(videoPath)

    # based on USE_LIVE_CAMERA, run CV on live feed or videoPath .mp4
    while cap.isOpened():
        ret, frame = cap.read()
        # If either reached end of .mp4 OR Live Camera Feed Ended
        if not ret:
            print("End of video or Live Camera feed lost!")
            break

        # Convert to RGB (for MediaPipe)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process pose detection
        results = pose.process(rgb_frame)

        if results.pose_landmarks:
            # Draw landmarks on the original frame (BGR)
            mp_drawing.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )

            # Extract XYZ landmarks
            landmarks_data = {}
            for landmark_enum in mp_pose.PoseLandmark:
                idx = landmark_enum.value  # Get landmark index
                landmark = results.pose_landmarks.landmark[idx]
                landmarks_data[landmark_enum.name] = {
                    "x": round(landmark.x, 4),
                    "y": round(landmark.y, 4),
                    "z": round(landmark.z, 4)
                }

            # Convert to JSON string
            pose_json = json.dumps(landmarks_data)
            # print(pose_json)

            # Send pose data over UDP directly to Unity, no json made
            sock.sendto(pose_json.encode(), (UDP_IP, UDP_PORT))

        # Show video output (optional)
        cv2.imshow("Live Pose Tracking", frame)

        # Capture at ~30 fps, Reduce CPU usage
        time.sleep(1/30)  # ~30 FPS

        # Quit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting live mode...")
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("Camera closed properly.")

    # else:
    #     print("Running in REPLAY mode (Reading JSON file)...")

    #     # Add Akul / Danny json processing logic here
    #     #

    #     # init frames, to be populated and sent to unity
    #     frames = []

    #     ### NEED TO ADD CV CODE FOR MAKING .mp4 INTO json
    #     # i.e. use videoPath arg
    #     frames = parse_akul_json(frames)
    #     send_akul_json_to_unity(frames)

def parse_akul_json(frames):
    with open(json_to_analyze, "r") as file:
        data = file.read()

    # Split into separate JSON objects by finding `{` and `}`
    depth = 0  # Tracks JSON object depth
    buffer = ""

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
    
    return frames
    

# Function to convert uppercase XYZ to lowercase xyz for Unity
def convert_to_lowercase_xyz(keypoint):
    return {
        "x": keypoint["X"],
        "y": keypoint["Y"],
        "z": keypoint["Z"]
    }

#### FOR DANNY'S JSONs, USE THIS SECTION OF CODE ####

# # Create a reader
# reader = SimplePoseLandmarkReader()

# # Access data
# landmarks = reader.get_pose_landmarks("reference", 0, 0)  # Get landmarks for frame 0, pose 0
# nose_pos = reader.get_landmark_position("reference", 0, "nose")  # Get NOSE landmark position

# # Load data
# reference_json = "reference_pose_landmarks.json"
# test_json = "test_pose_landmarks.json"
# normalized_json = "normalized_test_landmarks.json"

# # Try to load the files
# files_to_load = [
#     (reference_json, "reference"),
#     (test_json, "test"),
#     (normalized_json, "normalized")
# ]

# loaded_files = []
# for file_path, name in files_to_load:
#     if os.path.exists(file_path):
#         success = reader.load_json(file_path, name)
#         if success:
#             loaded_files.append(name)
#             print(f"Loaded {name} dataset")

# if not loaded_files:
#     print("No data files found. Please make sure the JSON files are in the current directory.")
#     print("Expecting files named:")
#     for file_path, _ in files_to_load:
#         print(f"  - {file_path}")
#     exit(1)

# print("\nAvailable datasets:", reader.list_datasets())

# # Show sample usage
# if loaded_files:
#     dataset = loaded_files[0]  # Use the first loaded dataset (0 is ref, 1 is test, 2 is norm)
#     print("DATASET IS: ")
#     print(dataset)
    
#     print(f"\nSample usage for dataset '{dataset}':")
#     print("\n1. Get the number of frames:")
#     frame_count = reader.get_frame_count(dataset)
#     print(f"   Number of frames: {frame_count}")
    
#     if frame_count > 0:
#         print("\n2. Get data for frame 0:")
#         frame_data = reader.get_frame(dataset, 0)
#         print(f"   Frame index: {frame_data['frame']}")
#         print(f"   Number of poses: {len(frame_data['poses'])}")
        
#         print("\n3. Get landmarks for pose 0 in frame 0:")
#         landmarks = reader.get_pose_landmarks(dataset, 0, 0)
#         print(f"   Number of landmarks: {len(landmarks)}")
        
#         print("\n4. Get position of the NOSE landmark in frame 0:")
#         nose_pos = reader.get_landmark_position(dataset, 0, "nose", 0)
#         print(f"   NOSE position: x={nose_pos['x']:.4f}, y={nose_pos['y']:.4f}, z={nose_pos['z']:.4f}")
        
#         print("\n5. Convert dataset to DataFrame and show first few rows:")
#         print("   (This can be useful for pandas-based analysis)")
#         df = reader.convert_to_dataframe(dataset)
#         print(df.head())

#     frame_rate = 1 / 30  # Simulating ~30 FPS
#     for frame_idx in range(frame_count):
#         # Extract only the required keypoints
#         pose_data = {
#             "LEFT_WRIST": reader.get_landmark_position(dataset, frame_idx, "left_wrist"),
#             "RIGHT_WRIST": reader.get_landmark_position(dataset, frame_idx, "right_wrist"),
#             "LEFT_ANKLE": reader.get_landmark_position(dataset, frame_idx, "left_ankle"),
#             "RIGHT_ANKLE": reader.get_landmark_position(dataset, frame_idx, "right_ankle"),
#             "NOSE": reader.get_landmark_position(dataset, frame_idx, "nose"),
#             "LEFT_HIP": reader.get_landmark_position(dataset, frame_idx, "left_hip"),
#             "RIGHT_HIP": reader.get_landmark_position(dataset, frame_idx, "right_hip"),
#             "LEFT_SHOULDER": reader.get_landmark_position(dataset, frame_idx, "left_shoulder"),
#             "RIGHT_SHOULDER": reader.get_landmark_position(dataset, frame_idx, "right_shoulder"),
#             "LEFT_ELBOW": reader.get_landmark_position(dataset, frame_idx, "left_elbow"),
#             "RIGHT_ELBOW": reader.get_landmark_position(dataset, frame_idx, "right_elbow")
#         }
#         # print(pose_data)

#         # Convert to JSON
#         json_data = json.dumps(pose_data)

#         # Send over UDP
#         sock.sendto(json_data.encode(), (UDP_IP, UDP_PORT))
        
#         # print(f"Sent: {json_data}")
#         time.sleep(frame_rate)  # Maintain real-time playback speed

#### END DANNY'S JSONs parser code section  ####

#### FOR AKUL'S JSONs, USE THIS SECTION OF CODE ####

def send_akul_json_to_unity(frames):
    # Send frames one by one
    frame_rate = 1 / 30  # Simulating ~30 FPS
    for frame in frames:
        # Extract only the required keypoints
        pose_data = {
            "LEFT_WRIST": convert_to_lowercase_xyz(frame["LEFT_WRIST"]),
            "RIGHT_WRIST": convert_to_lowercase_xyz(frame["RIGHT_WRIST"]),
            "LEFT_ANKLE": convert_to_lowercase_xyz(frame["LEFT_ANKLE"]),
            "RIGHT_ANKLE": convert_to_lowercase_xyz(frame["RIGHT_ANKLE"]),
            "NOSE": convert_to_lowercase_xyz(frame["NOSE"]),
            "LEFT_HIP": convert_to_lowercase_xyz(frame["LEFT_HIP"]),
            "RIGHT_HIP": convert_to_lowercase_xyz(frame["RIGHT_HIP"]),
            "LEFT_SHOULDER": convert_to_lowercase_xyz(frame["LEFT_SHOULDER"]),
            "RIGHT_SHOULDER": convert_to_lowercase_xyz(frame["RIGHT_SHOULDER"]),
            "LEFT_ELBOW": convert_to_lowercase_xyz(frame["LEFT_ELBOW"]),
            "RIGHT_ELBOW": convert_to_lowercase_xyz(frame["RIGHT_ELBOW"])
        }

        # Convert to JSON
        json_data = json.dumps(pose_data)

        # Send over UDP
        sock.sendto(json_data.encode(), (UDP_IP, UDP_PORT))
        
        # print(f"Sent: {json_data}")
        time.sleep(frame_rate)  # Maintain real-time playback speed

if __name__ == '__main__':
    USE_LIVE_CAMERA = sys.argv[1].lower()
    print(f"pose_sender CALLED with: {sys.argv}")
    if (USE_LIVE_CAMERA == "true"):
        main(USE_LIVE_CAMERA)
    elif (USE_LIVE_CAMERA == "false"):
        main(USE_LIVE_CAMERA, sys.argv[2])  # sys.argv[2] is path to .mp4
    else:
        print("ERRROR, USAGE: python pose_sender.py [USE_LIVE_CAMERA bool] (PATH_TO_MP4_IF_NOT_LIVE)")
