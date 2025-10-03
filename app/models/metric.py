"""Metric data models."""
from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime
from enum import Enum


@dataclass
class MetricData:
    """Represents a single metric reading."""
    handle: str
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"{self.name}: {self.value} {self.unit}"
