"""Service for managing SDC device connections."""
import logging
from typing import Optional, Callable
from sdc11073.consumer import SdcConsumer
from sdc11073.mdib import ConsumerMdib
from sdc11073 import observableproperties
from models.device import Device, DeviceStatus

logger = logging.getLogger(__name__)


class ConnectionService:
    """Manages connection to a single SDC device."""

    def __init__(self, device: Device):
        self.device = device
        self.consumer: Optional[SdcConsumer] = None
        self.mdib: Optional[ConsumerMdib] = None
        self._metric_callback: Optional[Callable] = None

    def connect(self, wsd_service):
        """
        Connect to the device.

        Args:
            wsd_service: WS-Discovery service object from discovery
        """
        try:
            logger.info(f"Connecting to device: {self.device.epr}")
            self.device.status = DeviceStatus.CONNECTING

            # Create SDC consumer
            self.consumer = SdcConsumer.from_wsd_service(
                wsd_service,
                ssl_context_container=None
            )
            self.consumer.start_all()

            # Initialize MDIB
            self.mdib = ConsumerMdib(self.consumer)
            self.mdib.init_mdib()

            self.device.status = DeviceStatus.CONNECTED
            logger.info(f"Successfully connected to {self.device.epr}")

        except Exception as e:
            self.device.status = DeviceStatus.ERROR
            logger.error(f"Failed to connect to {self.device.epr}: {e}")
            raise

    def disconnect(self):
        """Disconnect from the device."""
        try:
            if self._metric_callback and self.mdib:
                # Unbind the callback
                observableproperties.unbind(
                    self.mdib,
                    metrics_by_handle=self._metric_callback
                )

            if self.consumer:
                self.consumer.stop_all()

            self.device.status = DeviceStatus.DISCONNECTED
            logger.info(f"Disconnected from {self.device.epr}")

        except Exception as e:
            logger.error(f"Error disconnecting from {self.device.epr}: {e}")

    def subscribe_to_metrics(self, callback: Callable):
        """
        Subscribe to metric updates from the device.

        Args:
            callback: Function to call when metrics are updated
                     Should accept (metrics_by_handle: dict) parameter
        """
        if not self.mdib:
            raise RuntimeError("Not connected to device")

        self._metric_callback = callback
        observableproperties.bind(
            self.mdib,
            metrics_by_handle=callback
        )
        logger.info(f"Subscribed to metrics for {self.device.epr}")

    def get_metric_descriptor(self, handle: str):
        """
        Get descriptor information for a metric.

        Args:
            handle: Metric handle

        Returns:
            Metric descriptor or None
        """
        if not self.mdib:
            return None

        return self.mdib.descriptions.handle.get_one(handle, allow_none=True)

    def is_connected(self) -> bool:
        """Check if currently connected to device."""
        return self.device.status == DeviceStatus.CONNECTED

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
