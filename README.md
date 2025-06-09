# 📊 IoT Anomaly Detection with AI & Blockchain

An end-to-end project demonstrating real-time IoT sensor data simulation, AI-driven anomaly detection (using Isolation Forest), and immutable logging of detected anomalies on an Ethereum blockchain (Ganache), all visualized through a live Streamlit dashboard.

This project showcases how machine learning can be used to monitor sensor data for unusual patterns, and how blockchain can provide a transparent and tamper-proof audit trail for critical events like anomalies, enhancing trust and accountability in IoT systems.

## ✨ Features

* **Realistic Time-Series Data Simulation:** Generates synthetic temperature, humidity, and pressure data with realistic daily cycles, noise, and configurable "sensor profiles."
* **Controlled Anomaly Injection:** Deliberately injects various types of anomalies:
    * **Point Anomalies:** Sudden, isolated spikes/drops (e.g., a temperature reading of 1000°C).
    * **Contextual Anomalies:** Values normal on their own but abnormal in context (e.g., 30°C in winter).
    * **Change Points:** Sudden shifts in underlying data distribution (e.g., a sensor consistently reporting higher values).
* **AI-Powered Anomaly Detection:** Utilizes the `IsolationForest` machine learning algorithm to learn "normal" patterns from historical data and flag deviations.
    * Incorporates **lagged features** (previous readings) to provide time-series context to the ML model, improving detection of contextual and change-point anomalies.
* **Blockchain Integration:**
    * Deploys a Solidity Smart Contract (`AnomalyLogger.sol`) on an Ethereum testnet (Ganache) to immutably log detected anomalies.
    * Each anomaly is recorded with a timestamp, sensor ID, data value, anomaly type, and an AI-generated explanation.
    * Leverages `web3.py` for seamless interaction between the Python backend and the blockchain.
* **Real-time Dashboard:** A dynamic Streamlit frontend for:
    * Displaying a live feed of detected anomalies fetched directly from the blockchain.
    * Allowing manual simulation of sensor data for immediate testing.
    * (Planned) Real-time push updates via WebSockets for instant anomaly alerts.

## 🚀 Architecture Overview

The project is structured into four main components that communicate with each other:

1.  **`smart_contracts/` (Solidity/Hardhat):** Contains the `AnomalyLogger.sol` smart contract. This is compiled and deployed to the Ganache blockchain.
2.  **`backend/` (Python/Flask):**
    * Acts as the central hub.
    * Receives simulated sensor data via an HTTP POST endpoint.
    * Hosts the trained `IsolationForest` model.
    * Performs anomaly detection on incoming data using lagged features.
    * If an anomaly is detected, it interacts with the deployed `AnomalyLogger` smart contract via `web3.py` to log the anomaly on the blockchain.
    * Provides an HTTP GET endpoint to retrieve all logged anomalies from the blockchain.
    * (Future) Will integrate `Flask-SocketIO` for real-time push notifications to the frontend.
3.  **`backend/data_simulator.py` (Python):**
    * A separate script that simulates sensor readings with realistic patterns and injects anomalies.
    * Sends these simulated readings as HTTP POST requests to the Flask backend's `/sensor_data` endpoint.
4.  **`frontend/streamlit_app.py` (Python/Streamlit):**
    * The user interface dashboard.
    * Fetches and displays logged anomalies from the Flask backend's `/anomalies` endpoint.
    * Allows manual input of sensor data to the backend.
    * (Future) Will receive real-time anomaly alerts via WebSockets.
