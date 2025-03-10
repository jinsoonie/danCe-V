import json
import numpy as np
import pandas as pd
import os
from pprint import pprint

class SimplePoseLandmarkReader:
    """
    A simple class to read and access pose landmark JSON data produced by the MediaPipe pose detection system.
    Provides easy access to the landmark data with minimal processing.
    """
    
    def __init__(self):
        """Initialize the reader with empty data structures."""
        self.data = {}  # Dictionary to store all loaded landmark data
        self.dataframes = {}  # Dictionary to store pandas DataFrame representations if needed
    
    def load_json(self, filepath, dataset_name=None):
        """
        Load landmark data from a JSON file.
        
        Args:
            filepath (str): Path to the JSON file
            dataset_name (str, optional): Name to identify this dataset. Defaults to the filename.
        
        Returns:
            bool: True if loading was successful, False otherwise
        """
        if dataset_name is None:
            dataset_name = os.path.splitext(os.path.basename(filepath))[0]
        
        try:
            with open(filepath, 'r') as f:
                json_data = json.load(f)
            
            print(f"Loaded {len(json_data)} frames from {filepath}")
            self.data[dataset_name] = json_data
            return True
        except Exception as e:
            print(f"Error loading JSON file {filepath}: {e}")
            return False
    
    def list_datasets(self):
        """List all loaded datasets."""
        return list(self.data.keys())
    
    def get_frame_count(self, dataset_name):
        """Get the number of frames in a dataset."""
        if dataset_name not in self.data:
            print(f"Dataset {dataset_name} not found")
            return 0
        return len(self.data[dataset_name])
    
    def get_frame(self, dataset_name, frame_idx):
        """
        Get all data for a specific frame.
        
        Args:
            dataset_name (str): Name of the dataset
            frame_idx (int): Frame index
        
        Returns:
            dict: The complete frame data, or None if not found
        """
        if dataset_name not in self.data:
            print(f"Dataset {dataset_name} not found")
            return None
        
        # Find the frame data
        frame_data = next((f for f in self.data[dataset_name] if f["frame"] == frame_idx), None)
        if frame_data is None:
            # Try by array index if frame index is not found
            try:
                if 0 <= frame_idx < len(self.data[dataset_name]):
                    return self.data[dataset_name][frame_idx]
                else:
                    print(f"Frame index {frame_idx} out of range for dataset {dataset_name}")
                    return None
            except:
                print(f"Frame {frame_idx} not found in dataset {dataset_name}")
                return None
            
        return frame_data
    
    def get_pose_landmarks(self, dataset_name, frame_idx, pose_id=0):
        """
        Get pose landmarks for a specific frame and pose.
        
        Args:
            dataset_name (str): Name of the dataset
            frame_idx (int): Frame index
            pose_id (int, optional): Pose ID if multiple people in frame. Defaults to 0.
        
        Returns:
            dict: Dictionary of landmark data, or None if not found
        """
        frame_data = self.get_frame(dataset_name, frame_idx)
        if frame_data is None:
            return None
        
        # Find the pose data
        pose_data = next((p for p in frame_data["poses"] if p["pose_id"] == pose_id), None)
        if pose_data is None:
            print(f"Pose ID {pose_id} not found in frame {frame_idx} of dataset {dataset_name}")
            return None
        
        return pose_data["landmarks"]
    
    def get_landmark_position(self, dataset_name, frame_idx, landmark_name, pose_id=0):
        """
        Get the position of a specific landmark in a specific frame.
        
        Args:
            dataset_name (str): Name of the dataset
            frame_idx (int): Frame index
            landmark_name (str): Name of the landmark (e.g., 'NOSE')
            pose_id (int, optional): Pose ID if multiple people in frame. Defaults to 0.
        
        Returns:
            dict: The landmark position with x, y, z coordinates, or None if not found
        """
        landmarks = self.get_pose_landmarks(dataset_name, frame_idx, pose_id)
        if landmarks is None:
            return None
        
        if landmark_name not in landmarks:
            print(f"Landmark {landmark_name} not found in frame {frame_idx} of dataset {dataset_name}")
            return None
        
        return landmarks[landmark_name]
    
    def convert_to_dataframe(self, dataset_name):
        """
        Convert a dataset to a pandas DataFrame for easier analysis if needed.
        
        Args:
            dataset_name (str): Name of the dataset
        
        Returns:
            pd.DataFrame: The DataFrame, or None if conversion fails
        """
        if dataset_name not in self.data:
            print(f"Dataset {dataset_name} not found")
            return None
        
        rows = []
        for frame_data in self.data[dataset_name]:
            frame_idx = frame_data["frame"]
            
            # Process each pose in the frame (usually just one)
            for pose in frame_data["poses"]:
                pose_id = pose["pose_id"]
                landmarks = pose["landmarks"]
                
                # Create a row for each frame-pose combination
                row = {
                    "frame": frame_idx,
                    "pose_id": pose_id
                }
                
                # Add all landmark coordinates
                for landmark_name, coords in landmarks.items():
                    row[f"{landmark_name}_x"] = coords["x"]
                    row[f"{landmark_name}_y"] = coords["y"]
                    row[f"{landmark_name}_z"] = coords["z"]
                    if "visibility" in coords and coords["visibility"] is not None:
                        row[f"{landmark_name}_visibility"] = coords["visibility"]
                
                rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        self.dataframes[dataset_name] = df
        print(f"Created DataFrame with {len(df)} rows for dataset {dataset_name}")
        return df
    
    def export_to_csv(self, dataset_name, output_filepath):
        """
        Export a dataset to CSV format.
        
        Args:
            dataset_name (str): Name of the dataset to export
            output_filepath (str): Path to save the CSV file
        
        Returns:
            bool: True if export was successful, False otherwise
        """
        if dataset_name not in self.data:
            print(f"Dataset {dataset_name} not found")
            return False
        
        # Convert to DataFrame if not already done
        if dataset_name not in self.dataframes:
            df = self.convert_to_dataframe(dataset_name)
            if df is None:
                return False
        else:
            df = self.dataframes[dataset_name]
        
        try:
            df.to_csv(output_filepath, index=False)
            print(f"Dataset {dataset_name} exported to {output_filepath}")
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Create reader
    reader = SimplePoseLandmarkReader()
    
    # Load data
    reference_json = "reference_pose_landmarks.json"
    test_json = "test_pose_landmarks.json"
    normalized_json = "normalized_test_landmarks.json"
    
    # Try to load the files
    files_to_load = [
        (reference_json, "reference"),
        (test_json, "test"),
        (normalized_json, "normalized")
    ]
    
    loaded_files = []
    for file_path, name in files_to_load:
        if os.path.exists(file_path):
            success = reader.load_json(file_path, name)
            if success:
                loaded_files.append(name)
                print(f"Loaded {name} dataset")
    
    if not loaded_files:
        print("No data files found. Please make sure the JSON files are in the current directory.")
        print("Expecting files named:")
        for file_path, _ in files_to_load:
            print(f"  - {file_path}")
        exit(1)
    
    print("\nAvailable datasets:", reader.list_datasets())
    
    # Show sample usage
    if loaded_files:
        dataset = loaded_files[0]  # Use the first loaded dataset
        
        print(f"\nSample usage for dataset '{dataset}':")
        print("\n1. Get the number of frames:")
        frame_count = reader.get_frame_count(dataset)
        print(f"   Number of frames: {frame_count}")
        
        if frame_count > 0:
            print("\n2. Get data for frame 0:")
            frame_data = reader.get_frame(dataset, 0)
            print(f"   Frame index: {frame_data['frame']}")
            print(f"   Number of poses: {len(frame_data['poses'])}")
            
            print("\n3. Get landmarks for pose 0 in frame 0:")
            landmarks = reader.get_pose_landmarks(dataset, 0, 0)
            print(f"   Number of landmarks: {len(landmarks)}")
            
            print("\n4. Get position of the NOSE landmark in frame 0:")
            nose_pos = reader.get_landmark_position(dataset, 0, "NOSE", 0)
            print(f"   NOSE position: x={nose_pos['x']:.4f}, y={nose_pos['y']:.4f}, z={nose_pos['z']:.4f}")
            
            print("\n5. Convert dataset to DataFrame and show first few rows:")
            print("   (This can be useful for pandas-based analysis)")
            df = reader.convert_to_dataframe(dataset)
            print(df.head())
