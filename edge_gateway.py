"""
edge_gateway.py - publish machine telemetry to the pipeline over MQTT.

The temperature is simulated here, so the rest of the pipeline (broker,
Node-RED, InfluxDB, Grafana) can be run and tested without a machine. In a
real deployment this value would come off the controller (OPC UA, Modbus, an
analog input); everything downstream of this file is identical either way.

Topics and payload fields match the Node-RED flow and Grafana dashboard in
this repo, so it is a drop-in source.
"""

import json
import math
import os
import random
import time

import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "factory/chemnitz/cnc_1/sensors")
TOPIC_STATUS = os.getenv("MQTT_STATUS_TOPIC", "factory/chemnitz/cnc_1/state")

PUBLISH_INTERVAL = 2.0        # seconds between readings
OVERHEAT_LIMIT = 100.0        # deg C; matches the dashboard threshold


def simulated_spindle_temp(t):
    """Warms from ambient and drifts up, so the demo also shows the overheating path."""
    ramp = 30 + 80 * (1 - math.exp(-t / 180))   # deg C, approaches ~110
    return round(ramp + random.uniform(-0.5, 0.5), 2)


def make_client():
    try:
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edge-gateway")
    except AttributeError:
        c = mqtt.Client(client_id="edge-gateway")

    # Last Will: if this gateway drops, the broker publishes "FATAL ERROR" for us.
    c.will_set(TOPIC_STATUS, json.dumps({"STATUS": "FATAL ERROR"}),
               qos=1, retain=True)

    c.connect(BROKER, PORT, keepalive=60)
    c.loop_start()
    c.publish(TOPIC_STATUS, json.dumps({"STATUS": "ONLINE"}), qos=1, retain=True)
    return c


def main():
    client = make_client()
    print(f"publishing to {TOPIC} on {BROKER}:{PORT} every {PUBLISH_INTERVAL:g}s "
          f"(Ctrl-C to stop)")
    t0 = time.time()
    try:
        while True:
            temp = simulated_spindle_temp(time.time() - t0)
            status = "OVERHEATING" if temp >= OVERHEAT_LIMIT else "NORMAL"
            client.publish(TOPIC, json.dumps({
                "MACHINE_TEMP": temp,
                "MACHINE_STATUS": status,
            }), qos=1)
            print(f"MACHINE_TEMP {temp:6.2f} C   {status}")
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        client.publish(TOPIC_STATUS, json.dumps({"STATUS": "GRACEFUL_SHUTDOWN"}),
                       qos=1, retain=True)
        client.loop_stop()
        client.disconnect()
        print("\nstopped")


if __name__ == "__main__":
    main()
