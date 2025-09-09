import json, csv, threading
from pathlib import Path


# models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

BBox = Tuple[float, float, float, float]

@dataclass(frozen=True)
class DetectionEvent:
    ts: datetime
    topic: str
    sensor: Optional[str]
    track_id: str
    bbox: BBox
    cls: Optional[str] = None
    conf: Optional[float] = None


class BaseSink:
    def handle(self, ev: DetectionEvent) -> None:
        raise NotImplementedError


class PrintSink(BaseSink):
    def handle(self, ev: DetectionEvent) -> None:
        x1,y1,x2,y2 = ev.bbox
        parts = [
            ev.ts.isoformat(timespec="milliseconds") + "Z",
            ev.topic,
            ev.sensor or "",
            f"id={ev.track_id}",
            f"bbox=[{x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f}]",
        ]
        if ev.cls:  parts.append(f"cls={ev.cls}")
        if ev.conf is not None: parts.append(f"conf={ev.conf:.3f}")
        print(" | ".join(p for p in parts if p))

class JsonlSink(BaseSink):
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def handle(self, ev: DetectionEvent) -> None:
        rec = {
            "ts": ev.ts.isoformat(timespec="milliseconds")+"Z",
            "topic": ev.topic,
            "sensor": ev.sensor,
            "track_id": ev.track_id,
            "bbox": list(ev.bbox),
            "cls": ev.cls,
            "conf": ev.conf,
        }
        line = json.dumps(rec, ensure_ascii=False)
        with self._lock, self.path.open("a", encoding="utf-8") as f:
            f.write(line+"\n")

class MultiSink(BaseSink):
    def __init__(self, *sinks: BaseSink):
        self.sinks = sinks
    def handle(self, ev: DetectionEvent) -> None:
        for s in self.sinks:
            s.handle(ev)
