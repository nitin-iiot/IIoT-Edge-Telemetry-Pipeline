# Industrial Edge Telemetry Pipeline

# Industrial Edge Telemetry Pipeline

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-660066?style=for-the-badge&logo=mqtt&logoColor=white)
![Node-RED](https://img.shields.io/badge/Node--RED-8F0000?style=for-the-badge&logo=node-red&logoColor=white)
![InfluxDB](https://img.shields.io/badge/InfluxDB-22ADF6?style=for-the-badge&logo=influxdb&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)

## Objective
An end-to-end, fully containerized edge computing architecture designed to extract, route, and visualize high-frequency machine telemetry. Built as a foundational data infrastructure for IIoT Digital Twin condition monitoring, supporting my M.Sc. Advanced Manufacturing research at TU Chemnitz.

## System Architecture

## System Architecture

```mermaid
graph TD
    A[Python CNC Edge Gateway] -->|JSON over MQTT| B[Mosquitto MQTT Broker]
    B -->|Topic Routing| C[Node-RED Stream Processing]
    C -->|Data Structuring| D[(InfluxDB Time-Series DB)]
    D -->|v.windowPeriod Flux Query| E[Grafana Dashboard]## System Architecture


## Future Work & Roadmap
* **Containerization:** Wrap the infrastructure layer (Broker, Node-RED, DB, Grafana) into a `docker-compose.yml` stack for single-command deployment.
* **Industrial Protocols:** Replace the Python simulation layer with a local OPC UA Server to mirror true factory-floor hardware integration.
