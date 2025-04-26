import streamlit as st
from kafka import KafkaConsumer
import mlflow
import joblib
import json
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Streamlit page config
st.set_page_config(page_title="📡 Real-Time Model Comparison", layout="wide")
st.title("📡 Live Kafka Stream | 🧠 XGBoost vs Snapshot Ensemble")
st_autorefresh(interval=2000, key="refresh")

# MLflow config
MLFLOW_TRACKING_URI = "http://mlflow:5000"
XGB_RUN_ID = "8ed0c6a352e24897b08654b16ecae0ad"
SNAPSHOT_RUN_ID = "3328f09e5e344da3b32166292b249cdb"
XGB_ARTIFACT = "xgb_final_model.pkl"
SNAPSHOT_ARTIFACT = "snapshot_final_models.pkl"

@st.cache_resource
def load_models():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    try:
        xgb_path = mlflow.artifacts.download_artifacts(run_id=XGB_RUN_ID, artifact_path=XGB_ARTIFACT)
        snapshot_path = mlflow.artifacts.download_artifacts(run_id=SNAPSHOT_RUN_ID, artifact_path=SNAPSHOT_ARTIFACT)
        
        xgb_model = joblib.load(xgb_path)
        snapshot_models = joblib.load(snapshot_path)
        
        st.success(f"✅ Loaded XGBoost model and {len(snapshot_models)} snapshot models")
        return xgb_model, snapshot_models
    except Exception as e:
        st.error(f"❌ Error loading models: {e}")
        return None, None

xgb_model, snapshot_models = load_models()

# Kafka config
KAFKA_TOPIC = "Raw_data"
BOOTSTRAP_SERVERS = ["ed-kafka:29092"]

@st.cache_resource
def get_consumer():
    try:
        return KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            auto_offset_reset="latest",
            enable_auto_commit=False,
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            group_id=None
        )
    except Exception as e:
        st.error(f"❌ Kafka connection error: {e}")
        return None

consumer = get_consumer()

# Initialize session state
if "xgb_history" not in st.session_state:
    st.session_state.xgb_history = []
if "snap_history" not in st.session_state:
    st.session_state.snap_history = []
if "true_labels" not in st.session_state:
    st.session_state.true_labels = []
if "timeline" not in st.session_state:
    st.session_state.timeline = []
if "snap_breakdown" not in st.session_state:
    st.session_state.snap_breakdown = []

if consumer is not None:
    messages = consumer.poll(timeout_ms=2000)
    
    
    if messages:
        for tp, msgs in messages.items():
            for msg in msgs:
                st.markdown("### 📥 Incoming Data:")
                st.json(msg.value)

                

                try:
                    df = pd.DataFrame([msg.value])
                    if "label" in df.columns:
                        true_label = df["label"].iloc[0]
                        df = df.drop("label", axis=1)
                    else:
                        true_label = None


                    # 📉 ECG Signal Plot
                    st.markdown("#### 🫀 Incoming ECG Signal (Simulated Time-Series)")

                    try:
                        ecg_signal = df.drop(columns=["label"], errors="ignore").values.flatten()
                        signal_df = pd.DataFrame({
                            "Time (a.u.)": np.arange(len(ecg_signal)),
                            "Amplitude": ecg_signal
                        })

                        fig = px.line(
                            signal_df,
                            x="Time (a.u.)",
                            y="Amplitude",
                            title="🫀 ECG Signal Waveform",
                            labels={"Amplitude": "ECG Value", "Time (a.u.)": "Sample Index"},
                            height=300
                        )

                        fig.update_traces(line=dict(color="royalblue"))
                        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))

                        st.plotly_chart(fig, use_container_width=True)

                    except Exception as e:
                        st.warning(f"Unable to plot ECG signal: {e}")


                    # Make predictions
                    xgb_pred = int(xgb_model.predict(df)[0])
                    snap_preds = np.array([model.predict(df)[0] for model in snapshot_models])
                    snap_pred = int(round(snap_preds.mean()))
                    snap_std = float(snap_preds.std())

                    # Update session state
                    timestamp = datetime.now()
                    st.session_state.xgb_history.append(xgb_pred)
                    st.session_state.snap_history.append(snap_pred)
                    st.session_state.timeline.append(timestamp)
                    st.session_state.snap_breakdown.append(snap_preds)
                    
                    if true_label is not None:
                        st.session_state.true_labels.append(true_label)

                    # Display predictions
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success(f"🧠 XGBoost Prediction: `{xgb_pred}`")
                    with col2:
                        st.success(f"📊 Snapshot Ensemble Prediction: `{snap_pred}` (Std: {snap_std:.2f})")

                    # Visualizations
                    with st.expander("📊 Live Performance Analysis", expanded=True):
                        # Prediction Timeline
                        st.markdown("#### Prediction Timeline")
                        timeline_df = pd.DataFrame({
                            "Time": st.session_state.timeline,
                            "XGBoost": st.session_state.xgb_history,
                            "Snapshot Ensemble": st.session_state.snap_history
                        }).set_index("Time")
                        st.line_chart(timeline_df,color=["#fd0", "#f0f"])

                        # Accuracy tracking (if true labels available)
                        if st.session_state.true_labels:
                            st.markdown("#### Cumulative Accuracy")
                            accuracy_df = pd.DataFrame({
                                "Time": st.session_state.timeline,
                                "XGBoost Accuracy": np.cumsum(
                                    np.array(st.session_state.xgb_history) == np.array(st.session_state.true_labels)
                                ) / (np.arange(len(st.session_state.xgb_history)) + 1),
                                "Snapshot Accuracy": np.cumsum(
                                    np.array(st.session_state.snap_history) == np.array(st.session_state.true_labels)
                                ) / (np.arange(len(st.session_state.snap_history)) + 1)
                            }).set_index("Time")
                            st.line_chart(accuracy_df,color=["#fd0", "#f0f"])

                        # Model agreement visualization
                        st.markdown("#### Snapshot Model Agreement")
                        latest_breakdown = st.session_state.snap_breakdown[-1]
                        breakdown_df = pd.DataFrame({
                            "Model": [f"Model {i+1}" for i in range(len(latest_breakdown))],
                            "Prediction": latest_breakdown
                        })
                        fig = px.bar(breakdown_df, x="Model", y="Prediction", 
                                    title="Individual Snapshot Model Predictions")
                        st.plotly_chart(fig, use_container_width=True)

                        # Feature importance
                        st.markdown("#### Feature Importance (Snapshot Ensemble Average)")
                        if hasattr(snapshot_models[0], 'feature_importances_'):
                            feature_importances = np.mean(
                                [model.feature_importances_ for model in snapshot_models], 
                                axis=0
                            )
                            importance_df = pd.DataFrame({
                                "Feature": df.columns,
                                "Importance": feature_importances
                            }).sort_values("Importance", ascending=False).head(10)
                            
                            import plotly.express as px

                            fig = px.bar(
                                importance_df,
                                x="Importance",
                                y="Feature",
                                orientation='h',
                                title="🔬 Top 10 Feature Importances (Snapshot Ensemble)",
                                color="Importance",
                                color_continuous_scale="Blues"
                            )

                            fig.update_layout(yaxis=dict(autorange="reversed"))  # highest importance on top
                            st.plotly_chart(fig, use_container_width=True)

                        else:
                            st.info("Feature importance not available for this model type")
                        

                        # Feature importance
                        st.markdown("#### Feature Importance (XGBoost Model)")
                        if hasattr(xgb_model, 'feature_importances_'):
                            feature_importances = xgb_model.feature_importances_
                            importance_df = pd.DataFrame({
                                "Feature": df.columns,
                                "Importance": feature_importances
                            }).sort_values("Importance", ascending=False).head(10)

                            fig = px.bar(
                                importance_df,
                                x="Importance",
                                y="Feature",
                                orientation='h',
                                title="🔬 Top 10 Feature Importances (XGBoost)",
                                color="Importance",
                                color_continuous_scale="Viridis"
                            )

                            fig.update_layout(yaxis=dict(autorange="reversed"))  # highest on top
                            st.plotly_chart(fig, use_container_width=True)

                        else:
                            st.info("Feature importance not available for the XGBoost model.")


                except Exception as e:
                    st.error(f"❌ Processing error: {str(e)}")
    else:
        st.info("📭 No new messages in the last refresh")
else:
    st.error("Failed to initialize Kafka consumer")