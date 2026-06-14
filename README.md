# Industrial Edge Telemetry & Semantic Digital Twin (AAS)

An end-to-end, fully containerized IIoT data infrastructure for condition monitoring — bridging the gap from raw OPC UA shop-floor data to a standardized Asset Administration Shell (AAS).

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-660066?logo=eclipsemosquitto&logoColor=white)](https://mosquitto.org/)
[![Node-RED](https://img.shields.io/badge/Node--RED-3.x-8F0000?logo=nodered&logoColor=white)](https://nodered.org/)
[![InfluxDB](https://img.shields.io/badge/InfluxDB-2.7-22ADF6?logo=influxdb&logoColor=white)](https://www.influxdata.com/)
[![Grafana](https://img.shields.io/badge/Grafana-10.x-F46800?logo=grafana&logoColor=white)](https://grafana.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)

---

## 📌 Objective

An end-to-end, fully containerized edge computing architecture designed to extract, route, and visualize high-frequency machine telemetry. Built as a foundational data infrastructure for IIoT Digital Twin condition monitoring, supporting my M.Sc. Advanced Manufacturing research at TU Chemnitz.

The project addresses a real manufacturing problem: industrial production lines generate continuous sensor data from PLCs, CNC machines, and discrete equipment. Without a reliable pipeline to capture, transform, and visualize this telemetry, predictive-maintenance analytics and digital-twin frameworks have no foundation. This repository demonstrates the IT–OT infrastructure layer that makes downstream semantic modelling and machine learning possible.

---

## 📊 Live Dashboard

![Grafana dashboard — CNC_1 live temperature monitoring with 100°C overheating threshold](dashboard.png)

The Grafana dashboard renders live `MACHINE_TEMP` telemetry, with a 100 °C operator-awareness threshold line, a real-time Stat panel for the current value, and adaptive historical trend retention via a custom downsampled Flux query.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    A[Python CNC Edge Gateway] -->|JSON over MQTT| B[Mosquitto MQTT Broker]
    B -->|Topic Routing| C[Node-RED Stream Processing]
    C -->|Data Structuring| D[(InfluxDB Time-Series DB)]
    D -->|v.windowPeriod Flux Query| E[Grafana Dashboard]
```

The architecture follows a classic IIoT pipeline pattern:

The architecture follows a modern IT/OT convergence pattern:

1. **OT Layer:** An asynchronous OPC UA server (`fake_plc.py`) simulates legacy CNC machine telemetry.
2. **Edge Gateway:** A Python bridge subscribes to the OPC UA nodes and translates payloads into lightweight JSON over MQTT, equipped with Last Will and Testament (LWT) for connection resilience.
3. **IT Infrastructure:** Eclipse Mosquitto routes topics, Node-RED parses streams into InfluxDB, and Grafana visualizes the time-series data using custom downsampled Flux queries.
4. **Semantic Layer (Industry 4.0):** The raw data points are structurally mapped into an official Asset Administration Shell (`CNC_1_Twin.aasx`) adhering to the IDTA V3 standard, making the data machine-readable for downstream predictive analytics.
---

## 🛠️ Tech Stack

| Layer | Technology | Role |
| :--- | :--- | :--- |
| Semantic Twin | AASX Package Explorer · IDTA V3 | Standardized machine shell and operational submodels |
| Machine Protocol | OPC UA (asyncio) | Deterministic industrial control simulation |
| Edge Gateway | Python 3.11 · `paho-mqtt` | Telemetry simulation, MQTT publishing with LWT |
| Messaging | Eclipse Mosquitto 2.0 | MQTT broker, topic-based routing |
| Stream Processing | Node-RED 3.x | Payload parsing, transformation, InfluxDB write |
| Storage | InfluxDB 2.7 | Time-series database with retention |
| Visualization | Grafana 10.x | Dashboards with custom Flux queries |
| Orchestration | Docker · Docker Compose | One-command reproducible deployment |

---

## 📁 Repository Structure

```
.
├── cnc_sensor.py                    # Python edge gateway (MQTT publisher with LWT)
├── Dockerfile                       # Builds the cnc-gateway container image
├── docker-compose.yml               # Orchestrates all 5 services
├── requirements.txt                 # Python dependencies for the edge gateway
├── NodeRED_Flow.json                # Importable Node-RED flow definition
├── Grafana_Dashboard.json           # Importable Grafana dashboard definition
├── machine_temp_downsample.flux     # Custom Flux query for adaptive downsampling
├── dashboard.png                    # Screenshot of the live dashboard
└── README.md
```

---

## 🚀 Quick Start

**Prerequisites:** Docker Desktop (or Docker Engine with Docker Compose v2) installed.

```bash
# Clone the repository
git clone https://github.com/IIoT-Edge-Telemetry-Pipeline
/industrial-edge-telemetry-pipeline.git
cd industrial-edge-telemetry-pipeline

# Start the full stack
docker compose up -d

# Verify all five services are running
docker compose ps
```

Then open in your browser:

| Service | URL | Default credentials |
|---------|-----|---------------------|
| Grafana | http://localhost:3000 | `admin` / `admin` (change on first login) |
| Node-RED | http://localhost:1880 | — |
| InfluxDB | http://localhost:8086 | configured on first run |

To stop the stack:

```bash
docker compose down
```

---

## ⚙️ Configuration

The Python edge gateway reads its MQTT broker target from environment variables. Defaults are set for the Docker Compose network and can be overridden via the `environment` block in `docker-compose.yml` or a `.env` file.

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_BROKER` | `mqtt-broker` | Hostname or IP of the MQTT broker |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_TOPIC` | `factory/chemnitz/cnc_1/sensors` | Telemetry publish topic |
| `MQTT_STATUS_TOPIC` | `factory/chemnitz/cnc_1/state` | Connection-state topic (LWT) |

---

## 🧰 Development Environment

This project was developed and tested using:

- **VS Code** with the Docker, Python, and Remote-Containers extensions for integrated container management
- **Docker Desktop** (Windows) for container orchestration and the embedded daemon
- **PowerShell** as the integrated terminal for `docker compose` commands
- **Python 3.11** runtime for the edge gateway implementation
- **Windows 10/11** as the development host (the stack is OS-agnostic and runs equally on Linux/macOS hosts)

To work on the codebase locally, install the Docker and Python extensions in VS Code, then open the repository folder. The integrated terminal makes it possible to run the entire `docker compose up -d` workflow without leaving the IDE.

---
---

## 🔁 Reproducing the Full Setup

For first-time setup after `docker compose up -d`, the Node-RED flow and Grafana dashboard need to be imported once. After this initial step, both configurations persist via Docker volumes across restarts.

### Step 1 · Import the Node-RED flow

1. Open Node-RED at <http://localhost:1880>
2. Menu (top right) → **Import**
3. Select **upload a file** and choose `NodeRED_Flow.json` from this repository
4. Click **Import**, then **Deploy** (red button, top right)

### Step 2 · Connect Grafana to InfluxDB

1. Open Grafana at <http://localhost:3000>
2. Sign in (default `admin` / `admin`) and change the password
3. **Connections → Data sources → Add data source → InfluxDB**
   - Query language: **Flux**
   - URL: `http://influxdb:8086`
   - Organization, token, and bucket: as configured during InfluxDB first-run setup at <http://localhost:8086>

### Step 3 · Import the Grafana dashboard

1. **Dashboards → New → Import**
2. Upload `Grafana_Dashboard.json`
3. Select the InfluxDB data source created in Step 2 and click **Import**

The custom downsampling query lives in `machine_temp_downsample.flux` — Grafana's panel references it via the `v.windowPeriod` variable for adaptive resolution at any time range, from the last minute to a full historical run.

### Verifying the data flow

After completing the steps above:

1. Grafana should display live `MACHINE_TEMP` values updating every few seconds
2. Node-RED's debug panel should show incoming JSON payloads under `factory/chemnitz/cnc_1/sensors`
3. The dashboard's threshold line at 100 °C should mark the overheating boundary, with the Stat panel reflecting the current value

---

## 🗺️ Project Roadmap

This repository represents **Phase 1** of a layered Industry 4.0 digital-twin architecture I am building incrementally. The phased structure reflects how production-grade digital twins are typically built: stable infrastructure first, then connectivity, semantics, and analytics.

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1** | Data infrastructure — Python edge, MQTT, Node-RED, InfluxDB, Grafana, Docker | ✅ **Complete** |
| **Phase 2** | OPC UA integration as the bridge from real PLCs to the existing pipeline |✅ **Complete**  |
| **Phase 3** | Semantic modelling via Asset Administration Shell (Eclipse BaSyx), aligned to BFO / IOF ontologies | ✅ **Complete** |


Phase 3 explicitly motivated by my interest in research on AAS-based digital twins and semantic-ML integration in industrial production environments.

---

## 👤 About

Built by **Nitin Senthilkumar**, M.Sc. Advanced Manufacturing student at **Technische Universität Chemnitz** (TU Chemnitz). Manufacturing-engineering background with focus on Industry 4.0, the IT–OT interface, and industrial data systems.

📧 [nitin.senthilkumar@s2025.tu-chemnitz.de](mailto:nitin.senthilkumar@s2025.tu-chemnitz.de)
🎓 M.Sc. Advanced Manufacturing · TU Chemnitz

---

## 📄 License

Released for academic and demonstration purposes. Free to reference for research and learning.
