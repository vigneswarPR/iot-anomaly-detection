# generate_normal_data.py
import requests
import time
import numpy as np
from collections import deque
import json  # To save the generated data
import datetime
# --- Configuration (Matching your data_simulator.py and app.py) ---
# Assuming these match the order and number of features your sensor sends
FEATURES_PER_READING = 3  # temperature, humidity, pressure
LAG_FEATURES_COUNT = 3  # Current reading + 2 previous readings = 3 total readings in history
TOTAL_FEATURES_FOR_MODEL = FEATURES_PER_READING * LAG_FEATURES_COUNT

# How many "normal" data points to collect for training (aim for 1000-5000+ for better results)
NUM_NORMAL_READINGS_TO_COLLECT = 2000

# Path to save the generated normal data
OUTPUT_FILE = 'normal_training_data_with_lags.json'

print(
    f"Generating {NUM_NORMAL_READINGS_TO_COLLECT} normal data points with {LAG_FEATURES_COUNT - 1} lagged features...")
print(f"Each training sample will have {TOTAL_FEATURES_FOR_MODEL} features.")

# --- Simulate Normal Data (similar to data_simulator.py, but without anomaly injection) ---
# You'll need to adapt this to actually GET data from your simulator if it were a separate service,
# OR you can copy/paste the core generation logic from data_simulator.py here.
# For simplicity and self-containment, let's copy the core generation logic here.

# SENSOR_PROFILES from data_simulator.py (for generating patterns)
SENSOR_PROFILES_FOR_NORMAL = {
    "temp_sensor_01": {
        "base_temp": 25.0, "temp_daily_amplitude": 5.0, "temp_noise_std": 0.5,
        "base_humidity": 60.0, "hum_daily_amplitude": 3.0, "hum_noise_std": 0.8,
        "base_pressure": 1010.0, "pres_daily_amplitude": 2.0, "pres_noise_std": 0.3
    },
    # Add other sensor profiles from your data_simulator.py here if needed for normal data
    # "temp_sensor_02": {...}
}


def generate_single_realistic_reading(timestamp_obj, profile):
    """Generates a single sensor reading with daily cycles and noise."""
    hour_of_day = timestamp_obj.hour + timestamp_obj.minute / 60.0

    temp_cycle = profile["temp_daily_amplitude"] * np.sin(2 * np.pi * (hour_of_day - 8) / 24)
    hum_cycle = profile["hum_daily_amplitude"] * np.sin(2 * np.pi * (hour_of_day - 10) / 24)
    pres_cycle = profile["pres_daily_amplitude"] * np.pi * (hour_of_day - 6) / 24

    temperature = profile["base_temp"] + temp_cycle + np.random.normal(0, profile["temp_noise_std"])
    humidity = profile["base_humidity"] + hum_cycle + np.random.normal(0, profile["hum_noise_std"])
    pressure = profile["base_pressure"] + pres_cycle + np.random.normal(0, profile["pres_noise_std"])

    return temperature, humidity, pressure


# --- Data Collection Logic ---
normal_lagged_data = []
history_buffers = {
    sensor_id: deque(maxlen=LAG_FEATURES_COUNT)
    for sensor_id in SENSOR_PROFILES_FOR_NORMAL.keys()
}

# Simulate time progression for normal data collection
current_sim_time = datetime.datetime.now()

while len(normal_lagged_data) < NUM_NORMAL_READINGS_TO_COLLECT:
    for sensor_id, profile in SENSOR_PROFILES_FOR_NORMAL.items():
        # Generate a normal reading for the current simulated time
        temperature, humidity, pressure = generate_single_realistic_reading(current_sim_time, profile)
        current_reading = (temperature, humidity, pressure)

        history_buffers[sensor_id].append(current_reading)

        # If we have enough history, create the lagged feature vector
        if len(history_buffers[sensor_id]) == LAG_FEATURES_COUNT:
            # Flatten the deque into a single row for the model
            # Order: [current_T, current_H, current_P, lag1_T, lag1_H, lag1_P, ...]
            flat_features = []
            for reading in list(history_buffers[sensor_id]):  # Convert deque to list to iterate for flattening
                flat_features.extend(reading)

            normal_lagged_data.append(flat_features)

            if len(normal_lagged_data) % 100 == 0:
                print(f"Collected {len(normal_lagged_data)} normal data points...")

            if len(normal_lagged_data) >= NUM_NORMAL_READINGS_TO_COLLECT:
                break  # Stop if we've collected enough

    current_sim_time += datetime.timedelta(seconds=2)  # Advance time by a small interval

print(f"\nFinished collecting {len(normal_lagged_data)} normal data points.")

# Convert to NumPy array
NORMAL_DATA_FOR_MODEL = np.array(normal_lagged_data)
print("Shape of generated NORMAL_DATA_FOR_MODEL:", NORMAL_DATA_FOR_MODEL.shape)

# Save to JSON for easy loading in app.py
with open(OUTPUT_FILE, 'w') as f:
    json.dump(NORMAL_DATA_FOR_MODEL.tolist(), f)  # Convert numpy array to list for JSON
print(f"Generated normal data saved to {OUTPUT_FILE}")