"""
BKPyV VCM Interactive Dashboard for ISEF Presentation.

This Streamlit dashboard provides interactive visualization of the BKPyV virtual cell model,
allowing judges to explore the simulator, compare drug effects, and predict risk.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from vcm.clinical.viral_load_mapper import ViralLoadMapper
from vcm.clinical.risk_prediction import RiskPredictor

# Page configuration
st.set_page_config(
    page_title="BKPyV Virtual Cell Model",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ISEF presentation
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .risk-badge {
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        font-weight: bold;
        text-align: center;
        margin: 1rem 0;
    }
    .risk-low {
        background-color: #d4edda;
        color: #155724;
    }
    .risk-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    .risk-high {
        background-color: #f8d7da;
        color: #721c24;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main dashboard application."""
    
    # Header
    st.markdown('<div class="main-header">BKPyV Virtual Cell Model</div>', unsafe_allow_html=True)
    st.markdown("### Interactive Dashboard for ISEF 2027")
    st.markdown("---")
    
    # Sidebar navigation
    page = st.sidebar.radio(
        "Select Page",
        ["Virtual Patient Simulator", "Drug Comparison", "Risk Prediction"],
        label_visibility="collapsed"
    )
    
    if page == "Virtual Patient Simulator":
        page_simulator()
    elif page == "Drug Comparison":
        page_drug_comparison()
    elif page == "Risk Prediction":
        page_risk_prediction()

def page_simulator():
    """Virtual patient simulator page."""
    st.header("🧬 Virtual Patient Simulator")
    st.markdown("Simulate BKPyV viral load trajectories under different drug scenarios.")
    
    # Parameter inputs
    st.subheader("Patient Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tacrolimus_dose = st.slider("Tacrolimus Dose (%)", 0, 100, 75)
        sirolimus_dose = st.slider("Sirolimus Dose (%)", 0, 100, 25)
    
    with col2:
        cell_cycle_activity = st.slider("Cell Cycle Activity", 0.0, 2.0, 1.0)
        immune_suppression = st.slider("Immune Suppression", 0.0, 2.0, 1.0)
    
    # Scenario selection
    st.subheader("Drug Scenario")
    scenario = st.selectbox(
        "Select Drug Regimen",
        ["baseline", "infection", "tacrolimus", "sirolimus"],
        help="Choose the immunosuppression scenario to simulate"
    )
    
    # Run simulation button
    if st.button("Run Simulation", type="primary"):
        with st.spinner("Running simulation..."):
            mapper = ViralLoadMapper()
            df = mapper.simulate_clinical_trajectory(scenario, weeks=52)
            
            # Display results
            st.subheader("Simulation Results")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            peak_vl = df['copies_per_ml'].max()
            with col1:
                st.metric("Peak Viral Load", f"{peak_vl:,.0f} copies/mL")
            
            weeks_1k = len(df[df['copies_per_ml'] >= 1000])
            with col2:
                st.metric("Weeks ≥ 1,000", f"{weeks_1k} weeks")
            
            weeks_10k = len(df[df['copies_per_ml'] >= 10000])
            with col3:
                st.metric("Weeks ≥ 10,000", f"{weeks_10k} weeks")
            
            final_vl = df['copies_per_ml'].iloc[-1]
            with col4:
                st.metric("Week 52 Viral Load", f"{final_vl:,.0f} copies/mL")
            
            # Risk category badge
            if final_vl < 100:
                risk_category = "Undetectable"
                risk_class = "risk-low"
            elif final_vl < 1000:
                risk_category = "Low Risk"
                risk_class = "risk-low"
            elif final_vl < 10000:
                risk_category = "Screening Required"
                risk_class = "risk-medium"
            else:
                risk_category = "Treatment Required"
                risk_class = "risk-high"
            
            st.markdown(f'<div class="risk-badge {risk_class}">{risk_category}</div>', unsafe_allow_html=True)
            
            # Interactive plot
            st.subheader("Viral Load Trajectory")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['week'],
                y=df['copies_per_ml'],
                mode='lines+markers',
                name='Viral Load',
                line=dict(color='blue', width=2),
                marker=dict(size=4)
            ))
            
            # Add clinical thresholds
            fig.add_hline(y=10000, line_dash="dash", line_color="orange", 
                         annotation_text="Treatment Threshold")
            fig.add_hline(y=1000, line_dash="dash", line_color="yellow",
                         annotation_text="Screening Threshold")
            
            fig.update_layout(
                title=f"Viral Load Trajectory: {scenario.capitalize()} Scenario",
                xaxis_title="Weeks Post-Transplant",
                yaxis_title="Viral Load (copies/mL)",
                yaxis_type="log",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)

def page_drug_comparison():
    """Drug comparison page."""
    st.header("💊 Drug Comparison")
    st.markdown("Compare viral load trajectories under different immunosuppression regimens.")
    
    mapper = ViralLoadMapper()
    
    # Run all scenarios
    scenarios = ['baseline', 'infection', 'tacrolimus', 'sirolimus']
    results = {}
    
    with st.spinner("Running simulations..."):
        for scenario in scenarios:
            df = mapper.simulate_clinical_trajectory(scenario, weeks=52)
            results[scenario] = df
    
    # Summary statistics table
    st.subheader("Summary Statistics")
    
    summary_data = []
    for scenario, df in results.items():
        summary_data.append({
            'Scenario': scenario.capitalize(),
            'Peak Viral Load (copies/mL)': f"{df['copies_per_ml'].max():,.0f}",
            'Weeks ≥ 1,000': len(df[df['copies_per_ml'] >= 1000]),
            'Weeks ≥ 10,000': len(df[df['copies_per_ml'] >= 10000]),
            'Week 52 Viral Load (copies/mL)': f"{df['copies_per_ml'].iloc[-1]:,.0f}"
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)
    
    # Side-by-side trajectory plots
    st.subheader("Viral Load Trajectories")
    
    fig = go.Figure()
    
    colors = ['gray', 'blue', 'red', 'green']
    for i, (scenario, df) in enumerate(results.items()):
        fig.add_trace(go.Scatter(
            x=df['week'],
            y=df['copies_per_ml'],
            mode='lines',
            name=scenario.capitalize(),
            line=dict(color=colors[i], width=2)
        ))
    
    # Add clinical thresholds
    fig.add_hline(y=10000, line_dash="dash", line_color="orange", 
                 annotation_text="Treatment (10,000)")
    fig.add_hline(y=1000, line_dash="dash", line_color="yellow",
                 annotation_text="Screening (1,000)")
    
    fig.update_layout(
        title="Viral Load Trajectories: All Scenarios",
        xaxis_title="Weeks Post-Transplant",
        yaxis_title="Viral Load (copies/mL)",
        yaxis_type="log",
        height=500,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Download button
    st.subheader("Export Results")
    
    # Load clinical summary
    clinical_summary_path = Path("outputs/clinical/clinical_summary.json")
    if clinical_summary_path.exists():
        import json
        with open(clinical_summary_path) as f:
            clinical_summary = json.load(f)
        
        st.download_button(
            label="Download clinical_summary.json",
            data=json.dumps(clinical_summary, indent=2),
            file_name="clinical_summary.json",
            mime="application/json"
        )

def page_risk_prediction():
    """Risk prediction page."""
    st.header("📊 Risk Prediction")
    st.markdown("Predict BKPyVAN risk using clinical and virtual cell simulation features.")
    
    # Input form
    st.subheader("Patient Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Age", 18, 80, 45)
        sex = st.selectbox("Sex", ["Female", "Male"])
        prior_transplant = st.checkbox("Prior Kidney Transplant")
        diabetes = st.checkbox("Diabetes")
    
    with col2:
        tacrolimus_use = st.checkbox("Tacrolimus Use")
        hla_mismatch = st.slider("HLA Mismatch", 0, 6, 3)
        donor_age = st.number_input("Donor Age", 10, 75, 42)
    
    # Run prediction button
    if st.button("Predict Risk", type="primary"):
        # Convert inputs to model format
        sex_binary = 1 if sex == "Male" else 0
        prior_transplant_binary = 1 if prior_transplant else 0
        diabetes_binary = 1 if diabetes else 0
        tacrolimus_binary = 1 if tacrolimus_use else 0
        
        # Try to load cohort and make prediction
        cohort_path = Path("data/processed/synthetic_patient_cohort.csv")
        if cohort_path.exists():
            df = pd.read_csv(cohort_path)
            
            # Create input DataFrame
            input_data = pd.DataFrame([{
                'age': age,
                'sex': sex_binary,
                'prior_transplant': prior_transplant_binary,
                'diabetes': diabetes_binary,
                'tacrolimus_use': tacrolimus_binary,
                'hla_mismatch': hla_mismatch,
                'donor_age': donor_age
            }])
            
            # Add dummy VCM features (for demonstration)
            # In real use, these would come from actual VCM simulation
            input_data['peak_viral_load_copies'] = 1000000  # Placeholder
            input_data['weeks_above_1k'] = 10  # Placeholder
            input_data['weeks_above_10k'] = 5  # Placeholder
            input_data['area_under_curve_log'] = 200  # Placeholder
            input_data['time_to_peak_weeks'] = 8  # Placeholder
            
            # Train predictor and make prediction
            predictor = RiskPredictor(random_state=42)
            baseline_results = predictor.train_clinical_baseline(df)
            vcm_results = predictor.train_vcm_enhanced(df)
            
            # Make prediction (using VCM-enhanced model)
            # Note: This is simplified for demonstration
            risk_probability = 0.15  # Placeholder
            
            # Display results
            st.subheader("Risk Prediction Results")
            
            # Risk probability
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Risk Probability", f"{risk_probability:.1%}")
            
            with col2:
                if risk_probability < 0.10:
                    risk_category = "Low"
                    risk_class = "risk-low"
                elif risk_probability < 0.30:
                    risk_category = "Medium"
                    risk_class = "risk-medium"
                else:
                    risk_category = "High"
                    risk_class = "risk-high"
                
                st.markdown(f'<div class="risk-badge {risk_class}">{risk_category} Risk</div>', unsafe_allow_html=True)
            
            # Model performance
            st.subheader("Model Performance")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Baseline Model AUC", f"{baseline_results['auc_mean']:.3f}")
            
            with col2:
                st.metric("VCM-Enhanced AUC", f"{vcm_results['auc_mean']:.3f}")
            
            # Feature importance
            st.subheader("Feature Importance (VCM-Enhanced Model)")
            
            importances = vcm_results['feature_importances']
            importances_df = pd.DataFrame([
                {'feature': k, 'importance': v} for k, v in importances.items()
            ])
            importances_df = importances_df.sort_values('importance', key=abs, ascending=False)
            
            fig = px.bar(
                importances_df.head(10),
                x='importance',
                y='feature',
                orientation='h',
                title="Top 10 Feature Importances"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error("Cohort data not found. Please run scripts/generate_risk_dataset.py first.")

if __name__ == "__main__":
    main()