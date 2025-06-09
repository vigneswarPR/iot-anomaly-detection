# frontend/streamlit_app.py

import streamlit as st
import requests
import pandas as pd
import time
import datetime

# --- Configuration ---
FLASK_BACKEND_URL = "http://127.0.0.1:5000"

st.set_page_config(layout="wide") # Use wide layout for better display

st.title("IoT Anomaly Detection Dashboard 📊")
st.markdown("Monitor real-time sensor data and blockchain-logged anomalies.")

# --- Function to fetch anomalies from Flask backend ---
def get_anomalies():
    try:
        response = requests.get(f"{FLASK_BACKEND_URL}/anomalies")
        response.raise_for_status() # Raise an exception for HTTP errors
        anomalies_data = response.json()
        print(f"DEBUG: Fetched anomalies from backend: {anomalies_data}") # Add this for debugging
        return anomalies_data
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to Flask backend at {FLASK_BACKEND_URL}. Please ensure it's running.")
        return []
    except Exception as e:
        st.error(f"Error fetching anomalies: {e}")
        return []

# --- Function to send simulated sensor data to Flask backend ---
# (This remains the same as your previous working version)
def send_sensor_data(sensor_id, temperature, humidity, pressure):
    payload = {
        "sensor_id": sensor_id,
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure
    }
    try:
        response = requests.post(f"{FLASK_BACKEND_URL}/sensor_data", json=payload)
        response.raise_for_status()
        result = response.json()
        return result
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to Flask backend at {FLASK_BACKEND_URL}. Please ensure it's running.")
        return {"status": "error", "message": "Backend not reachable"}
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return {"status": "error", "message": e.response.text}
    except Exception as e:
        st.error(f"Error sending data: {e}")
        return {"status": "error", "message": str(e)}

# --- Sidebar for Sensor Data Simulation ---
st.sidebar.header("Simulate Sensor Data")
with st.sidebar.form("sensor_form"):
    st.markdown("Enter sensor readings to test anomaly detection.")
    sim_sensor_id = st.text_input("Sensor ID", value=f"sensor_{int(time.time()) % 1000}")
    sim_temperature = st.number_input("Temperature (°C)", value=20.5, format="%.1f")
    sim_humidity = st.number_input("Humidity (%)", value=50.0, format="%.1f")
    sim_pressure = st.number_input("Pressure (hPa)", value=700.0, format="%.1f")

    submitted = st.form_submit_button("Send Data")
    if submitted:
        st.sidebar.write("Sending data...")
        response = send_sensor_data(sim_sensor_id, sim_temperature, sim_humidity, sim_pressure)
        if response.get("status") == "Anomaly Detected and Logged":
            st.sidebar.success(f"Anomaly detected and logged for {sim_sensor_id}! Tx initiated.")
        elif response.get("status") == "Data Processed: No Anomaly":
            st.sidebar.info(f"Data processed for {sim_sensor_id}. No anomaly detected.")
        else:
            st.sidebar.warning(f"Error sending data: {response.get('message', 'Unknown error')}")
        st.sidebar.json(response) # Display full response for debugging

# --- Main Dashboard Content ---
st.header("Logged Anomalies (from Blockchain)")

# Using st.empty() and st.button for manual refresh, as before.
# We'll add an optional auto-refresh later if needed.
placeholder = st.empty()

# Function to refresh data and update dashboard
def refresh_anomalies_dashboard():
    with placeholder.container():
        st.subheader("Latest Anomalies")
        anomalies = get_anomalies() # Fetches data from Flask backend

        if anomalies:
            # Create DataFrame directly from the list of dictionaries
            df = pd.DataFrame(anomalies)

            # Ensure expected columns are present and rename for display
            expected_columns = ['timestamp', 'sensor_id', 'data_value', 'anomaly_type', 'explanation']
            if all(col in df.columns for col in expected_columns):
                # Convert Unix timestamp to readable datetime
                df['Time (UTC)'] = pd.to_datetime(df['timestamp'], unit='s')

                # Select and reorder columns for display
                df_display = df[[
                    'Time (UTC)',
                    'sensor_id',
                    'data_value',
                    'anomaly_type',
                    'explanation'
                ]].copy() # .copy() to avoid SettingWithCopyWarning

                # Rename columns for better readability in the UI
                df_display.columns = [
                    'Time (UTC)',
                    'Sensor ID',
                    'Data Value', # Changed from 'Value' to 'Data Value' for clarity
                    'Anomaly Type',
                    'Explanation'
                ]
                st.dataframe(df_display, use_container_width=True, height=300)
            else:
                st.warning("Anomaly data is missing expected columns. Showing raw data for debugging.")
                st.json(anomalies) # Display raw JSON for debugging

        else:
            st.info("No anomalies logged on the blockchain yet. Simulate some data!")

# Auto-refresh mechanism (optional, can be uncommented)
# If you want auto-refresh, place this in a loop or use Streamlit's rerun.
# For a hackathon, often a manual refresh button is sufficient to avoid complex state management.
# You could use st.rerun() in a background thread or based on a timer, but it can be tricky.
# For now, let's stick to the button to ensure clear debugging.

if st.button("Refresh Anomalies Now"):
    refresh_anomalies_dashboard()
else:
    # Initial load of anomalies when the app starts
    refresh_anomalies_dashboard()


st.write("---")
st.subheader("About This Dashboard")
st.info("""
This dashboard allows you to:
- Simulate IoT sensor data through the sidebar. This data is sent to a Flask backend.
- The Flask backend runs an Isolation Forest model for anomaly detection.
- If an anomaly is detected, it's logged on the Ethereum blockchain via your smart contract.
- The "Logged Anomalies" section fetches and displays all anomalies currently stored on the blockchain.
""")