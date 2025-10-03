"""Controller for device discovery operations."""
import logging
from typing import List, Callable
from models.device import Device
from services.discovery_service import DiscoveryService

logger = logging.getLogger(__name__)


class DiscoveryController:
    """Handles device discovery logic and state."""

    def __init__(self):
        self.discovery_service = DiscoveryService()
        self.discovered_devices: List[Device] = []
        self._on_devices_found_callback: Callable = None
        self._on_error_callback: Callable = None
        self._is_searching = False

    def initialize(self):
        """Initialize the controller and start discovery service."""
        try:
            self.discovery_service.start()
            logger.info("Discovery controller initialized")
        except Exception as e:
            logger.error(f"Failed to initialize discovery controller: {e}")
            if self._on_error_callback:
                self._on_error_callback(str(e))
            raise

    def shutdown(self):
        """Shutdown the controller and stop discovery service."""
        try:
            self.discovery_service.stop()
            logger.info("Discovery controller shutdown")
        except Exception as e:
            logger.error(f"Error during discovery controller shutdown: {e}")

    async def search_for_devices(self, timeout: int = None):
        """
        Asynchronously search for devices on the network.

        Args:
            timeout: Search timeout in seconds
        """
        if self._is_searching:
            logger.warning("Search already in progress")
            return

        try:
            self._is_searching = True
            logger.info("Starting device search...")
            print(f"DEBUG: Starting search with timeout={timeout}")

            # Perform discovery (blocking call, should run in executor for true async)
            import asyncio
            loop = asyncio.get_event_loop()
            devices = await loop.run_in_executor(
                None,
                self.discovery_service.search_devices,
                timeout
            )
            self.discovered_devices = devices

            logger.info(f"Search complete. Found {len(devices)} device(s)")
            print(f"DEBUG: Found {len(devices)} devices")

            # Notify callback
            if self._on_devices_found_callback:
                self._on_devices_found_callback(devices)
            else:
                logger.warning("No callback set for devices found!")

        except Exception as e:
            logger.error(f"Error during device search: {e}", exc_info=True)
            print(f"DEBUG: Error during search: {e}")
            if self._on_error_callback:
                self._on_error_callback(str(e))
        finally:
            self._is_searching = False
            print("DEBUG: Search completed")

    def get_device_by_epr(self, epr: str) -> Device:
        """
        Get a discovered device by its EPR.

        Args:
            epr: Device endpoint reference

        Returns:
            Device object or None
        """
        for device in self.discovered_devices:
            if device.epr == epr:
                return device
        return None

    def is_searching(self) -> bool:
        """Check if a search is currently in progress."""
        return self._is_searching

    def set_on_devices_found_callback(self, callback: Callable):
        """
        Set callback to be called when devices are found.

        Args:
            callback: Function(List[Device]) to call with discovered devices
        """
        self._on_devices_found_callback = callback

    def set_on_error_callback(self, callback: Callable):
        """
        Set callback to be called on errors.

        Args:
            callback: Function(str) to call with error message
        """
        self._on_error_callback = callback
