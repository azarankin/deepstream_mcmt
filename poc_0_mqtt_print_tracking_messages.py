
#!/usr/bin/env python3

from utils_brocker_mqtt import MqttSubscriber
from utils_deepstream import parse_ds_payload, fmt_num
from config import BrokerConfig as cfg


def on_message(client, userdata, msg):
    objs = parse_ds_payload(msg.payload)
    if objs:
        for o in objs:
            x1, y1, x2, y2 = o["bbox"]
            cls = o.get("cls")
            conf = o.get("conf")
            parts = [
                o["last_seen"],
                msg.topic,
                o.get("sensor", ""),
                f"id={o['track_id']}",
                f"bbox=[{fmt_num(x1)},{fmt_num(y1)},{fmt_num(x2)},{fmt_num(y2)}]",
            ]
            if cls:
                parts.append(f"cls={cls}")
            if conf is not None:
                parts.append(f"conf={fmt_num(conf)}")
            line = " | ".join(p for p in parts if p)
            print(line)
        return


if __name__ == "__main__":
    client = MqttSubscriber(cfg(), on_message=on_message).connect()
    try:
        client.start_forever()
    except KeyboardInterrupt:
        print("\n[MQTT] Stopped by user.")
    finally:
        client.stop()