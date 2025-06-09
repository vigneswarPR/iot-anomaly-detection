// smart_contract/contracts/AnomalyLogger.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0; // Use your chosen Solidity version

contract AnomalyLogger {
    struct Anomaly {
        uint256 timestamp;
        string sensorId;
        int256 dataValue;
        string anomalyType;
        string explanation;
    }

    Anomaly[] public anomalies;

    event AnomalyDetected(
        uint256 indexed timestamp,
        string indexed sensorId,
        int256 dataValue,
        string anomalyType,
        string explanation
    );

    function logAnomaly(
        uint256 _timestamp,
        string memory _sensorId,
        int256 _dataValue,
        string memory _anomalyType,
        string memory _explanation
    ) public {
        anomalies.push(Anomaly({
            timestamp: _timestamp,
            sensorId: _sensorId,
            dataValue: _dataValue,
            anomalyType: _anomalyType,
            explanation: _explanation
        }));
        emit AnomalyDetected(_timestamp, _sensorId, _dataValue, _anomalyType, _explanation);
    }

    function getAllAnomalies() public view returns (Anomaly[] memory) {
        return anomalies;
    }
}