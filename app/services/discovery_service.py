"""Service for discovering SDC devices on the network."""
import logging
from typing import List
from sdc11073.wsdiscovery import WSDiscovery
from sdc11073.definitions_sdc import SdcV1Definitions
from models.device import Device, DeviceStatus
from config.settings import settings

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Handles device discovery using WS-Discovery protocol."""

    def __init__(self):
        self.discovery = None
        self._is_running = False

    def start(self):
        """Start the discovery service."""
        if self._is_running:
            logger.warning("Discovery service already running")
            return

        try:
            self.discovery = WSDiscovery(settings.DISCOVERY_ADDRESS)
            self.discovery.start()
            self._is_running = True
            logger.info("Discovery service started")
        except Exception as e:
            logger.error(f"Failed to start discovery service: {e}")
            raise

    def stop(self):
        """Stop the discovery service."""
        if self.discovery and self._is_running:
            try:
                self.discovery.stop()
                self._is_running = False
                logger.info("Discovery service stopped")
            except Exception as e:
                logger.error(f"Error stopping discovery service: {e}")

    def search_devices(self, timeout: int = None) -> List[Device]:
        """
        Search for SDC medical devices on the network.

        Args:
            timeout: Search timeout in seconds

        Returns:
            List of discovered Device objects
        """
        if not self._is_running:
            raise RuntimeError("Discovery service not started")

        timeout = timeout or settings.DISCOVERY_TIMEOUT
        devices = []

        try:
            logger.info(f"Searching for devices (timeout: {timeout}s)...")
            services = self.discovery.search_services(
                types=SdcV1Definitions.MedicalDeviceTypesFilter,
                timeout=timeout
            )

            logger.info(f"services find services {services}")

            for service in services:
                try:
                    device = Device(
                        epr=service.epr,
                        name=self._extract_device_name(service),
                        ip_address=self._extract_ip_address(service),
                        status=DeviceStatus.DISCOVERED
                    )
                    devices.append(device)
                    logger.info(f"Discovered device: {device.epr}")
                except Exception as e:
                    logger.error(f"Error processing discovered device: {e}")

            logger.info(f"Discovery complete. Found {len(devices)} device(s)")

        except Exception as e:
            logger.error(f"Error during device search: {e}")
            raise

        return devices

    def _extract_device_name(self, service) -> str:
        """Extract device name from service info."""
        # Try to get a friendly name from service metadata
        # This is a placeholder - adjust based on actual service structure
        if hasattr(service, 'scopes') and service.scopes:
            for scope in service.scopes:
                if 'name' in scope.lower():
                    return scope.split('/')[-1]
        return service.epr.split(':')[-1][:8]  # Use part of UUID as fallback

    def _extract_ip_address(self, service) -> str:
        """Extract IP address from service info."""
        # This is a placeholder - adjust based on actual service structure
        if hasattr(service, 'xaddrs') and service.xaddrs:
            addr = service.xaddrs[0]
            # Extract IP from URL like "http://192.168.1.100:8080/..."
            if '://' in addr:
                addr = addr.split('://')[1]
            if ':' in addr:
                addr = addr.split(':')[0]
            return addr
        return None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
