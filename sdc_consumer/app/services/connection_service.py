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

            # Store in device object for easy access
            self.device.client = self.consumer
            self.device.mdib = self.mdib

            # Populate device information from DPWS and MDIB
            self._populate_device_info()

            self.device.status = DeviceStatus.CONNECTED
            logger.info(f"Successfully connected to {self.device.epr}")

        except Exception as e:
            self.device.status = DeviceStatus.ERROR
            logger.error(f"Failed to connect to {self.device.epr}: {e}")
            raise

    def _populate_device_info(self):
        """Extract and populate device information from DPWS and MDIB."""
        try:
            # Get DPWS Model Information
            if hasattr(self.consumer, 'host_description') and self.consumer.host_description:
                host_desc = self.consumer.host_description

                # Model Information
                if hasattr(host_desc, 'this_model') and host_desc.this_model:
                    model = host_desc.this_model
                    self.device.manufacturer = self._get_text(
                        getattr(model, 'Manufacturer', None))
                    self.device.manufacturer_url = getattr(
                        model, 'ManufacturerUrl', None)
                    self.device.model_name = self._get_text(
                        getattr(model, 'ModelName', None))
                    self.device.model_number = getattr(
                        model, 'ModelNumber', None)
                    self.device.model_url = getattr(model, 'ModelUrl', None)
                    self.device.presentation_url = getattr(
                        model, 'PresentationUrl', None)

                # Device Information
                if hasattr(host_desc, 'this_device') and host_desc.this_device:
                    device_info = host_desc.this_device
                    self.device.friendly_name = self._get_text(
                        getattr(device_info, 'FriendlyName', None))
                    self.device.firmware_version = getattr(
                        device_info, 'FirmwareVersion', None)
                    self.device.serial_number = getattr(
                        device_info, 'SerialNumber', None)

            # Get Location from MDIB if not already set
            if self.device.location is None or not any([
                self.device.location.facility,
                self.device.location.poc,
                self.device.location.bed
            ]):
                self._populate_location_from_mdib()

            logger.info(
                f"Device info populated: {self.device.get_display_name()}")

        except Exception as e:
            logger.warning(f"Could not fully populate device info: {e}")

    def _populate_location_from_mdib(self):
        """Extract location information from MDIB context states."""
        try:
            from sdc11073.xml_types import pm_qnames as pm
            from sdc11073.xml_types import pm_types
            from models.device import LocationInfo

            location_contexts = self.mdib.context_states.NODETYPE.get(
                pm.LocationContextState, [])

            for loc in location_contexts:
                if loc.ContextAssociation == pm_types.ContextAssociation.ASSOCIATED:
                    if loc.LocationDetail:
                        detail = loc.LocationDetail
                        self.device.location = LocationInfo(
                            facility=getattr(detail, 'Facility', None),
                            poc=getattr(detail, 'PoC', None),
                            bed=getattr(detail, 'Bed', None),
                            room=getattr(detail, 'Room', None),
                            building=getattr(detail, 'Building', None),
                            floor=getattr(detail, 'Floor', None)
                        )
                        logger.info(
                            f"Location populated from MDIB: {self.device.location}")
                        break

        except Exception as e:
            logger.debug(f"Could not extract location from MDIB: {e}")

    def _get_text(self, value):
        """Extract text from LocalizedStringType or return value as-is."""
        if value is None:
            return None
        if isinstance(value, list) and len(value) > 0:
            first_item = value[0]
            if hasattr(first_item, 'text'):
                return first_item.text
        elif hasattr(value, 'text'):
            return value.text
        return str(value) if value else None

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
