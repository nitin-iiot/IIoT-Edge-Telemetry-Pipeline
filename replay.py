"""Play a NASA milling tool's life back over MQTT as if it were live.

    <prefix>/telemetry     ac_rms + run number, one message per cut
    <prefix>/groundtruth   measured VB, for the dashboard only

The estimator must never subscribe to groundtruth; it can only see what a
gateway would see. Start estimator.py first - it takes its fresh-tool
baseline from the first telemetry message, so subscribing late baselines it
against an already-worn tool.

    python replay.py [--runs runs.csv] [--case 11] [--speed 3.0]
"""

import argparse
import json
import time

import pandas as pd
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC_TELEMETRY = "nitin7f3a/cnc01/telemetry"
TOPIC_GROUNDTRUTH = "nitin7f3a/cnc01/groundtruth"
TOPIC_STATUS = "nitin7f3a/cnc01/status"

CASE = 11                 # the held-out tool
SECONDS_PER_RUN = 3.0
STARTUP_DELAY = 2.0       # let a subscriber attach before run 1 goes out


def make_client(client_id):
    try:
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except AttributeError:
        c = mqtt.Client(client_id=client_id)

    c.will_set(TOPIC_STATUS, json.dumps({"node": "replay", "online": False}),
               qos=1, retain=True)
    c.connect(BROKER, PORT, keepalive=60)
    c.loop_start()
    c.publish(TOPIC_STATUS, json.dumps({"node": "replay", "online": True}),
              qos=1, retain=True)
    return c


def go_offline(client):
    client.publish(TOPIC_STATUS, json.dumps({"node": "replay", "online": False}),
                   qos=1, retain=True).wait_for_publish(timeout=2)
    client.loop_stop()
    client.disconnect()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", default="runs.csv")
    p.add_argument("--case", type=int, default=CASE)
    p.add_argument("--speed", type=float, default=SECONDS_PER_RUN)
    args = p.parse_args()

    df = pd.read_csv(args.runs)
    tool = df[df.case == args.case].sort_values("run").reset_index(drop=True)
    if tool.empty:
        raise SystemExit(f"case {args.case} not found in {args.runs}")

    first, last = int(tool["run"].iloc[0]), int(tool["run"].iloc[-1])
    if first != 1:
        print(f"WARNING: case {args.case} starts at run {first} - the estimator's "
              f"baseline will not be a fresh tool")

    client = make_client("replay")
    print(f"replaying case {args.case}: {len(tool)} runs (start estimator.py first)")
    time.sleep(STARTUP_DELAY)
    print()

    try:
        for _, r in tool.iterrows():
            ts = time.time()          # one timestamp per cut, both topics
            run = int(r["run"])

            info = client.publish(TOPIC_TELEMETRY, json.dumps({
                "ts": ts,
                "run": run,
                "ac_rms": round(float(r["smcAC_rms"]), 6),
            }), qos=1)

            if pd.notna(r["VB_mm"]):
                info = client.publish(TOPIC_GROUNDTRUTH, json.dumps({
                    "ts": ts,
                    "run": run,
                    "vb_true_mm": float(r["VB_mm"]),
                }), qos=1)

            vb = float(r["VB_mm"]) if pd.notna(r["VB_mm"]) else float("nan")
            print(f"run {run:3d}   ac_rms {r['smcAC_rms']:.4f}   vb_true {vb:.3f}")

            if run != last:
                time.sleep(args.speed)
    except KeyboardInterrupt:
        print("\nreplay interrupted")
    else:
        info.wait_for_publish(timeout=5)   # QoS 1 is not on the wire yet
        print("\ntool life finished")

    go_offline(client)


if __name__ == "__main__":
    main()