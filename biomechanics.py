import numpy as np
import pandas as pd
import math
from collections import defaultdict

def calculate_angle(a, b, c):
    """
    Calculate the angle between three points
    
    Args:
        a (tuple): First point (x, y)
        b (tuple): Middle point (x, y) - the vertex
        c (tuple): Third point (x, y)
        
    Returns:
        float: Angle in degrees
    """
    ang = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
    return ang + 360 if ang < 0 else ang

def extract_biomechanics(landmarks, frame_shape):
    """
    Extract biomechanical measurements from pose landmarks
    
    Args:
        landmarks: MediaPipe pose landmarks
        frame_shape: Shape of the frame (height, width)
        
    Returns:
        dict: Dictionary of biomechanical measurements
    """
    try:
        if landmarks is None:
            print("No landmarks provided to extract_biomechanics")
            return None
        
        h, w = frame_shape[:2]
        
        # Initialize landmark coordinates with safe defaults
        landmark_coords = {}
        
        # Function to safely extract landmark coordinates
        def get_landmark_safely(landmark_idx):
            try:
                if landmark_idx >= len(landmarks.landmark):
                    print(f"Landmark index {landmark_idx} out of range")
                    return (0, 0)
                
                landmark = landmarks.landmark[landmark_idx]
                if not hasattr(landmark, 'visibility') or landmark.visibility < 0.5:
                    print(f"Landmark {landmark_idx} has low visibility")
                    return (0, 0)
                
                return (landmark.x * w, landmark.y * h)
            except Exception as e:
                print(f"Error extracting landmark {landmark_idx}: {str(e)}")
                return (0, 0)
        
        # Extract key landmark coordinates with safety checks
        # Shoulder landmarks
        left_shoulder = get_landmark_safely(11)
        right_shoulder = get_landmark_safely(12)
        
        # Elbow landmarks
        left_elbow = get_landmark_safely(13)
        right_elbow = get_landmark_safely(14)
        
        # Wrist landmarks
        left_wrist = get_landmark_safely(15)
        right_wrist = get_landmark_safely(16)
        
        # Hip landmarks
        left_hip = get_landmark_safely(23)
        right_hip = get_landmark_safely(24)
    
        # Knee landmarks
        left_knee = get_landmark_safely(25)
        right_knee = get_landmark_safely(26)
    
        # Ankle landmarks
        left_ankle = get_landmark_safely(27)
        right_ankle = get_landmark_safely(28)
    
        # Calculate biomechanical measurements
        
        # Arm angle (shoulder-elbow-wrist)
        # For right-handed bowlers, use right arm
        # For left-handed bowlers, would need to detect and use left arm
        bowling_arm_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
        
        # Wrist angle (elbow-wrist-index finger)
        # Approximating using the elbow-wrist vector and assuming wrist extension
        wrist_angle = 180 - abs(bowling_arm_angle - 180)
        
        # Trunk angle (shoulder-hip vertical alignment)
        # Vertical alignment of shoulders relative to hips
        trunk_angle = np.rad2deg(np.arctan2(
            abs(right_shoulder[0] - right_hip[0]),
            abs(right_shoulder[1] - right_hip[1])
        ))
        
        # Front knee angle (hip-knee-ankle)
        front_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
        
        # Back knee angle
        back_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
        
        # Shoulder rotation (estimated from shoulder alignment)
        shoulder_rotation = np.rad2deg(np.arctan2(
            right_shoulder[1] - left_shoulder[1],
            right_shoulder[0] - left_shoulder[0]
        ))
        
        # Hip-shoulder separation (difference in alignment between hips and shoulders)
        hip_alignment = np.rad2deg(np.arctan2(
            right_hip[1] - left_hip[1],
            right_hip[0] - left_hip[0]
        ))
        hip_shoulder_separation = abs(shoulder_rotation - hip_alignment)
        
        # Release point - using wrist position
        release_point_height = right_wrist[1] / h  # Normalized by frame height
        release_point_horizontal = right_wrist[0] / w  # Normalized by frame width
        
        # Return all biomechanical measurements
        return {
            'arm_angle': bowling_arm_angle,
            'wrist_angle': wrist_angle,
            'trunk_angle': trunk_angle,
            'front_knee_angle': front_knee_angle,
            'back_knee_angle': back_knee_angle,
            'shoulder_rotation': shoulder_rotation,
            'hip_shoulder_separation': hip_shoulder_separation,
            'release_point_height': release_point_height,
            'release_point_horizontal': release_point_horizontal,
            'shoulder_coordinates': {
                'left': left_shoulder,
                'right': right_shoulder
            },
            'elbow_coordinates': {
                'left': left_elbow,
                'right': right_elbow
            },
            'wrist_coordinates': {
                'left': left_wrist,
                'right': right_wrist
            }
        }
    except Exception as e:
        print(f"Error in extract_biomechanics: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def extract_time_series_data(processed_results):
    """
    Extract time series data from processed frames
    
    Args:
        processed_results: List of processed frame results
        
    Returns:
        dict: Dictionary of time series data for each biomechanical measurement
    """
    # Initialize time series data structure
    time_series = defaultdict(list)
    
    # Extract biomechanical data from each frame
    for result in processed_results:
        if result['biomechanics']:
            for key, value in result['biomechanics'].items():
                # Only add scalar values to time series
                if isinstance(value, (int, float)):
                    time_series[key].append(value)
    
    # Convert to regular dictionary with numpy arrays
    for key in time_series:
        time_series[key] = np.array(time_series[key])
    
    return dict(time_series)

def identify_bowling_phases(processed_results):
    """
    Identify key phases in the bowling action
    
    Args:
        processed_results: List of processed frame results
        
    Returns:
        dict: Dictionary of key phases and their frame indices
    """
    # Initialize phases with None values
    phases = {
        'Run-up': None,
        'Loading': None,
        'Delivery Stride': None,
        'Release': None,
        'Follow Through': None
    }
    
    # Safety check for empty or invalid data
    if not processed_results:
        print("No processed results provided to identify_bowling_phases")
        return phases
    
    # Verify frames have biomechanics data
    valid_frames = []
    for i, result in enumerate(processed_results):
        # Check that the structure includes biomechanics
        if result and 'biomechanics' in result and result['biomechanics'] is not None:
            valid_frames.append(i)
    
    if not valid_frames:
        print("No valid frames with biomechanics data found")
        return phases
    
    # Extract arm angles across frames
    arm_angles = []
    trunk_angles = []
    
    for i in valid_frames:
        result = processed_results[i]
        # Use get() with default to avoid KeyError
        if result['biomechanics'] and 'arm_angle' in result['biomechanics'] and 'trunk_angle' in result['biomechanics']:
            arm_angles.append((i, result['biomechanics']['arm_angle']))
            trunk_angles.append((i, result['biomechanics']['trunk_angle']))
    
    if not arm_angles or not trunk_angles:
        print("Could not extract arm or trunk angles from biomechanics data")
        return phases
    
    # Find run-up phase - early frames with relatively consistent arm angle
    if len(arm_angles) > 5:
        phases['Run-up'] = arm_angles[2][0]  # Use a frame near the beginning
    
    # Find loading phase - when trunk angle starts increasing
    trunk_angle_changes = [abs(trunk_angles[i+1][1] - trunk_angles[i][1]) 
                          for i in range(len(trunk_angles)-1)]
    
    if trunk_angle_changes:
        max_trunk_change_idx = trunk_angle_changes.index(max(trunk_angle_changes, default=0))
        if max_trunk_change_idx > 0:
            phases['Loading'] = trunk_angles[max_trunk_change_idx][0]
    
    # Find delivery stride - when arm angle starts decreasing rapidly
    arm_angle_changes = [arm_angles[i+1][1] - arm_angles[i][1] 
                        for i in range(len(arm_angles)-1)]
    
    if arm_angle_changes:
        min_arm_change_idx = arm_angle_changes.index(min(arm_angle_changes, default=0))
        if min_arm_change_idx > 0:
            phases['Delivery Stride'] = arm_angles[min_arm_change_idx][0]
    
    # Find release point - when arm angle is approximately 180 degrees
    release_candidates = [(i, abs(angle - 180)) for i, angle in arm_angles]
    if release_candidates:
        release_idx, _ = min(release_candidates, key=lambda x: x[1])
        phases['Release'] = release_idx
    
    # Find follow through - a few frames after release
    if phases['Release'] is not None:
        release_idx_in_list = [i for i, (frame_idx, _) in enumerate(arm_angles) 
                              if frame_idx == phases['Release']]
        
        if release_idx_in_list and release_idx_in_list[0] + 3 < len(arm_angles):
            phases['Follow Through'] = arm_angles[release_idx_in_list[0] + 3][0]
    
    return phases

def calculate_performance_metrics(biomechanics_data, processed_results):
    """
    Calculate performance metrics from biomechanical data
    
    Args:
        biomechanics_data: Dictionary of time series biomechanical data
        processed_results: List of processed frame results
        
    Returns:
        dict: Dictionary of performance metrics
    """
    if not biomechanics_data or not processed_results:
        return None
    
    metrics = {}
    
    # Find release frame
    phases = identify_bowling_phases(processed_results)
    release_frame = phases.get('Release')
    
    # Extract arm angle at release
    if release_frame is not None and 0 <= release_frame < len(processed_results):
        # Get biomechanics data safely
        release_biomechanics = processed_results[release_frame].get('biomechanics', None)
        if release_biomechanics:
            # Get metrics using get with defaults to avoid KeyError
            metrics['Arm Angle at Release'] = release_biomechanics.get('arm_angle', 0)
            metrics['Wrist Angle at Release'] = release_biomechanics.get('wrist_angle', 0)
            metrics['Release Height'] = release_biomechanics.get('release_point_height', 0) * 100  # As percentage of frame height
    
    # If we don't have release frame data, use the time series data
    if 'Arm Angle at Release' not in metrics and 'arm_angle' in biomechanics_data:
        # Estimate release point as the frame where arm angle is closest to 180 degrees
        arm_angles = biomechanics_data['arm_angle']
        if len(arm_angles) > 0:
            release_idx = np.argmin(np.abs(arm_angles - 180))
            metrics['Arm Angle at Release'] = arm_angles[release_idx]
    
    # Calculate consistency metrics
    if 'arm_angle' in biomechanics_data:
        # Variability in arm angle through delivery
        metrics['Arm Angle Consistency'] = np.std(biomechanics_data['arm_angle'])
    
    if 'trunk_angle' in biomechanics_data:
        # Maximum trunk angle during delivery
        metrics['Max Trunk Angle'] = np.max(biomechanics_data['trunk_angle'])
        
        # Trunk stability (lower standard deviation means more stable)
        metrics['Trunk Stability'] = np.std(biomechanics_data['trunk_angle'])
    
    if 'hip_shoulder_separation' in biomechanics_data:
        # Maximum hip-shoulder separation (important for generating power)
        metrics['Max Hip-Shoulder Separation'] = np.max(biomechanics_data['hip_shoulder_separation'])
    
    if 'front_knee_angle' in biomechanics_data:
        # Front knee angle at release (indicator of bracing)
        metrics['Front Knee Angle'] = np.mean(biomechanics_data['front_knee_angle'])
    
    # Calculate efficiency score (0-100)
    # This is a simplified model and would need calibration for accuracy
    score_components = []
    
    # Arm angle at release (ideally close to 180 degrees)
    if 'Arm Angle at Release' in metrics:
        arm_angle_score = 100 - min(abs(metrics['Arm Angle at Release'] - 180) * 2, 100)
        score_components.append(arm_angle_score)
    
    # Hip-shoulder separation (higher is generally better up to a point)
    if 'Max Hip-Shoulder Separation' in metrics:
        hip_shoulder_score = min(metrics['Max Hip-Shoulder Separation'] * 1.5, 100)
        score_components.append(hip_shoulder_score)
    
    # Trunk stability (lower variation is better)
    if 'Trunk Stability' in metrics:
        trunk_stability_score = max(100 - metrics['Trunk Stability'] * 5, 0)
        score_components.append(trunk_stability_score)
    
    # Calculate technical efficiency score if we have components
    if score_components:
        metrics['Technical Efficiency'] = np.mean(score_components)
    
    return metrics

def calculate_technical_score(metrics):
    """
    Calculate an overall technical score from performance metrics
    
    Args:
        metrics: Dictionary of performance metrics
        
    Returns:
        int: Overall technical score (0-100)
    """
    if not metrics:
        return 0
    
    # If technical efficiency is already calculated, use it
    if 'Technical Efficiency' in metrics:
        return int(metrics['Technical Efficiency'])
    
    # Otherwise calculate from components
    score_components = []
    
    # Arm angle at release (ideally close to 180 degrees)
    if 'Arm Angle at Release' in metrics:
        arm_angle_score = 100 - min(abs(metrics['Arm Angle at Release'] - 180) * 2, 100)
        score_components.append(arm_angle_score)
    
    # Hip-shoulder separation (higher is generally better up to a point)
    if 'Max Hip-Shoulder Separation' in metrics:
        hip_shoulder_score = min(metrics['Max Hip-Shoulder Separation'] * 1.5, 100)
        score_components.append(hip_shoulder_score)
    
    # Trunk stability (lower variation is better)
    if 'Trunk Stability' in metrics:
        trunk_stability_score = max(100 - metrics['Trunk Stability'] * 5, 0)
        score_components.append(trunk_stability_score)
    
    # Front knee angle (should be somewhat bent but not too much)
    if 'Front Knee Angle' in metrics:
        knee_angle = metrics['Front Knee Angle']
        # Ideal range is around 140-160 degrees
        if 140 <= knee_angle <= 160:
            knee_score = 100
        else:
            knee_score = 100 - min(abs(knee_angle - 150) * 2, 100)
        score_components.append(knee_score)
    
    # Calculate overall score if we have components
    if score_components:
        return int(np.mean(score_components))
    
    return 0

def generate_suggestions(metrics):
    """
    Generate improvement suggestions based on performance metrics
    
    Args:
        metrics: Dictionary of performance metrics
        
    Returns:
        dict: Dictionary of improvement suggestions by area
    """
    if not metrics:
        return {}
    
    suggestions = {}
    
    # Arm angle suggestions
    if 'Arm Angle at Release' in metrics:
        arm_angle = metrics['Arm Angle at Release']
        if abs(arm_angle - 180) > 20:
            if arm_angle < 180:
                suggestions['Arm Action'] = "Your bowling arm appears to be bending too early. Try to maintain a straighter arm through the release for better efficiency and reduced injury risk."
            else:
                suggestions['Arm Action'] = "Your bowling arm seems to be extending beyond vertical. Focus on releasing the ball when your arm is closer to vertical for optimal delivery."
    
    # Trunk angle suggestions
    if 'Max Trunk Angle' in metrics:
        trunk_angle = metrics['Max Trunk Angle']
        if trunk_angle < 30:
            suggestions['Trunk Position'] = "Your trunk is too upright during delivery. Try to lean forward more to generate power from your core and improve your follow-through."
        elif trunk_angle > 60:
            suggestions['Trunk Position'] = "You're leaning too far forward during delivery. Try to maintain a more balanced trunk position to prevent stress on your back."
    
    # Hip-shoulder separation suggestions
    if 'Max Hip-Shoulder Separation' in metrics:
        separation = metrics['Max Hip-Shoulder Separation']
        if separation < 30:
            suggestions['Hip-Shoulder Rotation'] = "You could generate more power by increasing the separation between your hips and shoulders during the delivery stride. Focus on rotating your shoulders while keeping your hips facing the target."
    
    # Front knee angle suggestions
    if 'Front Knee Angle' in metrics:
        knee_angle = metrics['Front Knee Angle']
        if knee_angle < 140:
            suggestions['Front Leg'] = "Your front knee is bending too much on delivery. Try to create a firmer front leg to provide better bracing and transfer of momentum."
        elif knee_angle > 170:
            suggestions['Front Leg'] = "Your front leg is too straight on delivery. Allow some flexion in your front knee to absorb forces and prevent injury."
    
    # Consistency suggestions
    if 'Arm Angle Consistency' in metrics:
        consistency = metrics['Arm Angle Consistency']
        if consistency > 20:
            suggestions['Consistency'] = "Your arm path shows significant variation. Work on repeating the same bowling action consistently to improve accuracy and control."
    
    # Add general suggestion if nothing specific was identified
    if not suggestions:
        suggestions['General'] = "Your bowling technique looks good overall. Continue to practice for consistency and minor refinements."
    
    return suggestions
