import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots

def plot_time_series(biomechanics_data, fps):
    """
    Plot time series data of biomechanical measurements
    
    Args:
        biomechanics_data (dict): Dictionary of time series data
        fps (float): Frames per second of the video
    """
    if not biomechanics_data:
        st.warning("No biomechanical data available for visualization")
        return
    
    # Create time values (in seconds)
    frames = len(list(biomechanics_data.values())[0])  # Length of first data series
    time = np.arange(frames) / fps
    
    # Create tabs for different metric categories
    tab1, tab2, tab3 = st.tabs(["Arm & Wrist Angles", "Body Alignment", "Other Metrics"])
    
    with tab1:
        # Create figure for arm and wrist angles
        fig = make_subplots(specs=[[{"secondary_y": False}]])
        
        # Add arm angle
        if 'arm_angle' in biomechanics_data:
            fig.add_trace(
                go.Scatter(x=time, y=biomechanics_data['arm_angle'], name="Arm Angle (°)"),
                secondary_y=False,
            )
        
        # Add wrist angle
        if 'wrist_angle' in biomechanics_data:
            fig.add_trace(
                go.Scatter(x=time, y=biomechanics_data['wrist_angle'], name="Wrist Angle (°)"),
                secondary_y=False,
            )
        
        # Add vertical line for release point if we can estimate it
        # Approximate release as the point where arm angle is closest to 180 degrees
        if 'arm_angle' in biomechanics_data:
            release_idx = np.argmin(np.abs(biomechanics_data['arm_angle'] - 180))
            release_time = release_idx / fps
            
            fig.add_vline(
                x=release_time, 
                line_width=2, 
                line_dash="dash", 
                line_color="red",
                annotation_text="Est. Release",
                annotation_position="top right"
            )
        
        # Update layout
        fig.update_layout(
            title="Arm and Wrist Angles Over Time",
            xaxis_title="Time (seconds)",
            yaxis_title="Angle (degrees)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Create figure for body alignment metrics
        fig = make_subplots(specs=[[{"secondary_y": False}]])
        
        # Add trunk angle
        if 'trunk_angle' in biomechanics_data:
            fig.add_trace(
                go.Scatter(x=time, y=biomechanics_data['trunk_angle'], name="Trunk Angle (°)"),
                secondary_y=False,
            )
        
        # Add front knee angle
        if 'front_knee_angle' in biomechanics_data:
            fig.add_trace(
                go.Scatter(x=time, y=biomechanics_data['front_knee_angle'], name="Front Knee Angle (°)"),
                secondary_y=False,
            )
        
        # Add back knee angle
        if 'back_knee_angle' in biomechanics_data:
            fig.add_trace(
                go.Scatter(x=time, y=biomechanics_data['back_knee_angle'], name="Back Knee Angle (°)"),
                secondary_y=False,
            )
        
        # Add hip-shoulder separation
        if 'hip_shoulder_separation' in biomechanics_data:
            fig.add_trace(
                go.Scatter(x=time, y=biomechanics_data['hip_shoulder_separation'], name="Hip-Shoulder Separation (°)"),
                secondary_y=False,
            )
        
        # Add vertical line for release point if we can estimate it
        if 'arm_angle' in biomechanics_data:
            release_idx = np.argmin(np.abs(biomechanics_data['arm_angle'] - 180))
            release_time = release_idx / fps
            
            fig.add_vline(
                x=release_time, 
                line_width=2, 
                line_dash="dash", 
                line_color="red",
                annotation_text="Est. Release",
                annotation_position="top right"
            )
        
        # Update layout
        fig.update_layout(
            title="Body Alignment Metrics Over Time",
            xaxis_title="Time (seconds)",
            yaxis_title="Angle (degrees)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Create figure for other metrics
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add normalized release point height
        if 'release_point_height' in biomechanics_data:
            fig.add_trace(
                go.Scatter(x=time, y=biomechanics_data['release_point_height'], name="Release Height (norm.)"),
                secondary_y=False,
            )
        
        # Add normalized release point horizontal position
        if 'release_point_horizontal' in biomechanics_data:
            fig.add_trace(
                go.Scatter(x=time, y=biomechanics_data['release_point_horizontal'], name="Release Horizontal Pos. (norm.)"),
                secondary_y=False,
            )
        
        # Add shoulder rotation
        if 'shoulder_rotation' in biomechanics_data:
            fig.add_trace(
                go.Scatter(x=time, y=biomechanics_data['shoulder_rotation'], name="Shoulder Rotation (°)"),
                secondary_y=True,
            )
        
        # Add vertical line for release point if we can estimate it
        if 'arm_angle' in biomechanics_data:
            release_idx = np.argmin(np.abs(biomechanics_data['arm_angle'] - 180))
            release_time = release_idx / fps
            
            fig.add_vline(
                x=release_time, 
                line_width=2, 
                line_dash="dash", 
                line_color="red",
                annotation_text="Est. Release",
                annotation_position="top right"
            )
        
        # Update layout
        fig.update_layout(
            title="Other Biomechanical Metrics Over Time",
            xaxis_title="Time (seconds)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500
        )
        
        fig.update_yaxes(title_text="Normalized Position (0-1)", secondary_y=False)
        fig.update_yaxes(title_text="Angle (degrees)", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)

def plot_technical_score_gauge(score):
    """
    Plot a gauge chart for the technical score
    
    Args:
        score (float): Technical score (0-100)
    """
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Technical Score"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "royalblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 25], 'color': 'red'},
                {'range': [25, 50], 'color': 'orange'},
                {'range': [50, 75], 'color': 'yellow'},
                {'range': [75, 100], 'color': 'green'}
            ],
            'threshold': {
                'line': {'color': "navy", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_session_comparison(data1, data2, name1, name2, metrics1, metrics2):
    """
    Plot comparison between two sessions
    
    Args:
        data1 (dict): Biomechanics data from first session
        data2 (dict): Biomechanics data from second session
        name1 (str): Name of first session
        name2 (str): Name of second session
        metrics1 (dict): Performance metrics from first session
        metrics2 (dict): Performance metrics from second session
    """
    # Create tabs for different comparison views
    tab1, tab2 = st.tabs(["Metrics Comparison", "Time Series Comparison"])
    
    with tab1:
        # Create a radar chart comparing key metrics
        if metrics1 and metrics2:
            # Identify common metrics that are numeric
            common_metrics = []
            for key in metrics1:
                if key in metrics2 and isinstance(metrics1[key], (int, float)) and isinstance(metrics2[key], (int, float)):
                    common_metrics.append(key)
            
            if common_metrics:
                # Prepare data for radar chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatterpolar(
                    r=[metrics1[m] for m in common_metrics],
                    theta=common_metrics,
                    fill='toself',
                    name=name1
                ))
                
                fig.add_trace(go.Scatterpolar(
                    r=[metrics2[m] for m in common_metrics],
                    theta=common_metrics,
                    fill='toself',
                    name=name2
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                        ),
                    ),
                    title="Metrics Comparison",
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Technical score comparison
                score1 = metrics1.get('Technical Efficiency', 0)
                score2 = metrics2.get('Technical Efficiency', 0)
                
                # Bar chart for technical scores
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=[name1, name2],
                    y=[score1, score2],
                    text=[f"{score1:.1f}", f"{score2:.1f}"],
                    textposition='auto',
                    marker_color=['royalblue', 'lightseagreen']
                ))
                
                fig.update_layout(
                    title="Technical Score Comparison",
                    yaxis=dict(
                        title="Score",
                        range=[0, 100]
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Create a comparison table
                comparison_data = []
                for metric in common_metrics:
                    comparison_data.append({
                        'Metric': metric,
                        name1: f"{metrics1[metric]:.1f}" if isinstance(metrics1[metric], (int, float)) else metrics1[metric],
                        name2: f"{metrics2[metric]:.1f}" if isinstance(metrics2[metric], (int, float)) else metrics2[metric],
                        'Change': f"{metrics2[metric] - metrics1[metric]:.1f}" if isinstance(metrics1[metric], (int, float)) and isinstance(metrics2[metric], (int, float)) else "N/A"
                    })
                
                df = pd.DataFrame(comparison_data)
                st.dataframe(df, use_container_width=True)
            
            else:
                st.warning("No common numeric metrics found for comparison")
        else:
            st.warning("Metrics data not available for both sessions")
    
    with tab2:
        # Create time series comparison plots
        if data1 and data2:
            # Identify common metrics
            common_metrics = [key for key in data1 if key in data2]
            
            if common_metrics:
                # Let user select which metric to compare
                selected_metric = st.selectbox("Select Metric to Compare", common_metrics)
                
                if selected_metric in data1 and selected_metric in data2:
                    # Create a figure
                    fig = go.Figure()
                    
                    # Add time series for first session
                    fig.add_trace(go.Scatter(
                        y=data1[selected_metric],
                        mode='lines',
                        name=f"{name1}"
                    ))
                    
                    # Add time series for second session
                    fig.add_trace(go.Scatter(
                        y=data2[selected_metric],
                        mode='lines',
                        name=f"{name2}"
                    ))
                    
                    # Update layout
                    fig.update_layout(
                        title=f"{selected_metric} Comparison",
                        xaxis_title="Frame",
                        yaxis_title="Value",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"Selected metric {selected_metric} not found in both sessions")
            else:
                st.warning("No common metrics found for time series comparison")
        else:
            st.warning("Time series data not available for both sessions")
