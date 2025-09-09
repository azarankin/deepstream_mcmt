import json
import paho.mqtt.client as mqtt
from config import BrokerConfig
from typing import Iterable, Union, Iterable, Callable, Optional 
from datetime import datetime, timezone

class MqttSubscriber:
    """Managed MQTT Subscriber, built from BrokerConfig."""

    def __init__(self, cfg: BrokerConfig, on_message: Optional[Callable[["MqttSubscriber", mqtt.Client, object, mqtt.MQTTMessage], None]] = None) -> None:
        if not cfg.host:
            raise ValueError("host is required")
        if not cfg.port:
            raise ValueError("port is required")
        if not cfg.topics:
            raise ValueError("topics are required")
        if cfg.qos is None:
            raise ValueError("qos is required")

        self.cfg = cfg
        self.topics = list(self._ensure_iter(cfg.topics))

        # Create client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        if on_message:
            self.client.on_message = on_message
        else:
            self.client.on_message = self._on_message

        if cfg.username:
            self.client.username_pw_set(cfg.username, cfg.password)

        self._running = False

    # -------- public API --------
    def connect(self) -> "MqttSubscriber":
        self.client.connect(self.cfg.host, self.cfg.port, keepalive=self.cfg.keepalive)
        return self

    def start_forever(self) -> None:
        self._running = True
        print(f"[MQTT] Connecting to {self.cfg.host}:{self.cfg.port} … (topics={self.topics})")
        try:
            self.client.loop_forever(retry_first_connection=True)
        except KeyboardInterrupt:
            print("\n[MQTT] Interrupted by user.")
        except Exception as e:
            print(f"[MQTT] Error during loop_forever: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._running = False
            print("[MQTT] Client stopped.")

    def stop(self) -> None:
        try:
            self.client.disconnect()
        except Exception:
            pass

    def __del__(self) -> None:
        try:
            if self._running:
                self.stop()
        except Exception:
            pass

    # -------- callbacks --------
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        code = self._rc_value(rc)
        status_map = {
            0: "Connected",
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorised",
        }
        status = status_map.get(code, f"Unknown ({rc})")
        print(f"[MQTT] on_connect: {status}")

        if code == 0:
            for t in self.topics:
                client.subscribe(t, qos=self.cfg.qos)
                print(f"[MQTT] Subscribed to '{t}' (qos={self.cfg.qos})")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        code = self._rc_value(rc)
        if code != 0:
            print(f"[MQTT] Unexpected disconnect (rc={rc}). Reconnecting…")

    def _on_message(self, client, userdata, msg):
        # not DeepStream – print raw/prettified
        text = self._pretty_or_raw(msg.payload)
        print(f"\n{msg.topic}:\n{text}")
        if self.cfg.save_path:
            self._append_to_file(self.cfg.save_path, msg.topic, text)

    # -------- helpers --------
    def _pretty_or_raw(self, payload: bytes) -> str:
        try:
            obj = json.loads(payload.decode("utf-8"))
            return (
                json.dumps(obj, ensure_ascii=False, indent=2)
                if self.cfg.pretty
                else json.dumps(obj, ensure_ascii=False)
            )
        except Exception:
            try:
                return payload.decode("utf-8", errors="replace")
            except Exception:
                return repr(payload)
        

    def _append_to_file(self, path: str, topic: str, text: str):
        ts = self.utc_iso()
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {topic} {text}\n")

    def _ensure_iter(self, x: Union[str, Iterable[str]]) -> Iterable[str]:
        if isinstance(x, str):
            return [x]
        return list(x)


    def _rc_value(self, rc):
        """Return numeric reason code if possible, else string."""
        if hasattr(rc, "value"):   # paho v5 ReasonCode
            return rc.value
        try:
            return int(rc)
        except Exception:
            return rc
        
    def utc_iso(self):
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")