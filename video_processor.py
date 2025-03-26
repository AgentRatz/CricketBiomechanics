import cv2
import numpy as np
import mediapipe as mp
import streamlit as st

# Initialize MediaPipe Pose model
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Pose model for processing
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=2,
    enable_segmentation=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def extract_frames(video_path, max_frames=300):
    """
    Extract frames from a video file
    
    Args:
        video_path (str): Path to video file
        max_frames (int): Maximum number of frames to extract
        
    Returns:
        tuple: (list of frames, fps)
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            st.error("Error opening video file")
            return [], 0
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame sampling rate if there are too many frames
        sample_every = max(1, total_frames // max_frames)
        
        frames = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Only process every nth frame if needed
            if frame_count % sample_every == 0:
                # Convert from BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
            
            frame_count += 1
        
        cap.release()
        
        st.info(f"Extracted {len(frames)} frames from video at {fps:.2f} fps")
        return frames, fps
    
    except Exception as e:
        st.error(f"Error processing video: {str(e)}")
        return [], 0

def process_frame(frame):
    """
    Process a single frame with MediaPipe Pose model
    
    Args:
        frame (numpy.ndarray): Input frame in RGB format
        
    Returns:
        tuple: (processed frame with landmarks drawn, pose landmarks)
    """
    try:
        # Make a copy of the frame for drawing
        output_frame = frame.copy()
        
        # Get image dimensions
        height, width = frame.shape[:2]
        
        # Print frame information for debugging
        print(f"Processing frame: shape={frame.shape}, dtype={frame.dtype}, min={np.min(frame)}, max={np.max(frame)}")
        
        # Process the frame with MediaPipe
        # The frame is already in the correct format for MediaPipe Pose
        results = pose.process(frame)
        
        # Check if pose landmarks were detected
        if results and results.pose_landmarks:
            # Draw the pose landmarks on the frame
            mp_drawing.draw_landmarks(
                output_frame, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )
            
            # Return the processed frame and the landmarks
            return output_frame, results.pose_landmarks
        else:
            # Return the original frame if no landmarks were detected
            print("No pose landmarks detected in frame")
            return output_frame, None
            
    except Exception as e:
        print(f"Error processing frame: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Return the original frame on error
        if frame is not None:
            return frame.copy(), None
        else:
            # Create a blank frame if input is None
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            return blank_frame, None

def crop_frame_to_person(frame, landmarks, padding=50):
    """
    Crop frame to the area containing the person
    
    Args:
        frame (numpy.ndarray): Input frame
        landmarks: MediaPipe pose landmarks
        padding (int): Padding around the person
        
    Returns:
        numpy.ndarray: Cropped frame
    """
    if landmarks is None:
        return frame
    
    h, w = frame.shape[:2]
    
    # Get the bounding box of the person
    x_min = w
    y_min = h
    x_max = 0
    y_max = 0
    
    for landmark in landmarks.landmark:
        x, y = int(landmark.x * w), int(landmark.y * h)
        x_min = min(x_min, x)
        y_min = min(y_min, y)
        x_max = max(x_max, x)
        y_max = max(y_max, y)
    
    # Add padding
    x_min = max(0, x_min - padding)
    y_min = max(0, y_min - padding)
    x_max = min(w, x_max + padding)
    y_max = min(h, y_max + padding)
    
    # Crop the frame
    cropped_frame = frame[y_min:y_max, x_min:x_max]
    
    return cropped_frame

def get_landmark_coordinates(landmarks, frame_shape):
    """
    Get the x, y coordinates of pose landmarks
    
    Args:
        landmarks: MediaPipe pose landmarks
        frame_shape: Shape of the frame (height, width)
        
    Returns:
        dict: Dictionary of landmark coordinates
    """
    if landmarks is None:
        return None
    
    h, w = frame_shape[:2]
    coords = {}
    
    # Extract coordinates for each landmark
    for idx, landmark in enumerate(landmarks.landmark):
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        visibility = landmark.visibility
        coords[idx] = {
            'x': x, 
            'y': y, 
            'visibility': visibility
        }
    
    return coords
