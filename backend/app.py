# app.py (UPDATED)
import json
import os
import time
import datetime
import numpy as np
from flask import Flask, request, jsonify
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from sklearn.ensemble import IsolationForest
import joblib
from collections import deque  # Import deque for history buffer

# --- CONFIGURATION ---
CONTRACT_ADDRESS = '0x7CdD0D08223D39840c8EB9A22077c64688f8ce09'  # Your deployed contract address
ABI_FILE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
        'smart_contracts',
        'artifacts',
        'contracts',
        'anomaly_logger.sol',
        'AnomalyLogger.json'
    )
)
GANACHE_URL = 'http://127.0.0.1:8545'

# --- NEW: Time Series Configuration ---
FEATURES_PER_READING = 3  # temperature, humidity, pressure
LAG_FEATURES_COUNT = 3  # Current reading + 2 previous readings. So, 3 readings total.
TOTAL_FEATURES_FOR_MODEL = FEATURES_PER_READING * LAG_FEATURES_COUNT
MAX_HISTORY_LENGTH = LAG_FEATURES_COUNT  # Only need enough to form the feature vector

# This dictionary will store a deque (double-ended queue) for each sensor_id
sensor_data_history = {}  # Key: sensor_id, Value: deque of (temp, hum, pres) tuples

# --- WEB3 SETUP (Remains the same) ---
try:
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer = 0)
    if w3.is_connected():
        print(f"✅ Successfully connected to Ganache at {GANACHE_URL}")
    else:
        print("❌ Failed to connect to Ganache. Please ensure Ganache is running.")
        exit()
except Exception as e:
    print(f"❌ Error during Web3 setup: {e}")
    exit()

try:
    with open(ABI_FILE_PATH, 'r') as f:
        abi_json = json.load(f)
        CONTRACT_ABI = abi_json['abi']
    print(f"✅ ABI loaded from: {ABI_FILE_PATH}")
except FileNotFoundError:
    print(f"❌ ABI file not found at: {ABI_FILE_PATH}")
    print("Please ensure you have compiled your smart contract (`npx hardhat compile`)")
    print("and the ABI_FILE_PATH in this script is correct.")
    exit()
except json.JSONDecodeError:
    print(f"❌ Error decoding JSON from ABI file: {ABI_FILE_PATH}")
    exit()

try:
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
    print(f"✅ Contract instance created for address: {CONTRACT_ADDRESS}")
except Exception as e:
    print(f"❌ Error creating contract instance: {e}")
    print("Please check CONTRACT_ADDRESS and CONTRACT_ABI.")
    exit()

SENDER_ACCOUNT = w3.eth.accounts[0]
print(f"Using sender account: {SENDER_ACCOUNT}")

# --- ANOMALY DETECTION MODEL SETUP ---
MODEL_PATH = 'anomaly_detection_model.joblib'
NORMAL_DATA_FILE = 'normal_training_data_with_lags.json'  # Path to your generated normal data


def train_or_load_model():
    """Trains an Isolation Forest model or loads it if it exists."""
    global anomaly_model
    if os.path.exists(MODEL_PATH):
        anomaly_model = joblib.load(MODEL_PATH)
        print(f"✅ Anomaly detection model loaded from {MODEL_PATH}")
    else:
        print("💡 Training new Isolation Forest model...")

        # Load the generated normal data
        try:
            with open(NORMAL_DATA_FILE, 'r') as f:
                loaded_normal_data = json.load(f)
            # Ensure it's a numpy array with correct shape
            NORMAL_DATA_FOR_TRAINING = np.array(loaded_normal_data)

            if NORMAL_DATA_FOR_TRAINING.shape[1] != TOTAL_FEATURES_FOR_MODEL:
                print(
                    f"❌ Error: Loaded normal data has {NORMAL_DATA_FOR_TRAINING.shape[1]} features, but expected {TOTAL_FEATURES_FOR_MODEL}.")
                print("Please re-run generate_normal_data.py with correct settings.")
                exit()
            print(f"Loaded {NORMAL_DATA_FOR_TRAINING.shape[0]} normal data points for training.")
        except FileNotFoundError:
            print(f"❌ Normal data file not found at: {NORMAL_DATA_FILE}")
            print("Please run `generate_normal_data.py` first to create the training data.")
            exit()
        except Exception as e:
            print(f"❌ Error loading normal training data: {e}")
            exit()

        anomaly_model = IsolationForest(contamination=0.01, random_state=42)  # Start with a lower contamination
        anomaly_model.fit(NORMAL_DATA_FOR_TRAINING)  # Train with the generated normal data
        joblib.dump(anomaly_model, MODEL_PATH)
        print(f"✅ Anomaly detection model trained and saved to {MODEL_PATH}")


# Call this once at startup
train_or_load_model()


# --- BLOCKCHAIN INTERACTION FUNCTIONS (Remains the same) ---
def log_anomaly_on_blockchain(timestamp, sensor_id, data_value, anomaly_type, explanation):
    print(f"\n--- Attempting to Log Anomaly on Blockchain ---")
    print(f"Logging: Timestamp={timestamp}, SensorID='{sensor_id}', Value={data_value}, Type='{anomaly_type}'")

    try:
        nonce = w3.eth.get_transaction_count(SENDER_ACCOUNT)
        gas_price = w3.eth.gas_price

        tx_hash = contract.functions.logAnomaly(
            timestamp,
            sensor_id,
            data_value,
            anomaly_type,
            explanation
        ).transact({
            'from': SENDER_ACCOUNT,
            'nonce': nonce,
            'gas': 3000000,
            'gasPrice': gas_price
        })

        print(f"Transaction sent. Tx Hash: {tx_hash.hex()}")
        print("Waiting for transaction receipt...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        print(f"Transaction mined. Status: {'SUCCESS' if receipt.status == 1 else 'FAILED'}")
        if receipt.status == 1:
            print("✅ Anomaly logged successfully on blockchain!")
        else:
            print("❌ Transaction failed to be mined successfully!")

    except Exception as e:
        print(f"❌ An error occurred during transaction: {e}")
        print("Common issues: Ganache not running, incorrect contract address, insufficient gas.")


def get_all_anomalies_from_blockchain():
    print("\n--- Fetching all anomalies from Blockchain ---")
    try:
        anomalies = contract.functions.getAllAnomalies().call()
        if anomalies:
            print(f"Found {len(anomalies)} anomalies:")
            for i, anomaly in enumerate(anomalies):
                print(f"Anomaly {i + 1}:")
                print(f"  Timestamp: {anomaly[0]} ({datetime.datetime.fromtimestamp(anomaly[0])})")
                print(f"  Sensor ID: {anomaly[1]}")
                print(f"  Value: {anomaly[2]}")
                print(f"  Type: {anomaly[3]}")
                print(f"  Explanation: {anomaly[4]}")
        else:
            print("No anomalies logged on the blockchain yet.")
    except Exception as e:
        print(f"❌ Error fetching anomalies: {e}")
        print("Ensure the contract is deployed and you have the correct ABI/Address.")


# --- FLASK APPLICATION ---
app = Flask(__name__)


@app.route('/sensor_data', methods=['POST'])
def receive_sensor_data():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    required_keys = ['sensor_id', 'temperature', 'humidity', 'pressure']
    if not all(key in data for key in required_keys):
        return jsonify({"error": f"Missing required data fields. Expected: {required_keys}"}), 400

    sensor_id = data.get('sensor_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    pressure = data.get('pressure')
    current_timestamp = int(time.time())

    # --- NEW: Update History and Prepare Lagged Features ---
    if sensor_id not in sensor_data_history:
        # Initialize deque if first time for this sensor
        sensor_data_history[sensor_id] = deque(maxlen=MAX_HISTORY_LENGTH)

    # Add current reading to history (as a tuple)
    current_reading = (temperature, humidity, pressure)
    sensor_data_history[sensor_id].append(current_reading)

    # We need at least LAG_FEATURES_COUNT readings to form the feature vector
    if len(sensor_data_history[sensor_id]) < LAG_FEATURES_COUNT:
        print(
            f"INFO: Not enough history for {sensor_id}. Current count: {len(sensor_data_history[sensor_id])}. Need {LAG_FEATURES_COUNT}.")
        return jsonify({
            "status": "Data received: Building history",
            "sensor_id": sensor_id,
            "data": data,
            "timestamp": current_timestamp
        }), 200

    # Create the lagged feature vector
    # recent_readings will contain the current reading and LAG_FEATURES_COUNT-1 previous readings
    # Example for LAG_FEATURES_COUNT = 3:
    # recent_readings = [(T_curr,H_curr,P_curr), (T_lag1,H_lag1,P_lag1), (T_lag2,H_lag2,P_lag2)]

    # Get the items directly from the deque, they are already in order of oldest to newest
    # We need them in order of newest to oldest for the feature vector
    ordered_readings = list(sensor_data_history[sensor_id])  # Convert deque to list

    # Flatten the list of tuples into a single numpy array
    # This loop ensures the order is [current_T, current_H, current_P, lag1_T, lag1_H, lag1_P, ...]
    # by iterating through the list in reverse order (to get newest first)
    flat_features = []
    for reading_tuple in reversed(ordered_readings):  # Iterate in reverse for (current, lag1, lag2...)
        flat_features.extend(reading_tuple)

    features = np.array([flat_features])  # Reshape to (1, num_features) for model.predict

    # Ensure the feature vector has the correct number of dimensions for the model
    if features.shape[1] != TOTAL_FEATURES_FOR_MODEL:
        print(f"ERROR: Feature vector dimension mismatch. Expected {TOTAL_FEATURES_FOR_MODEL}, got {features.shape[1]}")
        return jsonify({"error": "Internal feature processing error: Dimension mismatch"}), 500

    try:
        # Predict if it's an anomaly: -1 for anomaly, 1 for normal
        prediction = anomaly_model.predict(features)
        anomaly_score = anomaly_model.decision_function(features)[0]  # Get decision score for context

        print(
            f"DEBUG: Data Point (Current): {current_reading}, Lagged Features: {features[0]}, Anomaly Score: {anomaly_score:.4f}, Prediction: {prediction[0]}")

        if prediction == -1:
            # Anomaly detected! Log to blockchain
            anomaly_type = "Environmental Anomaly (Time Series)"
            explanation = (f"Detected via Isolation Forest (Score: {anomaly_score:.2f}). "
                           f"Current: Temp={temperature}, Humidity={humidity}, Pressure={pressure}. "
                           f"Contextual change based on recent readings.")
            print(f"❗ ANOMALY DETECTED for {sensor_id}!")
            temperature_for_blockchain = int(round(temperature))
            log_anomaly_on_blockchain(current_timestamp, sensor_id, temperature_for_blockchain, anomaly_type,
                                      explanation)

            return jsonify({
                "status": "Anomaly Detected and Logged",
                "sensor_id": sensor_id,
                "data": data,
                "timestamp": current_timestamp,
                "anomaly_score": anomaly_score
            }), 200
        else:
            print(f"✔️ Normal data received for {sensor_id}: Current: {current_reading}, Score: {anomaly_score:.4f}")
            return jsonify({
                "status": "Data Processed: No Anomaly",
                "sensor_id": sensor_id,
                "data": data,
                "timestamp": current_timestamp,
                "anomaly_score": anomaly_score
            }), 200

    except Exception as e:
        print(f"❌ Error during anomaly detection or logging: {e}")
        return jsonify({"error": f"Processing failed: {e}"}), 500


@app.route('/anomalies', methods=['GET'])
def get_anomalies():
    try:
        anomalies_list = contract.functions.getAllAnomalies().call()
        formatted_anomalies = []
        for anomaly in anomalies_list:
            formatted_anomalies.append({
                "timestamp": anomaly[0],
                "datetime": datetime.datetime.fromtimestamp(anomaly[0]).isoformat(),
                "sensor_id": anomaly[1],
                "data_value": anomaly[2],
                "anomaly_type": anomaly[3],
                "explanation": anomaly[4]
            })
        return jsonify(formatted_anomalies), 200
    except Exception as e:
        print(f"❌ Error fetching anomalies for API: {e}")
        return jsonify({"error": f"Could not fetch anomalies: {e}"}), 500


if __name__ == "__main__":
    print("\nStarting IoT Anomaly Detection Backend...")
    app.run(host='0.0.0.0', port=5000, debug=True)