import os
import json
import datetime
import shutil
import tempfile
import pandas as pd
import streamlit as st

# Define base directory for data storage
DATA_DIR = "cricket_biomechanics_data"
SESSIONS_DIR = f"{DATA_DIR}/sessions"
REPORTS_DIR = f"{DATA_DIR}/reports"

def ensure_directories():
    """
    Ensure that the necessary directories exist
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

def save_session(session_data):
    """
    Save session data to file
    
    Args:
        session_data (dict): Session data to save
        
    Returns:
        str: Path to saved session file
    """
    ensure_directories()
    
    # Create a copy of the session data without large frame data
    session_metadata = {
        'id': session_data['id'],
        'name': session_data['name'],
        'bowler': session_data['bowler'],
        'type': session_data['type'],
        'date': session_data['date'],
        'fps': session_data['fps']
    }
    
    # Create paths for metadata and processed results
    metadata_path = os.path.join(SESSIONS_DIR, f"{session_data['id']}_metadata.json")
    
    # Save session metadata
    with open(metadata_path, 'w') as f:
        json.dump(session_metadata, f)
    
    # Save lightweight session_data to state
    # We don't actually save the processed_results permanently due to size constraints
    # In a real application, we would implement a more sophisticated storage solution
    
    # Just to simulate persistence between Streamlit reruns:
    if 'saved_sessions' not in st.session_state:
        st.session_state.saved_sessions = {}
    
    # Store the full session data in session state
    st.session_state.saved_sessions[session_data['id']] = session_data
    
    return metadata_path

def load_session_history():
    """
    Load metadata for all saved sessions
    
    Returns:
        list: List of session metadata
    """
    ensure_directories()
    
    # In a real app, we would load metadata from files and actual session data from database
    # For this demo, we'll use session state to simulate persistence
    
    # If no saved sessions in state, create empty dict
    if 'saved_sessions' not in st.session_state:
        st.session_state.saved_sessions = {}
        
    # Return list of sessions from session state
    return list(st.session_state.saved_sessions.values())

def load_session(session_id):
    """
    Load session data from file
    
    Args:
        session_id (str): ID of session to load
        
    Returns:
        dict: Session data
    """
    # In a real app, we would load from disk/database
    # For this demo, we retrieve from session state
    
    if 'saved_sessions' not in st.session_state:
        return None
    
    return st.session_state.saved_sessions.get(session_id)

def delete_session(session_id):
    """
    Delete a session
    
    Args:
        session_id (str): ID of session to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    ensure_directories()
    
    # Delete from session state
    if 'saved_sessions' in st.session_state and session_id in st.session_state.saved_sessions:
        del st.session_state.saved_sessions[session_id]
        return True
    
    return False

def save_analysis_report(session_data):
    """
    Generate and save an analysis report for a session
    
    Args:
        session_data (dict): Session data
        
    Returns:
        str: Path to saved report
    """
    ensure_directories()
    
    # Create report filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{session_data['id']}_{timestamp}_report.json"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    
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
    
    # Save report
    with open(report_path, 'w') as f:
        json.dump(report_data, f)
    
    return report_path

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
        # Create a temporary directory for the export
        temp_dir = tempfile.mkdtemp()
        
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
            file_path = os.path.join(temp_dir, f"{file_name}.csv")
            df.to_csv(file_path, index=False)
        else:  # excel
            file_path = os.path.join(temp_dir, f"{file_name}.xlsx")
            df.to_excel(file_path, index=False)
        
        return True, file_path
        
    except Exception as e:
        return False, str(e)
