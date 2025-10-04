"""Service for discovering SDC devices on the network."""
import logging
from typing import List
from urllib.parse import unquote
from sdc11073.wsdiscovery import WSDiscovery
from sdc11073.definitions_sdc import SdcV1Definitions
from models.device import Device, DeviceStatus, LocationInfo
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
                    device = self._create_device_from_service(service)
                    devices.append(device)
                    logger.info(
                        f"Discovered device: {device.epr} - {device.get_display_name()}")
                except Exception as e:
                    logger.error(
                        f"Error processing discovered device: {e}", exc_info=True)

            logger.info(f"Discovery complete. Found {len(devices)} device(s)")

        except Exception as e:
            logger.error(f"Error during device search: {e}")
            raise

        return devices

    def _create_device_from_service(self, service) -> Device:
        """
        Create Device object from WS-Discovery service.

        Args:
            service: WSD service object

        Returns:
            Device object with extracted information
        """
        # Extract basic info
        epr = service.epr
        ip_address = self._extract_ip_address(service)

        # Extract location from scopes
        location = self._extract_location_from_scopes(service)

        # Create device with discovered information
        device = Device(
            epr=epr,
            name=self._extract_device_name(service),
            ip_address=ip_address,
            status=DeviceStatus.DISCOVERED,
            location=location,
            xaddrs=service.xaddrs if hasattr(service, 'xaddrs') else None,
            scopes=self._extract_scopes(service)
        )

        return device

    def _extract_device_name(self, service) -> str:
        """Extract device name from service info."""
        # Try to get name from scopes or use part of EPR
        if hasattr(service, 'epr'):
            epr = service.epr
            if epr.startswith('urn:uuid:'):
                return f"Device-{epr.replace('urn:uuid:', '')[:8]}"
        return "Unknown Device"

    def _extract_ip_address(self, service) -> str:
        """Extract IP address from service xAddrs."""
        try:
            if hasattr(service, 'xaddrs') and service.xaddrs:
                addr = service.xaddrs[0]
                # Extract IP from URL like "http://192.168.1.100:8080/..."
                if '://' in addr:
                    addr = addr.split('://')[1]
                if ':' in addr:
                    addr = addr.split(':')[0]
                if '/' in addr:
                    addr = addr.split('/')[0]
                return addr
        except Exception as e:
            logger.debug(f"Could not extract IP address: {e}")
        return None

    def _extract_location_from_scopes(self, service) -> LocationInfo:
        """
        Extract location information from WS-Discovery scopes.
        Parses SDC location scope format.
        """
        location = LocationInfo()

        try:
            if not hasattr(service, 'scopes'):
                return location

            scopes = service.scopes

            # Handle ScopesType object - convert to list of strings
            scope_list = []
            if hasattr(scopes, '__iter__') and not isinstance(scopes, str):
                # It's iterable (likely a list)
                scope_list = list(scopes)
            elif hasattr(scopes, 'text'):
                # It's a single scope with text attribute
                scope_list = [scopes.text]
            else:
                # Try to convert to string
                scope_list = [str(scopes)]

            for scope in scope_list:
                scope_str = str(scope)

                # Parse location scope: sdc.ctxt.loc:/sdc.ctxt.loc.detail/...
                if 'sdc.ctxt.loc' in scope_str and '?' in scope_str:
                    # Extract query parameters
                    query_part = scope_str.split('?')[1]
                    query = query_part.split(',')[0]

                    print(f"%$$$%%%%%%%:{query}")

                    params = {}

                    for param in query.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params[key.lower()] = unquote(value)

                    # Map parameters to LocationInfo
                    location.facility = params.get('fac')
                    location.poc = params.get('poc')
                    location.bed = params.get('bed')
                    location.room = params.get('rm')
                    location.building = params.get('bldng')
                    location.floor = params.get('flr')

                    logger.debug(f"Extracted location: {location}")
                    break

        except Exception as e:
            logger.debug(f"Could not extract location from scopes: {e}")

        return location

    def _extract_scopes(self, service) -> list:
        """Extract and convert scopes to list of strings."""
        try:
            if not hasattr(service, 'scopes'):
                return []

            scopes = service.scopes

            # Convert to list of strings
            if hasattr(scopes, '__iter__') and not isinstance(scopes, str):
                return [str(s) for s in scopes]
            else:
                return [str(scopes)]

        except Exception as e:
            logger.debug(f"Could not extract scopes: {e}")
            return []

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
