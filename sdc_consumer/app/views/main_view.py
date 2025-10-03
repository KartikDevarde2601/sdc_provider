"""Main view for device discovery and selection."""
import logging
from nicegui import ui
from typing import Callable
from models.device import Device, DeviceStatus

logger = logging.getLogger(__name__)


class MainView:
    """Main screen showing device discovery and list."""

    def __init__(self, on_device_selected: Callable):
        """
        Initialize main view.

        Args:
            on_device_selected: Callback(Device) when user selects a device
        """
        self.on_device_selected = on_device_selected
        self.device_cards = {}  # {epr: ui.card}
        self.search_callback = None  # Will be set by controller

    def render(self):
        """Render the main view."""
        with ui.column().classes('w-full items-center p-8'):
            # Header
            ui.label('SDC Medical Device Monitor').classes(
                'text-4xl font-bold mb-8')

            # Search section
            with ui.card().classes('w-full max-w-4xl mb-4'):
                with ui.row().classes('w-full items-center gap-4'):
                    ui.label('Discover Devices:').classes('text-lg')
                    self.search_button = ui.button(
                        'Search Network',
                        on_click=self._handle_search_click,
                        icon='search'
                    ).classes('ml-auto')
                    self.search_spinner = ui.spinner(size='lg')
                    self.search_spinner.visible = False

            # Status message
            self.status_label = ui.label(
                'Click "Search Network" to find devices').classes('text-gray-600 mb-4')

            # Device list container
            self.devices_container = ui.column().classes('w-full max-w-4xl gap-4')

        return self

    async def _handle_search_click(self):
        """Internal handler for search button click."""
        if self.search_callback:
            await self.search_callback()
        else:
            logger.warning("Search callback not set!")
            ui.notify("Search function not initialized", type='warning')

    def set_search_callback(self, callback: Callable):
        """
        Set the callback function for search button.

        Args:
            callback: Async function to call when search is clicked
        """
        self.search_callback = callback

    def show_searching(self):
        """Show searching state."""
        self.search_button.disable()
        self.search_spinner.visible = True
        self.status_label.text = 'Searching for devices...'
        self.status_label.classes(
            'text-blue-600', remove='text-gray-600 text-red-600 text-green-600')

    def hide_searching(self):
        """Hide searching state."""
        self.search_button.enable()
        self.search_spinner.visible = False

    def display_devices(self, devices: list[Device]):
        """
        Display discovered devices.

        Args:
            devices: List of Device objects to display
        """
        self.devices_container.clear()
        self.device_cards.clear()

        if not devices:
            self.status_label.text = 'No devices found. Please ensure devices are online and try again.'
            self.status_label.classes(
                'text-gray-600', remove='text-blue-600 text-red-600 text-green-600')
            return

        self.status_label.text = f'Found {len(devices)} device(s)'
        self.status_label.classes(
            'text-green-600', remove='text-blue-600 text-gray-600 text-red-600')

        with self.devices_container:
            for device in devices:
                self._create_device_card(device)

    def _create_device_card(self, device: Device):
        """Create a card for a single device."""
        with ui.card().classes('w-full hover:shadow-lg transition-shadow cursor-pointer') as card:
            self.device_cards[device.epr] = card

            with ui.row().classes('w-full items-center'):
                # Device icon
                ui.icon('monitor_heart', size='lg').classes('text-blue-600')

                # Device info
                with ui.column().classes('flex-grow'):
                    ui.label(device.get_display_name()).classes(
                        'text-xl font-semibold')
                    ui.label(f'EPR: {device.epr}').classes(
                        'text-sm text-gray-500')
                    if device.ip_address:
                        ui.label(f'IP: {device.ip_address}').classes(
                            'text-sm text-gray-500')

                # Status badge
                self._create_status_badge(device.status)

                # Connect button
                ui.button(
                    'Connect',
                    on_click=lambda d=device: self.on_device_selected(d),
                    icon='link'
                ).props('color=primary')

    def _create_status_badge(self, status: DeviceStatus):
        """Create status badge for device."""
        colors = {
            DeviceStatus.DISCOVERED: 'bg-gray-200 text-gray-800',
            DeviceStatus.CONNECTING: 'bg-yellow-200 text-yellow-800',
            DeviceStatus.CONNECTED: 'bg-green-200 text-green-800',
            DeviceStatus.DISCONNECTED: 'bg-gray-300 text-gray-700',
            DeviceStatus.ERROR: 'bg-red-200 text-red-800'
        }
        color = colors.get(status, 'bg-gray-200 text-gray-800')
        ui.label(status.value.title()).classes(
            f'px-3 py-1 rounded-full text-sm {color}')

    def show_error(self, message: str):
        """Display error message."""
        self.status_label.text = f'Error: {message}'
        self.status_label.classes(
            'text-red-600', remove='text-blue-600 text-gray-600 text-green-600')
        ui.notify(message, type='negative')
