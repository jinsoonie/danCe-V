import mediapipe as mp
import socket
import json
import time
import os
import sys
import string
# from simple_landmark_reader import SimplePoseLandmarkReader
import cv2
import numpy as np
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw
import collections
import threading

# Create a global flag to signal when video is done
reference_video_finished = False

# Declare sync flag (for comparison algo only to begin when Ref Avatar also start moving, i.e. spacebar from unity)
comparison_started = threading.Event()
def listen_for_start_signal(sock):
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            if data.decode().strip() == "START_COMPARISON":
                print("Python Received START signal from Unity! Beginning comparison...")
                comparison_started.set()
                break
        except:
            continue

# Create a function to handle only the reference video playback
def play_reference_video(video_path):
    global reference_video_finished
    video_cap = cv2.VideoCapture(video_path)
    if not video_cap.isOpened():
        print(f"Error: Could not open reference video at {video_path}")
        return
    
    fps = video_cap.get(cv2.CAP_PROP_FPS)
    frame_delay = int(1000 / fps)  # milliseconds
    print(f"Reference video FPS: {fps}, frame delay: {frame_delay}ms")
    
    cv2.namedWindow("Reference Video", cv2.WINDOW_NORMAL)
    
    while True:
        ret, frame = video_cap.read()
        if not ret:
            reference_video_finished = True
            break
            
        cv2.imshow("Reference Video", frame)
        
        # This is critical - this waitKey controls the playback speed
        # and also handles the window refresh
        key = cv2.waitKey(frame_delay) & 0xFF
        if key == ord('q'):
            break

    reference_video_finished = True
    video_cap.release()

# initialize MediaPipe Pose model
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils  # Drawing utility
mp_drawing_styles = mp.solutions.drawing_styles  # Styles
pose = mp_pose.Pose()

# json_to_analyze for akul/danny's json
script_dir = os.path.dirname(os.path.abspath(__file__))  # Get directory of the script
json_to_analyze = os.path.join(script_dir, "danny_poses.txt")  # full path
pose_filename = os.path.join(script_dir, "ref_mp4_pose_data.json")  # Save JSON in same directory


# when this script invoked, USE_LIVE_CAMERA is arg1, videoPath is arg2 (only used when arg1 = True), send_preformed_json is arg3 (for only sending .json to unity)
# SELECT WHICH MODE TO USE, USE_LIVE_CAMERA True is for live capture of user CV, False is for reference mp4 .json
ref_mp4_pose_data_list = []     # list to store ref_mp4_pose data (py list of jsons)

# Global variables for state management
live_buffer = collections.deque(maxlen=30)  # 30 frames = ~1 second at 30fps
last_analysis_time = 0
current_ref_position = 0
last_dtw_distance = float('inf')
last_matched_segment = 0
joint_similarity_scores = {}  # Store per-joint similarity scores

def normalize_pose(landmarks):
    """
    Normalize pose data to be invariant to position and scale, ignoring z-axis
    
    Args:
        landmarks: Dictionary of joint coordinates
        
    Returns:
        Dictionary of normalized joint coordinates
    """
    # Find the center point (midpoint between hips)
    if "LEFT_HIP" in landmarks and "RIGHT_HIP" in landmarks:
        center_x = (landmarks["LEFT_HIP"]["x"] + landmarks["RIGHT_HIP"]["x"]) / 2
        center_y = (landmarks["LEFT_HIP"]["y"] + landmarks["RIGHT_HIP"]["y"]) / 2
        
        # Calculate scale using torso height
        if "LEFT_SHOULDER" in landmarks and "RIGHT_SHOULDER" in landmarks:
            shoulder_y = (landmarks["LEFT_SHOULDER"]["y"] + landmarks["RIGHT_SHOULDER"]["y"]) / 2
            scale = abs(shoulder_y - center_y) * 2  # Torso height as scale
            if scale < 0.01:  # Avoid division by zero
                scale = 0.01
        else:
            scale = 0.2  # Default scale if shoulders not detected
            
        # Normalize all landmarks, ignoring z coordinate
        normalized = {}
        for joint, coords in landmarks.items():
            normalized[joint] = {
                "x": (coords["x"] - center_x) / scale,
                "y": (coords["y"] - center_y) / scale,
                "z": coords["z"]  # Keep z as is, it will be ignored in feature extraction
            }
        return normalized
    return landmarks  # Return original if normalization not possible

def load_reference_data(reference_json_path):
    """Load reference pose data from JSON file"""
    with open(reference_json_path, 'r') as f:
        return json.load(f)

def get_joint_groups():
    """
    Return a dictionary of joint groups for more meaningful feedback
    Each group contains related joints that work together
    """
    return {
        "arms": {
            "left": ["LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"],
            "right": ["RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"]
        },
        "legs": {
            "left": ["LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE"],
            "right": ["RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE"]
        },
        "torso": ["LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_HIP", "RIGHT_HIP"],
        "head": ["NOSE", "LEFT_EYE", "RIGHT_EYE", "LEFT_EAR", "RIGHT_EAR"]
    }

def get_all_landmarks():
    """Return a list of all landmarks to consider for comparison"""
    return [
        "NOSE", "LEFT_EYE", "RIGHT_EYE", "LEFT_EAR", "RIGHT_EAR",
        "LEFT_SHOULDER", "RIGHT_SHOULDER", 
        "LEFT_ELBOW", "RIGHT_ELBOW",
        "LEFT_WRIST", "RIGHT_WRIST",
        "LEFT_HIP", "RIGHT_HIP",
        "LEFT_KNEE", "RIGHT_KNEE",
        "LEFT_ANKLE", "RIGHT_ANKLE"
    ]

def extract_joint_features(pose_data, joint_name):
    """Extract features for a specific joint, ignoring z-axis"""
    # First normalize the pose data
    normalized_pose = normalize_pose(pose_data)
    
    if joint_name in normalized_pose:
        landmark = normalized_pose[joint_name] 
        # Only use x and y coordinates
        return np.array([landmark["x"], landmark["y"]])  
    return np.zeros(2)  # Return 2D zero vector since we're ignoring z

def extract_features(pose_data, landmark_list=None):
    """Extract relevant features from pose data for comparison, ignoring z-axis"""
    if landmark_list is None:
        landmark_list = get_all_landmarks()
    
    # First normalize the pose data
    normalized_pose = normalize_pose(pose_data)
    
    features = []
    for landmark_name in landmark_list:
        if landmark_name in normalized_pose:
            landmark = normalized_pose[landmark_name]
            # Only use x and y coordinates, ignore z
            features.extend([landmark["x"], landmark["y"]])
    
    return np.array(features)

def compute_joint_dtw(live_sequence, ref_sequence, joint_names):
    """
    Compute DTW distance for a specific joint or group of joints, ignoring z-axis
    
    Args:
        live_sequence: List of live frame data
        ref_sequence: List of reference frame data
        joint_names: List of joint names to compare
        
    Returns:
        Normalized DTW distance
    """
    # Extract features for specified joints only
    live_joint_seq = []
    ref_joint_seq = []
    
    for live_frame in live_sequence:
        live_features = extract_features(live_frame, joint_names)
        live_joint_seq.append(live_features)
    
    for ref_frame in ref_sequence:
        ref_features = extract_features(ref_frame, joint_names)
        ref_joint_seq.append(ref_features)
    
    # Compute DTW
    distance, path = fastdtw(np.array(live_joint_seq), np.array(ref_joint_seq), dist=euclidean)
    
    # Normalize by path length and number of features (2 per joint since we're ignoring z)
    normalized_distance = distance / (len(path) * len(joint_names) * 2)
    
    return normalized_distance

def analyze_window(live_buffer, reference_data, window_size=30, stride=1):
    """
    Analyze the current window against reference sequence with per-joint analysis
    
    Args:
        live_buffer: List of recent live frames (full pose data)
        reference_data: List of reference pose data frames
        window_size: Size of the comparison window
        stride: Number of frames to advance window for each analysis
        
    Returns:
        Dictionary with analysis results including per-joint scores
    """
    global current_ref_position, last_dtw_distance, last_matched_segment, joint_similarity_scores
    
    # First find the best matching segment based on overall pose
    best_distance = float('inf')
    best_position = 0
    
    # Use the expected position based on time elapsed
    # This assumes constant playback speed of the reference
    expected_position = current_ref_position
    
    # Search window in reference sequence
    search_start = max(0, expected_position - window_size)
    search_end = min(len(reference_data) - window_size, 
                     expected_position + window_size)
    
    # Extract live sequence from buffer (we need the full pose data)
    live_sequence = list(live_buffer)
    
    for i in range(search_start, search_end, stride):
        # Extract window from reference
        ref_window = reference_data[i:i+window_size]
        if len(ref_window) < window_size:
            continue
            
        # Get overall DTW distance first
        all_landmarks = get_all_landmarks()
        
        # Extract features for full comparison (all joints)
        live_features = [extract_features(frame, all_landmarks) for frame in live_sequence]
        ref_features = [extract_features(frame, all_landmarks) for frame in ref_window]
        
        # Compute overall DTW
        distance, path = fastdtw(np.array(live_features), np.array(ref_features), dist=euclidean)
        normalized_distance = distance / len(path)
        
        # Update best match
        if normalized_distance < best_distance:
            best_distance = normalized_distance
            best_position = i
    
    # Now that we found the best matching segment, analyze individual joints
    if best_position != 0:  # Make sure we found a match
        ref_best_window = reference_data[best_position:best_position+window_size]
        
        # Get joint groups
        joint_groups = get_joint_groups()
        
        # Analyze each joint group
        group_scores = {}
        
        # Analyze individual joints first
        individual_joints = []
        for group in joint_groups.values():
            if isinstance(group, dict):
                for subgroup in group.values():
                    individual_joints.extend(subgroup)
            else:
                individual_joints.extend(group)
        
        # De-duplicate joints
        individual_joints = list(set(individual_joints))
        
        # Calculate per-joint scores
        joint_scores = {}
        for joint in individual_joints:
            joint_dtw = compute_joint_dtw(live_sequence, ref_best_window, [joint])
            similarity = max(0, 100 - (joint_dtw * (100/0.3)))
            similarity = min(100, similarity)  # Cap at 100
            joint_scores[joint] = similarity
        
        # Calculate group scores based on individual joints
        for group_name, group_data in joint_groups.items():
            if isinstance(group_data, dict):
                # This is a group with subgroups
                group_scores[group_name] = {}
                for subgroup_name, joints in group_data.items():
                    subgroup_score = sum(joint_scores[j] for j in joints) / len(joints)
                    group_scores[group_name][subgroup_name] = subgroup_score
            else:
                # This is a simple group
                group_score = sum(joint_scores[j] for j in group_data) / len(group_data)
                group_scores[group_name] = group_score
        
        # Store for later use
        joint_similarity_scores = {
            "individual": joint_scores,
            "groups": group_scores
        }
    
    # Update current position and score
    current_ref_position = current_ref_position + stride
    last_dtw_distance = best_distance
    last_matched_segment = best_position
    
    # Return analysis results
    return get_current_analysis()

def get_current_analysis():
    """Get the latest analysis results including per-joint feedback"""
    global last_dtw_distance, last_matched_segment, current_ref_position, joint_similarity_scores
    
    # Calculate overall similarity score (0-100 scale)
    threshold = 1.5
    overall_similarity = max(0, 100 - (last_dtw_distance * (100/threshold)))
    overall_similarity = min(100, overall_similarity)  # Cap at 100
    
    # Check if dancer is ahead or behind
    timing_diff = current_ref_position - last_matched_segment
    
    # Find problem areas (joints with low scores)
    problem_areas = []
    improvement_suggestions = {}
    
    if joint_similarity_scores:
        # Find joints with similarity below threshold
        individual_scores = joint_similarity_scores.get("individual", {})
        
        # Get the worst performing joints
        worst_joints = sorted(individual_scores.items(), key=lambda x: x[1])[:3]
        for joint, score in worst_joints:
            if score < 70:  # Only include problematic joints
                problem_areas.append(joint)
        
        # Create improvement suggestions based on group scores
        group_scores = joint_similarity_scores.get("groups", {})
        
        # Check arms
        arms = group_scores.get("arms", {})
        if isinstance(arms, dict):
            left_arm = arms.get("left", 100)
            right_arm = arms.get("right", 100)
            
            if left_arm < 60:
                improvement_suggestions["left_arm"] = "Work on left arm movement and positioning"
            if right_arm < 60:
                improvement_suggestions["right_arm"] = "Work on right arm movement and positioning"
        
        # Check legs
        legs = group_scores.get("legs", {})
        if isinstance(legs, dict):
            left_leg = legs.get("left", 100)
            right_leg = legs.get("right", 100)
            
            if left_leg < 60:
                improvement_suggestions["left_leg"] = "Improve left leg movement and positioning"
            if right_leg < 60:
                improvement_suggestions["right_leg"] = "Improve right leg movement and positioning"
        
        # Check torso
        torso = group_scores.get("torso", 100)
        if torso < 60:
            improvement_suggestions["torso"] = "Focus on core body positioning and stability"
            
        # Check head
        head = group_scores.get("head", 100)
        if head < 60:
            improvement_suggestions["head"] = "Pay attention to head positioning"
    
    return {
        "overall_similarity": overall_similarity,
        "reference_position": last_matched_segment,
        "timing_difference": timing_diff,
        "dtw_distance": last_dtw_distance,
        "joint_scores": joint_similarity_scores,
        "problem_areas": problem_areas,
        "improvement_suggestions": improvement_suggestions
    }

# def add_live_frame(pose_data, reference_data, analysis_interval=0.5):
#     """
#     Add a new frame from live video to the buffer and analyze if needed
    
#     Args:
#         pose_data: Current frame's pose data
#         reference_data: Full reference sequence data
#         analysis_interval: How often to run analysis (in seconds)
        
#     Returns:
#         Dictionary with analysis results or None if not analyzed
#     """
#     global live_buffer, last_analysis_time
    
#     # Add frame to buffer
#     live_buffer.append(pose_data)
    
#     # Perform analysis if enough time has passed
#     current_time = time.time()
#     if current_time - last_analysis_time >= analysis_interval and len(live_buffer) >= live_buffer.maxlen:
#         last_analysis_time = current_time
#         return analyze_window(live_buffer, reference_data)
        
#     return get_current_analysis()

# modified to run analysis in the background, else too slow on live webcam for add_live_frame
analysis_result = None
analysis_running = False

def background_analysis(reference_data):
    global analysis_result, analysis_running
    print("BACKGROUND ANALYSIS RUNNING")
    analysis_result = analyze_window(live_buffer, reference_data)
    analysis_running = False

# add_live_frame's analysis interval increased, 0.1 -> 0.8
def add_live_frame(pose_data, reference_data, analysis_interval=0.8):
    global live_buffer, last_analysis_time, analysis_result, analysis_running

    # Add frame to buffer
    live_buffer.append(pose_data)
    
    # Perform analysis if enough time has passed
    current_time = time.time()
    if current_time - last_analysis_time >= analysis_interval and len(live_buffer) >= live_buffer.maxlen:
        last_analysis_time = current_time
        analysis_running = True
        threading.Thread(target=background_analysis, args=(reference_data,)).start()
        
    return analysis_result or get_current_analysis()


def get_score_color(score):
    if score > 80: return (0, 255, 0)
    elif score > 60: return (0, 255, 255)
    elif score > 40: return (0, 165, 255)
    else: return (0, 0, 255)

def visualize_comparison(frame, comparison_data):
    """Display detailed comparison metrics on the frame"""
    if not comparison_data:
        return frame
        
    # Overall similarity
    similarity = comparison_data.get("overall_similarity", 0)
    color = (0, 255, 0) if similarity > 70 else (0, 165, 255) if similarity > 40 else (0, 0, 255)
    cv2.putText(frame, f"Overall: {similarity:.1f}%", (10, 30), 
              cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
    # Timing with more sensitive thresholds
    timing_diff = comparison_data.get("timing_difference", 0)
    timing_text = "On time"
    if timing_diff < -5:  # If negative, you're BEHIND
        timing_text = "Behind"
    elif timing_diff > 5:  # If positive, you're AHEAD
        timing_text = "Ahead"       
    
    # Add color coding for timing
    if timing_text == "On time":
        timing_color = (0, 255, 0)  # Green
    elif timing_text == "Behind":
        timing_color = (0, 0, 255)  # Red
    else:  # Ahead
        timing_color = (255, 165, 0)  # Orange
        
    cv2.putText(frame, f"Timing: {timing_text} ({timing_diff})", (10, 60),
              cv2.FONT_HERSHEY_SIMPLEX, 0.8, timing_color, 2)
              
    # Display problem areas
    problem_areas = comparison_data.get("problem_areas", [])
    if problem_areas:
        areas_text = "Improve: " + ", ".join([p.split('_')[0] for p in problem_areas[:3]])
        cv2.putText(frame, areas_text, (10, 90),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    # Display improvement suggestions (only one at a time to avoid cluttering)
    suggestions = comparison_data.get("improvement_suggestions", {})
    if suggestions:
        # Get a random suggestion to display (changes every frame)
        import random
        suggestion_key = random.choice(list(suggestions.keys()))
        suggestion_text = suggestions[suggestion_key]
        cv2.putText(frame, suggestion_text, (10, 120),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    # Add group scores on the right side of the frame
    joint_scores = comparison_data.get("joint_scores", {})
    group_scores = joint_scores.get("groups", {})
    
    y_offset = 30
    for group_name, score in group_scores.items():
        if isinstance(score, dict):
            # This is a group with subgroups
            for subgroup_name, subscore in score.items():
                display_name = f"{group_name.title()} ({subgroup_name})"
                color = get_score_color(subscore)
                cv2.putText(frame, f"{display_name}: {subscore:.1f}%", 
                          (frame.shape[1] - 250, y_offset),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                y_offset += 25
        else:
            # This is a simple group score
            color = get_score_color(score)
            cv2.putText(frame, f"{group_name.title()}: {score:.1f}%", 
                      (frame.shape[1] - 250, y_offset),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_offset += 25
    
    return frame


def main(USE_LIVE_CAMERA, videoPath="", send_preformed_json=False):
    # configure UDP socket
    UDP_IP = "127.0.0.1"    # local host IP as assume running on same device
    UDP_PORT = None         # default value None (if UDP_PORT is none later, failed to init port)
    TEST_MESSAGE = "Hello Unity from Python pose_sender.py!"

    print(f"message: {TEST_MESSAGE}")

    # init UDP socket
    sock = socket.socket(socket.AF_INET,    # INTERNET
                        socket.SOCK_DGRAM)  # UDP
    
    # Load reference data if needed for comparison
    reference_data = None
    if USE_LIVE_CAMERA == "true" and os.path.exists(pose_filename):
        print("Loading reference data for DTW comparison...")
        reference_data = load_reference_data(pose_filename)
    
    if USE_LIVE_CAMERA == "true":
        print(f"Running in REAL-TIME mode (Live Camera)... Press 'q' to quit. Ref video on {videoPath}")

        # assign UDP_PORT for pose_receiver_script_right_live
        UDP_PORT = 5005

        # Open webcam for live feed window
        cap = cv2.VideoCapture(0)  # 0 = Default webcam


        # UNCOMMENT THIS SECTION FOR START SIGNAL SYNC from Unity (ref avatar sync)
        # Create a separate socket bound to port 5010 just for listening for the START_SIGNAL from unity launch_two_avatar_controller
        control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        control_sock.bind(("127.0.0.1", 5010))  # New control port

        listener_thread = threading.Thread(target=listen_for_start_signal, args=(control_sock,))
        listener_thread.daemon = True
        listener_thread.start()

        # Start reference video in a separate thread
        video_thread = threading.Thread(target=play_reference_video, args=(videoPath,))
        video_thread.daemon = True
        video_thread.start()

    else:
        print("Running in REPLAY mode...")

        # assign UDP_PORT for pose_receiver_script_left_ref
        UDP_PORT = 5006

        # if send_preformed_json, then only run send_preformed_json and prematurely end main func
        if (str(send_preformed_json).lower() == "true"):
            print(f"Sending Preformed .json selected... taking {pose_filename} and sending to {UDP_PORT} in Unity")
            # func here just to decode json and send frames
            send_json_to_unity(pose_filename, sock, UDP_IP, UDP_PORT)
            return

        # Open videoPath .mp4
        cap = cv2.VideoCapture(videoPath)
        video_cap = None

    print(f"Opening cap with UDP_PORT: {UDP_PORT}...")

    # make window resizable
    cv2.namedWindow("Live/Video Pose Tracking", cv2.WINDOW_NORMAL)

    # TEMP ADDED FOR FASTER PROCESSING (TEMP)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_skip = 2  # Process every 2nd frame, for example

    # based on USE_LIVE_CAMERA, run CV on live feed or videoPath .mp4
    while cap.isOpened() or video_cap.isOpened():

        if USE_LIVE_CAMERA == "true" and reference_video_finished:
            print("Reference video finished, terminating program")
            break

        start_time = time.time()    # ADDED for fps matching on stream

        ret, frame = cap.read()
        # If either reached end of .mp4 OR Live Camera Feed Ended
        if not ret:
            print("End of video or Live Camera feed lost!")
            break

        # TEMP ADDED FOR FASTER PROCESSING (TEMP)
        frame_id = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        # if frame_id % frame_skip != 0 and USE_LIVE_CAMERA == "false":
        #     continue

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

            # If in REPLAY mode, add to reference data
            # if USE_LIVE_CAMERA == "false":
            ref_mp4_pose_data_list.append(landmarks_data)
            
            # If in LIVE mode and reference data exists, perform DTW comparison (ONLY when Unity triggers via spacebar)
            comparison_data = {}
            if USE_LIVE_CAMERA == "true" and reference_data and comparison_started.is_set():
                # print("how much processing??")
                # comparison_data = add_live_frame(landmarks_data, reference_data)
                # Visualize comparison on frame with enhanced per-joint feedback
                frame = visualize_comparison(frame, comparison_data)

            # Combine pose data with comparison results
            combined_data = {
                "pose": landmarks_data,
                "comparison": comparison_data
            }

            # Convert to JSON string
            pose_json = json.dumps(combined_data)

            # Send pose data over UDP directly to Unity
            sock.sendto(pose_json.encode(), (UDP_IP, UDP_PORT))

        # Show video output
        cv2.imshow("Live/Video Pose Tracking", frame)


        # Capture at ~30 fps, Reduce CPU usage
        # time.sleep(1/30)  # ~30 FPS

        # temp added for matching FPS with OG .mp4
        # elapsed = time.time() - start_time
        # sleep_time = max(0, adjusted_frame_duration - elapsed)
        # time.sleep(sleep_time)

        # Quit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting live mode...")
            break

    # Save to JSON file for later use (if reference .mp4 version)
    if USE_LIVE_CAMERA == "false":
        with open(pose_filename, "w") as f:
            json.dump(ref_mp4_pose_data_list, f, indent=4)

        print(f"Pose data saved to {os.path.abspath(pose_filename)}")

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("Camera closed properly.")

def send_json_to_unity(pose_filename, sock, UDP_IP, UDP_PORT):
    """
    Load a JSON file containing a list of pose frames and send selected keypoints to Unity over UDP.
    
    Args:
        pose_filename (str): Path to the JSON file.
        sock (socket.socket): The UDP socket used for transmission.
        UDP_IP (str): The target IP address.
        UDP_PORT (int): The target UDP port.
    """
    # Load the saved pose frames from the JSON file
    with open(pose_filename, "r") as f:
        frames = json.load(f)

    frame_rate = 1 / 30  # Simulate ~30 FPS
    for frame in frames:
        # Extract only the required keypoints, converting their coordinate dicts
        pose_data = {
            "LEFT_WRIST": frame.get("LEFT_WRIST", {}),
            "RIGHT_WRIST": frame.get("RIGHT_WRIST", {}),
            "LEFT_ANKLE": frame.get("LEFT_ANKLE", {}),
            "RIGHT_ANKLE": frame.get("RIGHT_ANKLE", {}),
            "NOSE": frame.get("NOSE", {}),
            "LEFT_HIP": frame.get("LEFT_HIP", {}),
            "RIGHT_HIP": frame.get("RIGHT_HIP", {}),
            "LEFT_SHOULDER": frame.get("LEFT_SHOULDER", {}),
            "RIGHT_SHOULDER": frame.get("RIGHT_SHOULDER", {}),
            "LEFT_ELBOW": frame.get("LEFT_ELBOW", {}),
            "RIGHT_ELBOW": frame.get("RIGHT_ELBOW", {})
        }
        
        # Convert the selected keypoints to a JSON string
        json_data = json.dumps(pose_data)
        
        # Send the JSON string over UDP
        sock.sendto(json_data.encode(), (UDP_IP, UDP_PORT))
        
        # Optional: uncomment for debugging
        # print(f"Sent: {json_data}")
        
        # Sleep to simulate real-time playback (~30 FPS)
        time.sleep(frame_rate)

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
    if (USE_LIVE_CAMERA == "true"): # even if called with USE_LIVE_CAMERA=true, need to include path to ref .mp4 (dannys ver)
        main(USE_LIVE_CAMERA, sys.argv[2]) #, sys.argv[3])
    elif (USE_LIVE_CAMERA == "false"):
        main(USE_LIVE_CAMERA, sys.argv[2], sys.argv[3])  # sys.argv[2] is path to .mp4, sys.argv[3] is send_preformed_json
    else:
        print("ERRROR, USAGE: python pose_sender.py [USE_LIVE_CAMERA bool] (PATH_TO_MP4_IF_NOT_LIVE) (SEND_PREFORMED_JSON_IF_NOT_LIVE)")
