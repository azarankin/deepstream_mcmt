import json
from typing import Iterable, Union, List, Dict, Any
from datetime import datetime, timezone

# ---------- utils ----------



def utc_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")



# ---------- DeepStream parsing ----------


def parse_ds_payload(payload: bytes) -> List[Dict[str, Any]]:
    """
    מנסה לפרש DeepStream JSON ולהחזיר רשימת אובייקטים סטנדרטיים:
    { sensor, track_id, bbox[x1,y1,x2,y2], last_seen, cls, conf }
    מחזיר [] אם לא פורמט DS שמוכר.
    """
    try:
        d = json.loads(payload.decode("utf-8"))
    except Exception:
        return []

    ts = d.get("@timestamp") or utc_iso()
    sensor = d.get("sensorId") or (d.get("sensor") or {}).get("id") or "unknown"

    # payload-type = 1: d["objects"] = ["id|x1|y1|x2|y2|class|#|gender|age|hair|cap|apparel|conf", ...]
    if isinstance(d.get("objects"), list):
        out = []
        for s in d["objects"]:
            if not isinstance(s, str):
                continue
            parts = s.split("|")
            if len(parts) >= 5:
                tid = parts[0]
                try:
                    x1, y1, x2, y2 = map(float, parts[1:5])
                except Exception:
                    continue
                cls = parts[5] if len(parts) > 5 else None
                conf = None
                if len(parts) >= 13:
                    # בקצה המחרוזת בד"כ confidence
                    try:
                        conf = float(parts[-1])
                    except Exception:
                        conf = None
                out.append({
                    "sensor": sensor,
                    "track_id": str(tid),
                    "bbox": [x1, y1, x2, y2],
                    "last_seen": ts,
                    "cls": cls,
                    "conf": conf,
                })
        return out

    # payload-type = 0: d["object"] הוא dict עם bbox, id וכו'
    if isinstance(d.get("object"), dict):
        o = d["object"]
        b = o.get("bbox") or {}
        x1, y1 = b.get("topleftx"), b.get("toplefty")
        x2, y2 = b.get("bottomrightx"), b.get("bottomrighty")
        cls = None
        # לפעמים class במבנה שונה — לא חובה לנו
        conf = None
        # person.confidence בד"כ קיים
        person = o.get("person")
        if isinstance(person, dict) and "confidence" in person:
            try:
                conf = float(person["confidence"])
            except Exception:
                pass
        return [{
            "sensor": sensor,
            "track_id": str(o.get("id")),
            "bbox": [x1, y1, x2, y2],
            "last_seen": ts,
            "cls": cls,
            "conf": conf,
        }]

    return []
