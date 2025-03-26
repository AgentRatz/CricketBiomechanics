import uuid
import os
import time
import numpy as np
import cv2
from datetime import datetime

def generate_id():
    """
    Generate a unique ID for a session
    
    Returns:
        str: Unique ID
    """
    return str(uuid.uuid4())

def timestamp_string():
    """
    Generate a timestamp string
    
    Returns:
        str: Timestamp string in format YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def filename_safe_string(s):
    """
    Convert a string to be safe for filenames
    
    Args:
        s (str): Input string
        
    Returns:
        str: Filename-safe string
    """
    # Replace spaces with underscores and remove special characters
    return "".join([c if c.isalnum() else "_" for c in s])

def resize_with_aspect_ratio(image, width=None, height=None, inter=cv2.INTER_AREA):
    """
    Resize an image maintaining aspect ratio
    
    Args:
        image: Image to resize
        width: Target width
        height: Target height
        inter: Interpolation method
        
    Returns:
        numpy.ndarray: Resized image
    """
    dim = None
    h, w = image.shape[:2]
    
    if width is None and height is None:
        return image
    
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    
    return cv2.resize(image, dim, interpolation=inter)

def smooth_time_series(data, window_size=5):
    """
    Apply moving average smoothing to time series data
    
    Args:
        data (numpy.ndarray): Input time series data
        window_size (int): Size of smoothing window
        
    Returns:
        numpy.ndarray: Smoothed time series
    """
    if len(data) < window_size:
        return data
    
    # Create the window
    window = np.ones(window_size) / window_size
    
    # Apply convolution
    smoothed = np.convolve(data, window, mode='valid')
    
    # Pad the ends to maintain the same length
    pad_size = len(data) - len(smoothed)
    pad_left = pad_size // 2
    pad_right = pad_size - pad_left
    
    return np.concatenate([data[:pad_left], smoothed, data[-pad_right:]])

def angle_between_points(a, b, c):
    """
    Calculate angle between three points
    
    Args:
        a (tuple): First point (x, y)
        b (tuple): Middle point (x, y) - the vertex
        c (tuple): Third point (x, y)
        
    Returns:
        float: Angle in degrees
    """
    vec_ba = (a[0] - b[0], a[1] - b[1])
    vec_bc = (c[0] - b[0], c[1] - b[1])
    
    # Calculate dot product
    dot_product = vec_ba[0] * vec_bc[0] + vec_ba[1] * vec_bc[1]
    
    # Calculate magnitudes
    mag_ba = np.sqrt(vec_ba[0]**2 + vec_ba[1]**2)
    mag_bc = np.sqrt(vec_bc[0]**2 + vec_bc[1]**2)
    
    # Calculate angle
    cos_angle = dot_product / (mag_ba * mag_bc)
    
    # Handle numerical errors
    cos_angle = max(-1, min(1, cos_angle))
    
    # Convert to degrees
    angle = np.degrees(np.arccos(cos_angle))
    
    return angle

def distance_between_points(a, b):
    """
    Calculate Euclidean distance between two points
    
    Args:
        a (tuple): First point (x, y)
        b (tuple): Second point (x, y)
        
    Returns:
        float: Distance
    """
    return np.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)

def normalize_values(values, min_val=None, max_val=None):
    """
    Normalize values to range [0, 1]
    
    Args:
        values (list): Values to normalize
        min_val (float): Minimum value for normalization
        max_val (float): Maximum value for normalization
        
    Returns:
        list: Normalized values
    """
    if min_val is None:
        min_val = min(values)
    if max_val is None:
        max_val = max(values)
    
    if max_val == min_val:
        return [0.5] * len(values)
    
    return [(x - min_val) / (max_val - min_val) for x in values]
