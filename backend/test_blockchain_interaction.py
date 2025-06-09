# backend/test_blockchain_interaction.py

import json
import os
import time
import datetime
from web3 import Web3
# FIXED: Updated import for newer Web3.py versions
from web3.middleware import ExtraDataToPOAMiddleware

# --- CONFIGURATION ---
# UPDATED: Use the contract address from your deployment
CONTRACT_ADDRESS = '0x7CdD0D08223D39840c8EB9A22077c64688f8ce09'  # Your deployed contract address

# Path to your AnomalyLogger.json (ABI file)
# This path assumes test_blockchain_interaction.py is in 'backend/'
# and AnomalyLogger.json is in 'smart_contract/artifacts/...'
# Path to your AnomalyLogger.json (ABI file)
# This path assumes test_blockchain_interaction.py is in 'backend/'
# and AnomalyLogger.json is in 'smart_contracts/artifacts/...'
ABI_FILE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), # Current directory (backend/)
        '..',                      # Go up to iot-anomaly-detection/
        'smart_contracts',         # <--- **MAKE SURE THIS IS 'smart_contracts' (plural)**
        'artifacts',
        'contracts',
        'anomaly_logger.sol',      # <--- **MAKE SURE THIS IS 'anomaly_logger.sol' (lowercase 'a')**
        'AnomalyLogger.json'       # <--- **MAKE SURE THIS IS 'AnomalyLogger.json' (capital 'A')**
    )
)

# UPDATED: Use port 7545 for Ganache GUI (port 8545 is for ganache-cli)
GANACHE_URL = 'http://127.0.0.1:8545'

# --- WEB3 SETUP ---
try:
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

    # FIXED: Add ExtraDataToPOAMiddleware for Ganache compatibility
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    # Check connection
    if w3.is_connected():
        print(f"✅ Successfully connected to Ganache at {GANACHE_URL}")
    else:
        print("❌ Failed to connect to Ganache. Please ensure Ganache is running.")
        exit()
except Exception as e:
    print(f"❌ Error during Web3 setup: {e}")
    exit()

# Get the ABI from the JSON file
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

# Get the contract instance
try:
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
    print(f"✅ Contract instance created for address: {CONTRACT_ADDRESS}")
except Exception as e:
    print(f"❌ Error creating contract instance: {e}")
    print("Please check CONTRACT_ADDRESS and CONTRACT_ABI.")
    exit()


# --- INTERACTION FUNCTIONS ---

def log_test_anomaly():
    # Get one of the accounts from Ganache
    # For a hackathon, using the first account is fine.
    # In a real app, you'd manage sender accounts/private keys securely.
    my_account = w3.eth.accounts[0] # Ganache typically provides 10 accounts

    print(f"\n--- Attempting to Log Test Anomaly ---")
    print(f"Using account: {my_account}")
    print(f"Account balance before: {w3.from_wei(w3.eth.get_balance(my_account), 'ether'):.4f} ETH")

    try:
        # Prepare transaction details
        timestamp = int(time.time()) # Current Unix timestamp
        sensor_id = f"test_sensor_{int(time.time()) % 100}" # Unique ID for each test
        data_value = 999
        anomaly_type = "Python Test Anomaly (Point)"
        explanation = "Automated test log via web3.py for hackathon demo."

        print(f"Logging: Timestamp={timestamp}, SensorID='{sensor_id}', Value={data_value}, Type='{anomaly_type}'")

        # Build the transaction
        # Using current nonce for the account to ensure transaction ordering
        nonce = w3.eth.get_transaction_count(my_account)
        gas_price = w3.eth.gas_price # Get current average gas price

        tx_hash = contract.functions.logAnomaly(
            timestamp,
            sensor_id,
            data_value,
            anomaly_type,
            explanation
        ).transact({
            'from': my_account,
            'nonce': nonce,
            'gas': 3000000, # A generous gas limit for Ganache, adjust if needed
            'gasPrice': gas_price
        })

        print(f"Transaction sent. Tx Hash: {tx_hash.hex()}")
        print("Waiting for transaction receipt...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120) # Wait up to 120 seconds

        print(f"Transaction mined. Status: {'SUCCESS' if receipt.status == 1 else 'FAILED'}")
        if receipt.status == 1:
            print("✅ Anomaly logged successfully on blockchain!")
        else:
            print("❌ Transaction failed to be mined successfully!")

        print(f"Account balance after: {w3.from_wei(w3.eth.get_balance(my_account), 'ether'):.4f} ETH")

    except Exception as e:
        print(f"❌ An error occurred during transaction: {e}")
        print("Common issues: Ganache not running, incorrect contract address, insufficient gas.")

def get_all_anomalies():
    print("\n--- Fetching all anomalies from Blockchain ---")
    try:
        anomalies = contract.functions.getAllAnomalies().call()
        if anomalies:
            print(f"Found {len(anomalies)} anomalies:")
            for i, anomaly in enumerate(anomalies):
                # Access struct members by index (0, 1, 2, 3, 4) as returned by web3.py for structs
                print(f"Anomaly {i+1}:")
                # FIXED: Use datetime.datetime.fromtimestamp for conversion
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

if __name__ == "__main__":
    log_test_anomaly()
    get_all_anomalies()