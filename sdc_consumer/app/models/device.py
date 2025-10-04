"""Device data models."""
from dataclasses import dataclass, field
from typing import Optional, Dict, TYPE_CHECKING
from datetime import datetime
from enum import Enum

# Avoid circular imports
if TYPE_CHECKING:
    from sdc11073.consumer import SdcConsumer
    from sdc11073.mdib import ConsumerMdib


class DeviceStatus(Enum):
    """Device connection status."""
    DISCOVERED = "discovered"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class LocationInfo:
    """Device location information."""
    facility: Optional[str] = None
    poc: Optional[str] = None  # Point of Care
    bed: Optional[str] = None
    room: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None

    def __str__(self):
        parts = []
        if self.facility:
            parts.append(f"Facility: {self.facility}")
        if self.poc:
            parts.append(f"PoC: {self.poc}")
        if self.bed:
            parts.append(f"Bed: {self.bed}")
        if self.room:
            parts.append(f"Room: {self.room}")
        return ", ".join(parts) if parts else "Location not available"


@dataclass
class Device:
    """Represents an SDC medical device with full DPWS information."""

    # Basic identification
    epr: str  # Endpoint reference (UUID)
    name: str = "Unknown Device"
    status: DeviceStatus = DeviceStatus.DISCOVERED
    ip_address: Optional[str] = None
    discovered_at: datetime = field(default_factory=datetime.now)

    # SDC Connection Objects (populated after connection)
    client: Optional['SdcConsumer'] = field(default=None, repr=False)
    mdib: Optional['ConsumerMdib'] = field(default=None, repr=False)

    # DPWS Model Information
    manufacturer: Optional[str] = None
    manufacturer_url: Optional[str] = None
    model_name: Optional[str] = None
    model_number: Optional[str] = None
    model_url: Optional[str] = None
    presentation_url: Optional[str] = None

    # DPWS Device Information
    friendly_name: Optional[str] = None
    firmware_version: Optional[str] = None
    serial_number: Optional[str] = None

    # Location Information
    location: Optional[LocationInfo] = None

    # WS-Discovery service metadata
    xaddrs: Optional[list] = field(default=None, repr=False)
    scopes: Optional[list] = field(default=None, repr=False)

    def __str__(self):
        return f"{self.get_display_name()} ({self.epr})"

    def is_connected(self) -> bool:
        """Check if device has active connection."""
        return self.status == DeviceStatus.CONNECTED and self.client is not None

    def get_display_name(self):
        """Returns a user-friendly display name."""
        # Priority: Friendly Name > Model Name > Manufacturer + Model
        if self.friendly_name:
            return self.friendly_name
        if self.model_name:
            return self.model_name
        if self.manufacturer and self.model_number:
            return f"{self.manufacturer} {self.model_number}"
        if self.manufacturer:
            return self.manufacturer
        return self.name or "Medical Device"

    def get_short_id(self):
        """Returns a shortened version of the EPR for display."""
        if self.epr.startswith('urn:uuid:'):
            return self.epr.replace('urn:uuid:', '')[:8] + '...'
        return self.epr[:16] + '...' if len(self.epr) > 16 else self.epr

    def get_full_info(self) -> str:
        """Returns formatted full device information."""
        lines = [
            f"Device: {self.get_display_name()}",
            f"EPR: {self.epr}",
            f"Status: {self.status.value}",
        ]

        if self.manufacturer:
            lines.append(f"Manufacturer: {self.manufacturer}")
        if self.model_number:
            lines.append(f"Model: {self.model_number}")
        if self.serial_number:
            lines.append(f"Serial: {self.serial_number}")
        if self.firmware_version:
            lines.append(f"Firmware: {self.firmware_version}")
        if self.ip_address:
            lines.append(f"IP Address: {self.ip_address}")
        if self.location:
            lines.append(f"Location: {self.location}")
        if self.is_connected():
            lines.append("Connection: Active ✓")

        return "\n".join(lines)


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
