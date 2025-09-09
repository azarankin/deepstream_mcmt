import cv2
import numpy as np
import random
import time

WIDTH, HEIGHT = 1280, 720
FONT = cv2.FONT_HERSHEY_SIMPLEX
TTL_SEC = 1.0  # משך חיים של כל bbox

def id_to_color(seed_str: str):
    """ממיר מחרוזת לצבע קבוע"""
    random.seed(hash(seed_str) % 2**32)
    return tuple(random.randint(50, 255) for _ in range(3))

class TrackInstance:
    """הופעה בודדת של אובייקט"""
    def __init__(self, bbox, sensor, conf):
        self.bbox = bbox
        self.sensor = sensor
        self.conf = conf
        self.timestamp = time.time()

    def is_alive(self, now_ts: float) -> bool:
        return (now_ts - self.timestamp) <= TTL_SEC

class TrackerScene:
    def __init__(self):
        self.instances = []  # רשימת הופעות פעילות

    def update_from_objs(self, obj_list, now_ts=None):
        now = now_ts if now_ts is not None else time.time()
        print(f"[DEBUG] Received {len(obj_list)} object(s) at {now:.2f}")
        for o in obj_list:
            bbox = o.get("bbox")
            if not bbox or len(bbox) != 4:
                print(f"[SKIP] Invalid bbox: {bbox}")
                continue
            sensor = o.get("sensor", "?")
            conf = o.get("conf", 0.0)
            inst = TrackInstance(bbox, sensor, conf)
            self.instances.append(inst)

        # ניקוי אובייקטים ישנים
        before = len(self.instances)
        self.instances = [i for i in self.instances if i.is_alive(now)]
        after = len(self.instances)
        if after < before:
            print(f"[GC] Removed {before - after} expired instances")

    def draw_scene(self):
        """מצייר את כל bbox הפעילים למסך לבן"""
        img = np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8) * 255
        now = time.time()
        drawn = 0
        for inst in self.instances:
            if not inst.is_alive(now):
                continue
            try:
                x1, y1, x2, y2 = map(int, inst.bbox)
                if x2 <= x1 or y2 <= y1:
                    print(f"[SKIP DRAW] Invalid bbox dims: {inst.bbox}")
                    continue
                color = id_to_color(inst.sensor or "default")
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                label = str(inst.sensor)
                text_size = cv2.getTextSize(label, FONT, 0.6, 2)[0]
                text_x = int((x1 + x2 - text_size[0]) / 2)
                text_y = int((y1 + y2 + text_size[1]) / 2)
                cv2.putText(img, label, (text_x, text_y), FONT, 0.6, color, 2)
                drawn += 1
            except Exception as e:
                print(f"[DRAW ERROR] {e}")
        print(f"[DRAW] Frame with {drawn} object(s) at {now:.2f}")
        return img
