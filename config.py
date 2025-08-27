# config.py

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BrokerConfig:
    host: str = "127.0.0.1"
    port: int = 1883
    topics: list[str] = field(default_factory=lambda: ["test-topic"])
    qos: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    keepalive: int = 60
    pretty: bool = False
    save_path: Optional[str] = None
