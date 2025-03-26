import streamlit as st
import cv2
import numpy as np
import tempfile
import os
import time
import pandas as pd
from datetime import datetime

import biomechanics
import video_processor
import data_handler
import visualization
import utils

# Page configuration
st.set_page_config(
    page_title="Comparative Analysis of Hyperextended Elbow Mechanics",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'current_session_data' not in st.session_state:
    st.session_state.current_session_data = None
if 'frame_index' not in st.session_state:
    st.session_state.frame_index = 0
if 'processed_frames' not in st.session_state:
    st.session_state.processed_frames = []
if 'biomechanics_data' not in st.session_state:
    st.session_state.biomechanics_data = None
if 'session_history' not in st.session_state:
    st.session_state.session_history = data_handler.load_session_history()
if 'selected_session' not in st.session_state:
    st.session_state.selected_session = None

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 0;
        margin-bottom: 2rem;
    }
    .university-logo {
        max-width: 300px; 
        margin: 0 auto;
        display: block;
    }
    .developer-info {
        text-align: center;
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1.5rem;
    }
    .metrics-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
    }
    .st-emotion-cache-1kyxreq {
        margin-top: -60px;
    }
    .subheader {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #aa0000;
    }
    .tab-content {
        padding: 1rem;
        border: 1px solid #e6e6e6;
        border-radius: 5px;
    }
    .sidebar .stRadio {
        background-color: #f0f2f6; 
        padding: 1rem;
        border-radius: 5px;
    }
    .tips-box {
        border-left: 3px solid #aa0000;
        padding-left: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# App title and logo
col1, col2 = st.columns([1, 2])

with col1:
    st.image("attached_assets/vitap.png", width=200)

with col2:
    st.markdown("<h1 class='main-header'>Comparative Analysis of Hyperextended Elbow Mechanics in Sport's Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<div class='developer-info'>Developed by: <b>CHINTAPENTA SAI RAHUL BHARADWAJ (21BCE7848)</b> | <b>PENDYALA SRI VENKATA PRANAV (21BCE7595)</b> | <b>ARYAN ANIL SHINDE (21BCE8722)</b></div>", unsafe_allow_html=True)

st.markdown("""
This advanced application analyzes cricket bowling technique using AI-powered video processing and biomechanical analysis. 
Upload a video of your bowling action to get detailed insights on arm angle, wrist position, release point, and more with 
visualization tools for comprehensive analysis.
""")

# Sidebar for navigation and controls
st.sidebar.image("attached_assets/vitap.png", width=120)
st.sidebar.title("Navigation")
st.sidebar.markdown("<div class='subheader'>Bowling Biomechanics Analysis</div>", unsafe_allow_html=True)

# Create colorful sidebar navigation
app_mode = st.sidebar.radio("Select Mode:", ["Record New Session", "Analyze Session", "Session History"])

# Add information section in sidebar
with st.sidebar.expander("About the Project"):
    st.markdown("""
    This application analyzes cricket bowling biomechanics using advanced computer vision techniques to track body movements. 
    
    It focuses on understanding hyperextended elbow mechanics and providing actionable feedback for technique improvement.
    
    **Key Features:**
    - Motion tracking with MediaPipe
    - Detailed biomechanical measurements
    - Comparative session analysis
    - Performance metrics and scoring
    - Personalized improvement suggestions
    """)

with st.sidebar.expander("Help & Instructions"):
    st.markdown("""
    1. **Record Session**: Upload a video of a bowling action
    2. **Analyze Session**: View detailed biomechanics of current session
    3. **Session History**: Access and compare previous sessions

    For best results, record videos from a side angle in good lighting with the bowler's full action visible.
    """)

if app_mode == "Record New Session":
    st.header("Record New Bowling Session")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Session Information")
        session_name = st.text_input("Session Name", f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        bowler_name = st.text_input("Bowler Name", "")
        bowling_type = st.selectbox("Bowling Type", ["Fast", "Medium Fast", "Spin", "Off Spin", "Leg Spin"])
        
        st.subheader("Video Source")
        source_option = st.radio("Choose Source", ["Upload Video", "Use Webcam"])
        
        if source_option == "Upload Video":
            uploaded_file = st.file_uploader("Upload bowling video", type=['mp4', 'mov', 'avi'])
            
            if uploaded_file is not None:
                # Save uploaded file to temp file
                tfile = tempfile.NamedTemporaryFile(delete=False)
                tfile.write(uploaded_file.read())
                video_path = tfile.name
                
                st.video(uploaded_file)
                
                if st.button("Process Video"):
                    try:
                        with st.spinner("Processing video..."):
                            st.info("Step 1: Extracting frames from video...")
                            # Process the video
                            frames, fps = video_processor.extract_frames(video_path)
                            if frames:
                                processed_results = []
                                progress_bar = st.progress(0)
                                
                                st.info(f"Step 2: Processing {len(frames)} frames with MediaPipe...")
                                for i, frame in enumerate(frames):
                                    try:
                                        # Process frame with MediaPipe
                                        processed_frame, landmarks = video_processor.process_frame(frame)
                                        
                                        # Extract biomechanics if landmarks were detected
                                        if landmarks:
                                            biomechanics_data = biomechanics.extract_biomechanics(landmarks, frame.shape)
                                            processed_results.append({
                                                'frame': processed_frame,
                                                'landmarks': landmarks,
                                                'biomechanics': biomechanics_data
                                            })
                                        else:
                                            processed_results.append({
                                                'frame': processed_frame,
                                                'landmarks': None,
                                                'biomechanics': None
                                            })
                                        
                                        # Update progress
                                        progress_bar.progress((i + 1) / len(frames))
                                    except Exception as frame_error:
                                        st.error(f"Error processing frame {i}: {str(frame_error)}")
                                        raise
                                
                                st.info("Step 3: Creating session data...")
                                # Save session data
                                session_data = {
                                    'id': utils.generate_id(),
                                    'name': session_name,
                                    'bowler': bowler_name,
                                    'type': bowling_type,
                                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'processed_results': processed_results,
                                    'fps': fps
                                }
                                
                                st.info("Step 4: Updating session state...")
                                st.session_state.current_session_data = session_data
                                st.session_state.processed_frames = processed_results
                                
                                st.info("Step 5: Extracting time series data...")
                                # Extract biomechanics time series data
                                st.session_state.biomechanics_data = biomechanics.extract_time_series_data(processed_results)
                                
                                st.info("Step 6: Saving to database...")
                                # Save session to history
                                save_result = data_handler.save_session(session_data)
                                if not save_result:
                                    st.error("Failed to save session to database!")
                                    raise Exception("Database save error")
                                
                                st.info("Step 7: Loading updated session history...")
                                st.session_state.session_history = data_handler.load_session_history()
                                
                                st.success("Video processed and saved successfully!")
                                
                                # Navigate to analysis page
                                st.session_state.app_mode = "Analyze Session"
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error processing video: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                
                # Clean up the temp file
                os.unlink(video_path)
        
        elif source_option == "Use Webcam":
            st.warning("Webcam recording functionality is not yet implemented in this version.")
            st.info("Please upload a pre-recorded video for analysis.")
            
    with col2:
        st.markdown("<div class='subheader'>Recording Tips</div>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("""
            <div class="tips-box">
            <h3>For Best Results:</h3>
            
            <ul>
                <li><strong>Angle:</strong> Record from side-on view for optimal biomechanical analysis</li>
                <li><strong>Lighting:</strong> Ensure good, consistent lighting without shadows</li>
                <li><strong>Clothing:</strong> Wear contrasting clothing to background</li>
                <li><strong>Camera:</strong> Keep the camera stable, preferably on a tripod</li>
                <li><strong>Coverage:</strong> Capture the full bowling action, from run-up to follow-through</li>
                <li><strong>Framing:</strong> Keep the bowler in frame throughout the action</li>
            </ul>
            
            <h3>Video Requirements:</h3>
            <ul>
                <li><strong>Formats:</strong> MP4, MOV, AVI</li>
                <li><strong>Resolution:</strong> 720p or higher recommended</li>
                <li><strong>Frame Rate:</strong> 30fps or higher for best results</li>
                <li><strong>Duration:</strong> 3-10 seconds covering the complete action</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
        # Example image
        st.markdown("<h4 style='text-align: center; margin-top: 20px;'>Example of Good Recording Angle</h4>", unsafe_allow_html=True)
        # This would typically be an example image, using logo as placeholder
        st.image("attached_assets/vitap.png", width=280)
        st.caption("Record from a side-on view to capture the full bowling action")
        

elif app_mode == "Analyze Session":
    st.header("Bowling Biomechanics Analysis")
    
    # Check if we have data to analyze
    if st.session_state.current_session_data is None:
        st.warning("No session data available for analysis. Please record a new session or select one from history.")
    else:
        session_data = st.session_state.current_session_data
        processed_results = session_data.get('processed_results', [])
        
        # Handling case where processed_results might have None frame data
        # This is likely when loading from the database with our simplified storage approach
        if processed_results and 'frame' in processed_results[0] and processed_results[0]['frame'] is None:
            st.info("Using simplified analysis with biomechanics data only (frames not loaded from database)")
            
            # If we need frame data for display later, we could regenerate it here or show placeholders
        
        # Session information in a nice container
        st.markdown("""
        <style>
        .session-info {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
        }
        .session-item {
            text-align: center;
            padding: 0 15px;
        }
        .session-label {
            font-size: 0.8rem;
            color: #555;
            margin-bottom: 5px;
        }
        .session-value {
            font-size: 1.1rem;
            font-weight: bold;
            color: #111;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="session-info">
            <div class="session-item">
                <div class="session-label">Session Name</div>
                <div class="session-value">{session_data['name']}</div>
            </div>
            <div class="session-item">
                <div class="session-label">Bowler</div>
                <div class="session-value">{session_data['bowler']}</div>
            </div>
            <div class="session-item">
                <div class="session-label">Bowling Type</div>
                <div class="session-value">{session_data['type']}</div>
            </div>
            <div class="session-item">
                <div class="session-label">Date</div>
                <div class="session-value">{session_data['date']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Frame navigation
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Frame slider
            # Safety check for processed_results
            if processed_results:
                frame_count = len(processed_results)
                if frame_count > 0:
                    # Initialize frame_index if needed
                    if not hasattr(st.session_state, 'frame_index') or st.session_state.frame_index >= frame_count:
                        st.session_state.frame_index = 0
                    
                    st.session_state.frame_index = st.slider("Frame", 0, frame_count-1, st.session_state.frame_index)
                    
                    # Display current frame with landmarks
                    current_result = processed_results[st.session_state.frame_index]
                    
                    # Check if the frame is available (it might be None if loaded from DB)
                    if current_result and current_result.get('frame') is not None:
                        st.image(current_result['frame'], caption=f"Frame {st.session_state.frame_index}", use_column_width=True)
                    else:
                        # Display a placeholder for frame data
                        st.info("Frame image not available - using simplified data from database")
                        # Display a placeholder image with the VIT-AP logo
                        st.image("attached_assets/vitap.png", caption="Frame data not stored in database", use_column_width=True)
                else:
                    st.warning("No frames available in the processed results.")
            else:
                st.warning("No processed results available for this session.")
        
        with col2:
            st.subheader("Frame Controls")
            col_prev, col_next = st.columns(2)
            
            with col_prev:
                if st.button("◀ Previous") and hasattr(st.session_state, 'frame_index'):
                    st.session_state.frame_index = max(0, st.session_state.frame_index - 1)
                    st.rerun()
            
            with col_next:
                if st.button("Next ▶"):
                    # Initialize frame_count if needed
                    frame_count = len(processed_results) if processed_results else 0
                    if frame_count > 0:  # Only proceed if there are frames
                        st.session_state.frame_index = min(frame_count - 1, st.session_state.frame_index + 1)
                        st.rerun()
            
            # Display frame biomechanics - with additional safety checks
            if processed_results and 0 <= st.session_state.frame_index < len(processed_results):
                current_result = processed_results[st.session_state.frame_index]
                if current_result and 'biomechanics' in current_result and current_result['biomechanics']:
                    st.subheader("Current Frame Metrics")
                    biometrics = current_result['biomechanics']
                    st.metric("Arm Angle", f"{biometrics.get('arm_angle', 0):.1f}°")
                    st.metric("Wrist Angle", f"{biometrics.get('wrist_angle', 0):.1f}°")
                    st.metric("Trunk Angle", f"{biometrics.get('trunk_angle', 0):.1f}°")
                    st.metric("Front Knee Angle", f"{biometrics.get('front_knee_angle', 0):.1f}°")
                else:
                    st.warning("No biomechanical data detected in this frame")
            else:
                st.warning("No frames available for biomechanical analysis")
        
        # Detailed analysis tabs
        st.subheader("Detailed Analysis")
        tab1, tab2, tab3 = st.tabs(["Biomechanics Graphs", "Phase Analysis", "Performance Metrics"])
        
        with tab1:
            # Display time series plots of biomechanical data
            if st.session_state.biomechanics_data is not None:
                visualization.plot_time_series(st.session_state.biomechanics_data, session_data['fps'])
            else:
                st.warning("No biomechanical time series data available")
        
        with tab2:
            # Key phases of the bowling action
            phases = biomechanics.identify_bowling_phases(session_data['processed_results'])
            if phases:
                st.subheader("Key Bowling Phases")
                
                # Create columns for each phase
                phase_cols = st.columns(len(phases))
                
                for i, (phase_name, frame_idx) in enumerate(phases.items()):
                    with phase_cols[i]:
                        st.markdown(f"**{phase_name}**")
                        if frame_idx is not None and 0 <= frame_idx < len(processed_results):
                            phase_result = processed_results[frame_idx]
                            
                            # Check if frame is available
                            if phase_result.get('frame') is not None:
                                st.image(phase_result['frame'], use_column_width=True)
                            else:
                                # Show placeholder
                                st.info(f"Phase {phase_name} frame not available")
                                st.image("attached_assets/vitap.png", width=150)
                            
                            if phase_result and 'biomechanics' in phase_result and phase_result['biomechanics']:
                                biometrics = phase_result['biomechanics']
                                # Use get() with defaults to prevent KeyError
                                metrics = [
                                    f"Arm Angle: {biometrics.get('arm_angle', 0):.1f}°",
                                    f"Wrist Angle: {biometrics.get('wrist_angle', 0):.1f}°",
                                    f"Trunk Angle: {biometrics.get('trunk_angle', 0):.1f}°"
                                ]
                                st.markdown("<br>".join(metrics), unsafe_allow_html=True)
                            
                            if st.button(f"Go to {phase_name}", key=f"goto_{phase_name}"):
                                st.session_state.frame_index = frame_idx
                                st.rerun()
                        else:
                            st.info("Phase not detected")
            else:
                st.warning("Could not identify distinct bowling phases")
        
        with tab3:
            # Performance metrics
            st.subheader("Performance Metrics")
            
            metrics = biomechanics.calculate_performance_metrics(st.session_state.biomechanics_data, processed_results)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Technical Metrics")
                
                if metrics:
                    for metric, value in metrics.items():
                        if isinstance(value, (int, float)):
                            st.metric(metric, f"{value:.1f}")
                        else:
                            st.metric(metric, value)
                    
                    # Render technical score
                    score = biomechanics.calculate_technical_score(metrics)
                    st.markdown(f"### Overall Technical Score: {score}/100")
                    
                    # Visualization of score
                    visualization.plot_technical_score_gauge(score)
                else:
                    st.warning("Could not calculate performance metrics")
            
            with col2:
                st.markdown("### Improvement Suggestions")
                suggestions = biomechanics.generate_suggestions(metrics)
                
                if suggestions:
                    for area, suggestion in suggestions.items():
                        st.markdown(f"**{area}:**")
                        st.markdown(f"{suggestion}")
                else:
                    st.info("No improvement suggestions available")
        
        # Save analysis button
        if st.button("Save Analysis Report"):
            # Generate and save the report
            report_path = data_handler.save_analysis_report(session_data)
            st.success(f"Analysis report saved successfully!")

elif app_mode == "Session History":
    st.header("Session History")
    
    if not st.session_state.session_history:
        st.info("No previous sessions found.")
    else:
        # Display sessions in a table
        sessions_df = pd.DataFrame([
            {
                'Session ID': session['id'],
                'Name': session['name'],
                'Bowler': session['bowler'],
                'Type': session['type'],
                'Date': session['date']
            }
            for session in st.session_state.session_history
        ])
        
        st.dataframe(sessions_df, use_container_width=True)
        
        # Session selection
        selected_session_id = st.selectbox(
            "Select a session to view", 
            options=[session['id'] for session in st.session_state.session_history],
            format_func=lambda x: next((s['name'] for s in st.session_state.session_history if s['id'] == x), x)
        )
        
        if st.button("Load Selected Session"):
            # Load the selected session
            selected_session = next((s for s in st.session_state.session_history if s['id'] == selected_session_id), None)
            
            if selected_session:
                # Load the full session from the database (the history might have limited data)
                full_session = data_handler.load_session(selected_session['id'])
                
                if full_session:
                    # Use the full session data
                    st.session_state.current_session_data = full_session
                else:
                    # In case loading the full session fails, use what we have
                    st.session_state.current_session_data = selected_session
                    # Ensure processed_results exists
                    if 'processed_results' not in selected_session:
                        selected_session['processed_results'] = []
                
                # Safely access processed_results with a default empty list
                processed_results = st.session_state.current_session_data.get('processed_results', [])
                st.session_state.processed_frames = processed_results
                st.session_state.biomechanics_data = biomechanics.extract_time_series_data(processed_results)
                st.session_state.frame_index = 0
                
                # Navigate to analysis page
                st.session_state.app_mode = "Analyze Session"
                st.rerun()
        
        # Compare sessions
        st.subheader("Compare Sessions")
        
        if len(st.session_state.session_history) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                session1_id = st.selectbox(
                    "First Session", 
                    options=[session['id'] for session in st.session_state.session_history],
                    format_func=lambda x: next((s['name'] for s in st.session_state.session_history if s['id'] == x), x),
                    key="session1"
                )
            
            with col2:
                # Filter out session1 from the options
                session2_options = [s['id'] for s in st.session_state.session_history if s['id'] != session1_id]
                session2_id = st.selectbox(
                    "Second Session", 
                    options=session2_options,
                    format_func=lambda x: next((s['name'] for s in st.session_state.session_history if s['id'] == x), x),
                    key="session2"
                )
            
            if st.button("Compare Sessions"):
                # Get the selected sessions
                session1 = next((s for s in st.session_state.session_history if s['id'] == session1_id), None)
                session2 = next((s for s in st.session_state.session_history if s['id'] == session2_id), None)
                
                if session1 and session2:
                    # Load full sessions from the database for better data
                    full_session1 = data_handler.load_session(session1['id'])
                    full_session2 = data_handler.load_session(session2['id'])
                    
                    # Use full sessions if available, otherwise use what we have from history
                    session1_data = full_session1 if full_session1 else session1
                    session2_data = full_session2 if full_session2 else session2
                    
                    # Ensure processed_results exists in both sessions
                    if 'processed_results' not in session1_data:
                        session1_data['processed_results'] = []
                    if 'processed_results' not in session2_data:
                        session2_data['processed_results'] = []
                    
                    # Extract time series data for both sessions
                    biomechanics_data1 = biomechanics.extract_time_series_data(session1_data['processed_results'])
                    biomechanics_data2 = biomechanics.extract_time_series_data(session2_data['processed_results'])
                    
                    # Calculate performance metrics
                    metrics1 = biomechanics.calculate_performance_metrics(biomechanics_data1, session1_data['processed_results'])
                    metrics2 = biomechanics.calculate_performance_metrics(biomechanics_data2, session2_data['processed_results'])
                    
                    # Display comparative visualization
                    st.subheader("Comparative Analysis")
                    visualization.plot_session_comparison(
                        biomechanics_data1, biomechanics_data2, 
                        session1['name'], session2['name'],
                        metrics1, metrics2
                    )
        else:
            st.info("You need at least two sessions to compare.")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.image("attached_assets/vitap.png", width=100)

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 10px;">
        <p><b>Comparative Analysis of Hyperextended Elbow Mechanics in Sport's Analytics</b></p>
        <p style="font-size: 0.8rem;">Developed with Streamlit, OpenCV, MediaPipe, and PostgreSQL | © 2025 VIT-AP University</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: right; padding: 10px;">
        <p style="font-size: 0.8rem;"><b>Department of Computer Science</b><br>
        Faculty of Engineering<br>
        VIT-AP University</p>
    </div>
    """, unsafe_allow_html=True)
