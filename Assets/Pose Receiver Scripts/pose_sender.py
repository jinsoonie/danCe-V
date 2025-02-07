import socket
import json

# configure UDP socket
UDP_IP = "127.0.0.1"    # local host IP as assume running on same device
UDP_PORT = 5005         # as specified in Unity pose_receiver_script
TEST_MESSAGE = "Hello Unity from Python!"


print(f"message: {TEST_MESSAGE}")

# init UDP socket
sock = socket.socket(socket.AF_INET,    # INTERNET
                     socket.SOCK_DGRAM) # UDP

# test sending message - works
# sock.sendto(TEST_MESSAGE.encode(), (UDP_IP, UDP_PORT))

# while True:
pose_data = {"x": 0.5, "y": 1.0, "z": 0.0}  # Example (Replace with real tracking)
sock.sendto(json.dumps(pose_data).encode(), (UDP_IP, UDP_PORT))

