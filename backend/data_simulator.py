# data_simulator.py
import requests
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# --- Configuration ---
FLASK_BACKEND_URL = "http://127.0.0.1:5000/sensor_data"
SIMULATION_INTERVAL_SECONDS = 2  # How often to send data (e.g., every 2 seconds)
SIMULATION_DURATION_SECONDS = 1200  # How long to run the simulation (e.g., 20 minutes)

# Sensor Profiles (Normal, Faulty1, Faulty2)
# These define baseline values and their variations
SENSOR_PROFILES = {
    "temp_sensor_01": {
        "base_temp": 25.0, "temp_daily_amplitude": 5.0, "temp_noise_std": 0.5,
        "base_humidity": 60.0, "hum_daily_amplitude": 3.0, "hum_noise_std": 0.8,
        "base_pressure": 1010.0, "pres_daily_amplitude": 2.0, "pres_noise_std": 0.3
    },
    "temp_sensor_02": {
        "base_temp": 22.0, "temp_daily_amplitude": 4.0, "temp_noise_std": 0.6,
        "base_humidity": 55.0, "hum_daily_amplitude": 2.5, "hum_noise_std": 0.7,
        "base_pressure": 1005.0, "pres_daily_amplitude": 1.5, "pres_noise_std": 0.4
    },
    "humidity_sensor_01": {  # Example for a different primary sensor type
        "base_temp": 28.0, "temp_daily_amplitude": 3.0, "temp_noise_std": 0.7,
        "base_humidity": 70.0, "hum_daily_amplitude": 6.0, "hum_noise_std": 1.0,  # Higher humidity variation
        "base_pressure": 1012.0, "pres_daily_amplitude": 2.5, "pres_noise_std": 0.5
    }
}


# --- Data Generation Functions ---

def generate_realistic_reading(timestamp_obj, profile):
    """Generates a single sensor reading with daily cycles and noise."""
    hour_of_day = timestamp_obj.hour + timestamp_obj.minute / 60.0

    # Simple sine wave for daily cycle (peak around midday)
    temp_cycle = profile["temp_daily_amplitude"] * np.sin(2 * np.pi * (hour_of_day - 8) / 24)
    hum_cycle = profile["hum_daily_amplitude"] * np.sin(2 * np.pi * (hour_of_day - 10) / 24)
    pres_cycle = profile["pres_daily_amplitude"] * np.pi * (hour_of_day - 6) / 24  # More linear trend for pressure

    temperature = profile["base_temp"] + temp_cycle + np.random.normal(0, profile["temp_noise_std"])
    humidity = profile["base_humidity"] + hum_cycle + np.random.normal(0, profile["hum_noise_std"])
    pressure = profile["base_pressure"] + pres_cycle + np.random.normal(0, profile["pres_noise_std"])

    return temperature, humidity, pressure


def inject_anomaly(temp, hum, pres, anomaly_type):
    """Injects different types of anomalies."""
    explanation = f"Normal operation"
    if anomaly_type == "point":
        # Sudden spike in temperature
        temp += random.uniform(50, 100)  # Extremely high temp
        explanation = "Point Anomaly: Extreme temperature spike"
    elif anomaly_type == "contextual":
        # Temp is normal for summer, but abnormal for winter (simulated as low base temp)
        # We'll apply this when the base temp for simulation is set low
        temp = random.uniform(28, 32)  # High temp but "normal" value. Context: it's winter.
        hum = random.uniform(85, 95)  # Also high humidity
        explanation = "Contextual Anomaly: High temp/hum in 'cold' context"
    elif anomaly_type == "change_point_high":
        # Sustained higher values
        temp += random.uniform(10, 15)
        hum += random.uniform(8, 12)
        explanation = "Change Point: Sustained high readings"
    elif anomaly_type == "change_point_low":
        # Sustained lower values
        temp -= random.uniform(10, 15)
        hum -= random.uniform(8, 12)
        explanation = "Change Point: Sustained low readings"
    # More anomaly types can be added

    return temp, hum, pres, explanation


# --- Simulation Logic ---

def run_simulation():
    print(f"Starting sensor data simulation. Sending to {FLASK_BACKEND_URL}")
    print(f"Interval: {SIMULATION_INTERVAL_SECONDS}s, Duration: {SIMULATION_DURATION_SECONDS / 60} minutes")

    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=SIMULATION_DURATION_SECONDS)

    current_time = start_time

    # Store the state of each sensor profile for continuous simulation
    sensor_states = {sensor_id: {"profile": profile, "current_anomaly_type": None, "anomaly_countdown": 0}
                     for sensor_id, profile in SENSOR_PROFILES.items()}

    while current_time < end_time:
        for sensor_id, state in sensor_states.items():
            profile = state["profile"]

            # --- Anomaly Injection Logic ---
            # Randomly decide to inject an anomaly or revert to normal
            if state["anomaly_countdown"] > 0:
                state["anomaly_countdown"] -= 1
            else:
                # 5% chance to start a new anomaly every interval
                if random.random() < 0.05:
                    anomaly_types = ["point", "contextual", "change_point_high", "change_point_low"]
                    state["current_anomaly_type"] = random.choice(anomaly_types)
                    state["anomaly_countdown"] = random.randint(3, 10)  # Anomaly lasts for 3-10 intervals
                    print(f"\n--- Injecting '{state['current_anomaly_type']}' anomaly for {sensor_id} ---")
                else:
                    state["current_anomaly_type"] = None  # No active anomaly

            # Generate base reading
            temperature, humidity, pressure = generate_realistic_reading(current_time, profile)

            # Inject anomaly if active
            anomaly_explanation = "Normal operation"
            if state["current_anomaly_type"]:
                temperature, humidity, pressure, anomaly_explanation = inject_anomaly(
                    temperature, humidity, pressure, state["current_anomaly_type"]
                )

            # Prepare data payload
            payload = {
                "sensor_id": sensor_id,
                "temperature": round(temperature, 2),
                "humidity": round(humidity, 2),
                "pressure": round(pressure, 2),
                "explanation_from_simulator": anomaly_explanation  # For debugging/context
            }

            # Send data to Flask backend
            try:
                response = requests.post(FLASK_BACKEND_URL, json=payload)
                response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
                print(
                    f"[{current_time.strftime('%H:%M:%S')}] {sensor_id}: Temp={payload['temperature']:.2f}°C, Hum={payload['humidity']:.2f}%, Pres={payload['pressure']:.2f}hPa - Status: {response.json().get('status', 'Unknown')}")
            except requests.exceptions.ConnectionError:
                print(f"❌ Error: Could not connect to Flask backend at {FLASK_BACKEND_URL}. Is it running?")
                return  # Exit simulation if backend is down
            except requests.exceptions.HTTPError as e:
                print(f"❌ HTTP Error for {sensor_id}: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"❌ An unexpected error occurred for {sensor_id}: {e}")

        current_time += timedelta(seconds=SIMULATION_INTERVAL_SECONDS)
        time.sleep(SIMULATION_INTERVAL_SECONDS)

    print("\nSimulation finished.")


if __name__ == "__main__":
    run_simulation()