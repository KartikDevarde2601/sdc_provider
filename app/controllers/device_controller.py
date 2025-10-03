"""Controller for managing individual device connections."""
import logging
from typing import Optional, Callable, Dict
from models.device import Device, DeviceStatus
from services.connection_service import ConnectionService
from services.metric_service import MetricService

logger = logging.getLogger(__name__)


class DeviceController:
    """Manages connection and interaction with a specific device."""

    def __init__(self, device: Device, discovery_service):
        self.device = device
        self.discovery_service = discovery_service
        self.connection_service: Optional[ConnectionService] = None
        self.metric_service = MetricService()
        self._on_connected_callback: Optional[Callable] = None
        self._on_disconnected_callback: Optional[Callable] = None
        self._on_error_callback: Optional[Callable] = None

    async def connect(self):
        """Connect to the device asynchronously."""
        try:
            logger.info(f"Attempting to connect to device: {self.device.epr}")

            # Find the WSD service for this device
            wsd_service = await self._find_wsd_service()
            if not wsd_service:
                raise Exception(
                    f"Could not find WSD service for device {self.device.epr}")

            # Create connection service
            self.connection_service = ConnectionService(self.device)
            self.connection_service.connect(wsd_service)

            # Subscribe to metrics
            self.connection_service.subscribe_to_metrics(
                self._on_metric_update)

            logger.info(f"Successfully connected to {self.device.epr}")

            # Notify callback
            if self._on_connected_callback:
                self._on_connected_callback()

        except Exception as e:
            self.device.status = DeviceStatus.ERROR
            logger.error(f"Failed to connect to {self.device.epr}: {e}")
            if self._on_error_callback:
                self._on_error_callback(str(e))
            raise

    async def _find_wsd_service(self):
        """Find the WSD service object for this device."""
        # Search for services again to get fresh WSD service objects
        services = self.discovery_service.search_services(timeout=5)
        for service in services:
            if service.epr == self.device.epr:
                return service
        return None

    def disconnect(self):
        """Disconnect from the device."""
        try:
            if self.connection_service:
                self.connection_service.disconnect()

            logger.info(f"Disconnected from {self.device.epr}")

            # Notify callback
            if self._on_disconnected_callback:
                self._on_disconnected_callback()

        except Exception as e:
            logger.error(f"Error disconnecting from {self.device.epr}: {e}")
            if self._on_error_callback:
                self._on_error_callback(str(e))

    def _on_metric_update(self, metrics_by_handle: dict):
        """
        Internal callback for metric updates from connection service.
        Processes metrics through metric service.
        """
        if self.connection_service:
            self.metric_service.process_metric_update(
                metrics_by_handle,
                self.connection_service
            )

    def get_latest_metrics(self) -> Dict:
        """Get the latest values for all metrics."""
        return self.metric_service.get_all_latest_metrics()

    def get_metric_history(self, handle: str, limit: int = None):
        """Get historical data for a specific metric."""
        return self.metric_service.get_metric_history(handle, limit)

    def register_metric_callback(self, callback: Callable):
        """
        Register callback for metric updates.

        Args:
            callback: Function(List[MetricData]) to call on updates
        """
        self.metric_service.register_callback(callback)

    def unregister_metric_callback(self, callback: Callable):
        """Unregister metric callback."""
        self.metric_service.unregister_callback(callback)

    def is_connected(self) -> bool:
        """Check if connected to device."""
        return (self.connection_service is not None and
                self.connection_service.is_connected())

    def set_on_connected_callback(self, callback: Callable):
        """Set callback for successful connection."""
        self._on_connected_callback = callback

    def set_on_disconnected_callback(self, callback: Callable):
        """Set callback for disconnection."""
        self._on_disconnected_callback = callback

    def set_on_error_callback(self, callback: Callable):
        """Set callback for errors."""
        self._on_error_callback = callback
