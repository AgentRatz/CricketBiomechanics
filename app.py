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
    page_title="Cricket Bowling Biomechanics Tracker",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# App title and description
st.title("🏏 Cricket Bowling Biomechanics Tracker")
st.markdown("""
This application helps cricket coaches and players analyze bowling technique using video processing and biomechanical analysis. 
Upload a video of your bowling action to get detailed insights on arm angle, wrist position, release point, and more.
""")

# Sidebar for navigation and controls
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Select Mode:", ["Record New Session", "Analyze Session", "Session History"])

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
                    with st.spinner("Processing video..."):
                        # Process the video
                        frames, fps = video_processor.extract_frames(video_path)
                        if frames:
                            processed_results = []
                            progress_bar = st.progress(0)
                            
                            for i, frame in enumerate(frames):
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
                            
                            st.session_state.current_session_data = session_data
                            st.session_state.processed_frames = processed_results
                            
                            # Extract biomechanics time series data
                            st.session_state.biomechanics_data = biomechanics.extract_time_series_data(processed_results)
                            
                            # Save session to history
                            data_handler.save_session(session_data)
                            st.session_state.session_history = data_handler.load_session_history()
                            
                            # Navigate to analysis page
                            st.session_state.app_mode = "Analyze Session"
                            st.rerun()
                
                # Clean up the temp file
                os.unlink(video_path)
        
        elif source_option == "Use Webcam":
            st.warning("Webcam recording functionality is not yet implemented in this version.")
            st.info("Please upload a pre-recorded video for analysis.")
            
    with col2:
        st.subheader("Recording Tips")
        st.markdown("""
        ### For Best Results:
        
        * Record from side-on view for best biomechanical analysis
        * Ensure good lighting conditions
        * Wear contrasting clothing to background
        * Keep the camera stable
        * Capture the full bowling action, from run-up to follow-through
        * Try to keep the bowler in frame throughout the action
        
        ### Video Requirements:
        * Supported formats: MP4, MOV, AVI
        * Recommended resolution: 720p or higher
        * Recommended frame rate: 30fps or higher for best results
        """)

elif app_mode == "Analyze Session":
    st.header("Bowling Biomechanics Analysis")
    
    # Check if we have data to analyze
    if st.session_state.current_session_data is None:
        st.warning("No session data available for analysis. Please record a new session or select one from history.")
    else:
        session_data = st.session_state.current_session_data
        processed_results = session_data['processed_results']
        
        # Session information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Session Name:** {session_data['name']}")
        with col2:
            st.markdown(f"**Bowler:** {session_data['bowler']}")
        with col3:
            st.markdown(f"**Date:** {session_data['date']}")
        
        # Frame navigation
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Frame slider
            frame_count = len(processed_results)
            if frame_count > 0:
                st.session_state.frame_index = st.slider("Frame", 0, frame_count-1, st.session_state.frame_index)
                
                # Display current frame with landmarks
                current_result = processed_results[st.session_state.frame_index]
                st.image(current_result['frame'], caption=f"Frame {st.session_state.frame_index}", use_column_width=True)
        
        with col2:
            st.subheader("Frame Controls")
            col_prev, col_next = st.columns(2)
            
            with col_prev:
                if st.button("◀ Previous"):
                    st.session_state.frame_index = max(0, st.session_state.frame_index - 1)
                    st.rerun()
            
            with col_next:
                if st.button("Next ▶"):
                    st.session_state.frame_index = min(frame_count - 1, st.session_state.frame_index + 1)
                    st.rerun()
            
            # Display frame biomechanics
            current_result = processed_results[st.session_state.frame_index]
            if current_result['biomechanics']:
                st.subheader("Current Frame Metrics")
                biometrics = current_result['biomechanics']
                st.metric("Arm Angle", f"{biometrics['arm_angle']:.1f}°")
                st.metric("Wrist Angle", f"{biometrics['wrist_angle']:.1f}°")
                st.metric("Trunk Angle", f"{biometrics['trunk_angle']:.1f}°")
                st.metric("Front Knee Angle", f"{biometrics['front_knee_angle']:.1f}°")
            else:
                st.warning("No biomechanical data detected in this frame")
        
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
                            st.image(phase_result['frame'], use_column_width=True)
                            
                            if phase_result['biomechanics']:
                                biometrics = phase_result['biomechanics']
                                metrics = [
                                    f"Arm Angle: {biometrics['arm_angle']:.1f}°",
                                    f"Wrist Angle: {biometrics['wrist_angle']:.1f}°",
                                    f"Trunk Angle: {biometrics['trunk_angle']:.1f}°"
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
                st.session_state.current_session_data = selected_session
                st.session_state.processed_frames = selected_session['processed_results']
                st.session_state.biomechanics_data = biomechanics.extract_time_series_data(selected_session['processed_results'])
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
                    # Extract time series data for both sessions
                    biomechanics_data1 = biomechanics.extract_time_series_data(session1['processed_results'])
                    biomechanics_data2 = biomechanics.extract_time_series_data(session2['processed_results'])
                    
                    # Calculate performance metrics
                    metrics1 = biomechanics.calculate_performance_metrics(biomechanics_data1, session1['processed_results'])
                    metrics2 = biomechanics.calculate_performance_metrics(biomechanics_data2, session2['processed_results'])
                    
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
st.markdown("Cricket Bowling Biomechanics Tracker | Developed with Streamlit, OpenCV and MediaPipe")
