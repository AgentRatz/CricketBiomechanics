import os
import json
import datetime
import shutil
import tempfile
import pandas as pd
import streamlit as st
import database

# Define base directory for data storage
DATA_DIR = "cricket_biomechanics_data"
EXPORTS_DIR = f"{DATA_DIR}/exports"

def ensure_directories():
    """
    Ensure that the necessary directories exist
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(EXPORTS_DIR, exist_ok=True)

def save_session(session_data):
    """
    Save session data to database
    
    Args:
        session_data (dict): Session data to save
        
    Returns:
        bool: Success status
    """
    ensure_directories()
    
    # Save to database
    success = database.save_session_to_db(session_data)
    
    if success:
        # Also keep in session state for immediate access
        if 'saved_sessions' not in st.session_state:
            st.session_state.saved_sessions = {}
        
        # Store the full session data in session state
        st.session_state.saved_sessions[session_data['id']] = session_data
    
    return success

def load_session_history():
    """
    Load metadata for all saved sessions
    
    Returns:
        list: List of session metadata
    """
    ensure_directories()
    
    # First try loading from database
    sessions = database.load_sessions_from_db()
    
    # If empty, check session state (might be during development)
    if not sessions and 'saved_sessions' in st.session_state:
        sessions = list(st.session_state.saved_sessions.values())
    
    return sessions

def load_session(session_id):
    """
    Load session data from database
    
    Args:
        session_id (str): ID of session to load
        
    Returns:
        dict: Session data
    """
    # First check session state for faster access
    if 'saved_sessions' in st.session_state and session_id in st.session_state.saved_sessions:
        return st.session_state.saved_sessions.get(session_id)
    
    # If not in session state, load from database
    return database.load_session_from_db(session_id)

def delete_session(session_id):
    """
    Delete a session from database
    
    Args:
        session_id (str): ID of session to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Delete from session state if present
    if 'saved_sessions' in st.session_state and session_id in st.session_state.saved_sessions:
        del st.session_state.saved_sessions[session_id]
    
    # Delete from database
    return database.delete_session_from_db(session_id)

def save_analysis_report(session_data):
    """
    Generate and save an analysis report for a session
    
    Args:
        session_data (dict): Session data
        
    Returns:
        str: Result message
    """
    ensure_directories()
    
    # Create timestamp for report
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extract key data for the report
    report_data = {
        'session_id': session_data['id'],
        'session_name': session_data['name'],
        'bowler': session_data['bowler'],
        'bowling_type': session_data['type'],
        'date': session_data['date'],
        'report_generated': timestamp,
        'summary': {
            'number_of_frames': len(session_data['processed_results']),
            'fps': session_data['fps']
        }
    }
    
    # In a real app, we would include more analysis metrics
    
    # Save report to database
    report_id = database.save_report_to_db(session_data['id'], report_data)
    
    if report_id:
        return f"Report saved with ID: {report_id}"
    else:
        return "Error saving report"

def export_session_data(session_id, export_format='csv'):
    """
    Export session data to CSV or Excel
    
    Args:
        session_id (str): ID of session to export
        export_format (str): Format to export (csv or excel)
        
    Returns:
        tuple: (success, file_path or error message)
    """
    # Load the session
    session_data = load_session(session_id)
    if not session_data:
        return False, "Session not found"
    
    try:
        ensure_directories()
        
        # Extract biomechanics data from all frames
        biomechanics_data = []
        
        for i, result in enumerate(session_data['processed_results']):
            if result['biomechanics']:
                frame_data = {
                    'frame': i,
                    'timestamp': i / session_data['fps']
                }
                
                # Add biomechanics metrics
                for key, value in result['biomechanics'].items():
                    if isinstance(value, (int, float)):
                        frame_data[key] = value
                
                biomechanics_data.append(frame_data)
        
        # Create a DataFrame
        df = pd.DataFrame(biomechanics_data)
        
        # Create export file path
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{session_data['id']}_{timestamp}_export"
        
        if export_format == 'csv':
            file_path = os.path.join(EXPORTS_DIR, f"{file_name}.csv")
            df.to_csv(file_path, index=False)
        else:  # excel
            file_path = os.path.join(EXPORTS_DIR, f"{file_name}.xlsx")
            df.to_excel(file_path, index=False)
        
        return True, file_path
        
    except Exception as e:
        return False, str(e)
