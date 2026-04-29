# Industrial Edge Telemetry Pipeline

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-660066?style=for-the-badge&logo=mqtt&logoColor=white)
![Node-RED](https://img.shields.io/badge/Node--RED-8F0000?style=for-the-badge&logo=node-red&logoColor=white)
![InfluxDB](https://img.shields.io/badge/InfluxDB-22ADF6?style=for-the-badge&logo=influxdb&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)

## Objective
An end-to-end edge computing architecture designed to extract, route, and visualize high-frequency machine telemetry. This serves as the foundational data infrastructure required for IIoT Digital Twin condition monitoring, built in preparation for the CREDIT project at TU Chemnitz.

## System Architecture

```mermaid
graph LR
    A[Python CNC Simulation] -->|JSON Payload| B[Mosquitto MQTT Broker]
    B -->|Topic Routing| C[Node-RED Edge Processing]
    C -->|Data Structuring| D[(InfluxDB Time-Series Database)]
    D -->|Flux Query Downsampling| E[Grafana Dashboard]
```
## Live Dashboard Output
![Grafana Dashboard](dashboard.png)
## Data Flow & Module Breakdown

1. **Edge Simulation (`iot_gateway.py`):** A Python routine utilizing `paho-mqtt` to simulate thermal and mechanical physics of a CNC machine. Structures telemetry into JSON envelopes.
2. **Message Broker (Eclipse Mosquitto):** The lightweight publish/subscribe nervous system running on `localhost:1883`, decoupling data generation from database ingestion.
3. **Stream Processing (Node-RED):** Subscribes to the MQTT topic, parses the JSON payload, and formats the time-series data for secure database insertion.
4. **Time-Series Database (InfluxDB):** High-write-performance data store operating on port `8086`. Archives the real-time stream into designated buckets.
5. **Visualization Layer (Grafana):** Connects to InfluxDB via Flux queries. Utilizes `aggregateWindow` functions mapped to `$__interval` for dynamic, pixel-perfect data downsampling on the UI.

## Prerequisites & Local Setup

To reproduce this pipeline locally:
1. Install **Python 3.x** and run `pip install -r requirements.txt`.
2. Ensure **Mosquitto**, **Node-RED**, **InfluxDB**, and **Grafana** are installed and running locally.
3. Import `NodeRED_Flow.json` into your local Node-RED instance.
4. Import `Grafana_Dashboard.json` into Grafana and configure the InfluxDB data source.
5. Execute the Python script to begin publishing telemetry to `factory/chemnitz/cnc_1/sensors`.

## Future Work & Roadmap
* **Containerization:** Wrap the infrastructure layer (Broker, Node-RED, DB, Grafana) into a `docker-compose.yml` stack for single-command deployment.
* **Industrial Protocols:** Replace the Python simulation layer with a local OPC UA Server to mirror true factory-floor hardware integration.
