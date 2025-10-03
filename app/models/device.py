"""Device data models."""
from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime
from enum import Enum


class DeviceStatus(Enum):
    """Device connection status."""
    DISCOVERED = "discovered"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class Device:
    """Represents an SDC medical device."""
    epr: str  # Endpoint reference (UUID)
    name: str = "Unknown Device"
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    status: DeviceStatus = DeviceStatus.DISCOVERED
    ip_address: Optional[str] = None
    discovered_at: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"{self.name} ({self.epr})"

    def get_display_name(self):
        """Returns a user-friendly display name."""
        if self.manufacturer and self.model:
            return f"{self.manufacturer} {self.model}"
        return self.name or "Medical Device"
