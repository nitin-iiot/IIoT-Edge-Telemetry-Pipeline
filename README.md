# Industrial Edge Telemetry Pipeline

## Objective
An end-to-end edge computing architecture designed to extract, route, and visualize high-frequency machine telemetry. This serves as the foundational data infrastructure required for Digital Twin condition monitoring.

## System Architecture

```mermaid
graph LR
    A[Python CNC Simulation] -->|JSON Payload| B(Mosquitto MQTT Broker)
    B -->|Topic Routing| C{Node-RED Edge Processing}
    C -->|Data Structuring| D[(InfluxDB Time-Series Vault)]
    D -->|Flux Query Downsampling| E[Grafana Command Center]
