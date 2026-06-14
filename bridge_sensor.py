import asyncio
import json
import os
import paho.mqtt.client as mqtt
from asyncua import Client

# --- IT SIDE: MQTT (The Walkie-Talkie) ---
BROKER = os.getenv('MQTT_BROKER', '127.0.0.1')
PORT = 1883
TOPIC = 'factory/chemnitz/cnc_1/sensors'
STATUS_TOPIC = 'factory/chemnitz/cnc_1/state'

# --- OT SIDE: OPC UA (The Machine Brain) ---
OPC_URL = "opc.tcp://127.0.0.1:4840/freeopcua/server/"
OPC_NAMESPACE = "http://fraunhofer.iwu.cnc"

async def main():
    print(f"1. Turning on Walkie-Talkie (Connecting to MQTT at {BROKER})...")
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="CNC_1_BRIDGE")
    
    # The Dead Man's Switch
    lwt_payload = json.dumps({'MACHINE':'CNC_1', 'STATUS':'FATAL ERROR'})
    mqtt_client.will_set(STATUS_TOPIC, payload=lwt_payload, qos=1, retain=True)
    
    mqtt_client.connect(BROKER, PORT)
    mqtt_client.loop_start() # Start breathing
    
    mqtt_client.publish(STATUS_TOPIC, json.dumps({'MACHINE':'CNC_1', 'STATUS':'ONLINE'}), qos=1, retain=True)

    print(f"2. Walking up to the PLC at {OPC_URL}...")
    # Clock into the PLC
    async with Client(url=OPC_URL) as opc_client:
        print("3. Connected! Locating the Spindle Temperature tag...")
        
        # Navigate the OPC UA folder structure
        idx = await opc_client.get_namespace_index(OPC_NAMESPACE)
        temp_node = await opc_client.nodes.objects.get_child([f"{idx}:CNC_1", f"{idx}:SpindleTemperature"])
        
        print("\n--- IT/OT BRIDGE ACTIVE ---")
        try:
            while True:
                # STEP A: Read real data from the PLC (OT)
                current_temp = await temp_node.read_value()
                
                # STEP B: Process and format the data
                machine_status = "OVERHEATING" if current_temp > 100 else "OK"
                payload = {
                    "MACHINE": "CNC_1",
                    "MACHINE_TEMP": current_temp,
                    "MACHINE_STATUS": machine_status
                }
                json_envelope = json.dumps(payload)
                
                # STEP C: Publish data to the Broker (IT)
                mqtt_client.publish(TOPIC, json_envelope, qos=1)
                print(f"Bridged: {current_temp} °C -> MQTT Broker")
                
                await asyncio.sleep(2)
                
        except KeyboardInterrupt:
            print("\nShutting down bridge gracefully...")
        finally:
            # Graceful shutdown sequence
            mqtt_client.publish(STATUS_TOPIC, json.dumps({'MACHINE':'CNC_1', 'STATUS':'GRACEFUL_SHUTDOWN'}), qos=1, retain=True)
            mqtt_client.disconnect()
            mqtt_client.loop_stop()

if __name__ == "__main__":
    asyncio.run(main())