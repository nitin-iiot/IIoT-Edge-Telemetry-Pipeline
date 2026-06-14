import asyncio
import json
import os

import paho.mqtt.client as mqtt
from asyncua import Client

# --- IT side: MQTT ---
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt-broker")   # use 127.0.0.1 when running outside Docker
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "factory/chemnitz/cnc_1/sensors")
MQTT_STATUS_TOPIC = os.getenv("MQTT_STATUS_TOPIC", "factory/chemnitz/cnc_1/state")

# --- OT side: OPC UA ---
OPC_URL = os.getenv("OPC_URL", "opc.tcp://127.0.0.1:4840/freeopcua/server/")
OPC_NAMESPACE = os.getenv("OPC_NAMESPACE", "https://github.com/nitin-iiot/IIoT-Edge-Telemetry-Pipeline")

OVERHEAT_THRESHOLD_C = 100.0
READ_INTERVAL_S = 2


async def main():
    print(f"1. Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT} ...")
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="CNC_1_BRIDGE")

    # Last Will and Testament: the broker announces this if the bridge dies unexpectedly
    lwt = json.dumps({"MACHINE": "CNC_1", "STATUS": "FATAL_ERROR"})
    mqtt_client.will_set(MQTT_STATUS_TOPIC, payload=lwt, qos=1, retain=True)

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()
    mqtt_client.publish(MQTT_STATUS_TOPIC, json.dumps({"MACHINE": "CNC_1", "STATUS": "ONLINE"}), qos=1, retain=True)

    print(f"2. Connecting to the PLC over OPC UA at {OPC_URL} ...")
    async with Client(url=OPC_URL) as opc_client:
        print("3. Connected. Locating the spindle-temperature node ...")
        idx = await opc_client.get_namespace_index(OPC_NAMESPACE)
        # NOTE: this path must match the OPC UA server: Objects -> CNC_1 -> SpindleTemperature
        temp_node = await opc_client.nodes.objects.get_child(
            [f"{idx}:CNC_1", f"{idx}:SpindleTemperature"]
        )

        print("\n--- IT/OT BRIDGE ACTIVE ---")
        try:
            while True:
                current_temp = await temp_node.read_value()
                status = "OVERHEATING" if current_temp > OVERHEAT_THRESHOLD_C else "OK"
                payload = {
                    "MACHINE": "CNC_1",
                    "MACHINE_TEMP": current_temp,
                    "MACHINE_STATUS": status,
                }
                mqtt_client.publish(MQTT_TOPIC, json.dumps(payload), qos=1)
                print(f"Bridged: {current_temp:.2f} °C -> MQTT")
                await asyncio.sleep(READ_INTERVAL_S)
        except KeyboardInterrupt:
            print("\nShutting down bridge gracefully ...")
        finally:
            mqtt_client.publish(
                MQTT_STATUS_TOPIC,
                json.dumps({"MACHINE": "CNC_1", "STATUS": "GRACEFUL_SHUTDOWN"}),
                qos=1, retain=True,
            )
            mqtt_client.disconnect()
            mqtt_client.loop_stop()


if __name__ == "__main__":
    asyncio.run(main())
