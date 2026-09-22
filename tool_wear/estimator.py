"""
estimator.py - estimate flank wear and remaining tool life from spindle current.

Subscribes ONLY to the telemetry topic. The microscope reference is published
by replay.py on a separate topic that this script never subscribes to, so the
error it produces is a genuine out-of-sample error.

    ac_rms  ->  rise vs the first run of the same tool
            ->  VB estimate, via the calibration fitted on case 3
            ->  line through recent estimates, extended to VB_CRIT
            ->  runs remaining

    python estimator.py
"""

import json

import numpy as np
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC_IN = "nitin7f3a/cnc01/telemetry"
TOPIC_OUT = "nitin7f3a/cnc01/estimate"
TOPIC_STATUS = "nitin7f3a/cnc01/status"

# --- calibration -----------------------------------------------------------
# VB = SLOPE * rise + INTERCEPT, least-squares fit on case 3
# (14 reference points, R^2 = 0.91).
# Case 3 and case 11 share cutting conditions - feed 0.25 mm, depth of cut
# 0.75 mm, material 1 - so replaying case 11 tests the calibration across a
# tool change, not across a change of process parameters.
SLOPE = 0.3348
INTERCEPT = 0.0845

VB_CRIT = 0.30         # mm, flank wear limit per ISO 3685
FIT_WINDOW = 10        # how many recent estimates the RUL line is fitted through
MIN_POINTS = 3         # fewer than this and there is no trend to extrapolate
MIN_SLOPE = 0.004      # mm per run; below this the trend is noise, not wear
# ---------------------------------------------------------------------------

baseline = None
history = []          # list of (run, vb_est)


def estimate_rul(hist):
    """Fit a line through recent VB estimates and extend it to VB_CRIT.

    Returns runs remaining, or None if there is not enough of a trend to
    extrapolate. Dividing by a near-zero slope is what produces those
    negative-then-infinite RUL numbers, so it is guarded.
    """
    if len(hist) < MIN_POINTS:
        return None

    recent = hist[-FIT_WINDOW:]
    runs = np.array([h[0] for h in recent], dtype=float)
    vbs = np.array([h[1] for h in recent], dtype=float)

    slope, intercept = np.polyfit(runs, vbs, 1)
    if slope < MIN_SLOPE:
        return None

    vb_now = slope * runs[-1] + intercept      # the FITTED value, not the raw one
    # int() truncates, which under-reports runs remaining - the safe direction.
    return max(0, int((VB_CRIT - vb_now) / slope))


def on_message(client, userdata, msg):
    try:
        _handle(client, msg)
    except Exception as e:
        print("ERROR in on_message:", repr(e))


def _handle(client, msg):
    global baseline

    d = json.loads(msg.payload)
    run, ac = d["run"], d["ac_rms"]

    if baseline is None:
        baseline = ac
        print(f"run {run:3d}   baseline set, no estimate yet")
        return

    rise = (ac - baseline) / baseline
    vb_est = SLOPE * rise + INTERCEPT
    history.append((run, vb_est))
    rul = estimate_rul(history)

    client.publish(TOPIC_OUT, json.dumps({
        "ts": d["ts"],
        "run": run,
        "rise": round(rise, 6),
        "vb_est_mm": round(vb_est, 4),
        "rul_runs": rul,
    }), qos=1)

    rul_txt = f"{rul:3d} runs" if rul is not None else "  unknown"
    print(f"run {run:3d}   rise {rise:6.3f}   vb_est {vb_est:.3f} mm   RUL {rul_txt}")


def main():
    try:
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="estimator")
    except AttributeError:
        c = mqtt.Client(client_id="estimator")

    c.on_message = on_message

    c.will_set(TOPIC_STATUS,
               json.dumps({"node": "estimator", "online": False}),
               qos=1, retain=True)

    c.connect(BROKER, PORT, keepalive=60)

    c.publish(TOPIC_STATUS,
              json.dumps({"node": "estimator", "online": True}),
              qos=1, retain=True)

    c.subscribe(TOPIC_IN, qos=1)
    print(f"listening on {TOPIC_IN}\n")

    try:
        c.loop_forever()
    except KeyboardInterrupt:
        c.publish(TOPIC_STATUS,
                  json.dumps({"node": "estimator", "online": False}),
                  qos=1, retain=True)
        c.disconnect()
        print("\nestimator stopped")


if __name__ == "__main__":
    main()