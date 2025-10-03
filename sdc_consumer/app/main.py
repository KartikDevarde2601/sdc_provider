"""
SDC Medical Device Monitor - Main Application Entry Point

This application implements a medical device monitoring system using the SDC standard.
It follows MVC architecture for scalability and maintainability.
"""
import logging
import asyncio
from nicegui import ui, app
from controllers.discovery_controller import DiscoveryController
from controllers.device_controller import DeviceController
from views.main_view import MainView
from views.device_view import DeviceView
from models.device import Device
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SDCMonitorApp:
    """Main application class coordinating all components."""

    def __init__(self):
        self.discovery_controller = DiscoveryController()
        self.current_device_controller = None
        self.main_view = None
        self.device_view = None

    def initialize(self):
        """Initialize the application."""
        try:
            # Initialize discovery controller
            self.discovery_controller.initialize()

            # Set up controller callbacks
            self.discovery_controller.set_on_devices_found_callback(
                self._on_devices_found
            )
            self.discovery_controller.set_on_error_callback(
                self._on_discovery_error
            )

            logger.info("Application initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise

    def shutdown(self):
        """Clean shutdown of the application."""
        try:
            # Disconnect from any connected device
            if self.current_device_controller:
                self.current_device_controller.disconnect()

            # Shutdown discovery
            self.discovery_controller.shutdown()

            logger.info("Application shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def run(self):
        """Run the application."""
        # Set up routes
        self.setup_routes()

        # Handle app shutdown
        app.on_shutdown(self.shutdown)

        # Start NiceGUI
        ui.run(
            title='SDC Medical Device Monitor',
            favicon='🏥',
            dark=False,
            reload=False
        )

    def setup_routes(self):
        """Set up application routes."""

        @ui.page('/')
        def main_page():
            """Main device discovery page."""
            self.main_view = MainView(
                on_device_selected=self._on_device_selected)
            self.main_view.render()

            # Connect search callback to controller
            self.main_view.set_search_callback(self._on_search_clicked)

        @ui.page('/device')
        def device_page():
            """Device monitoring page."""
            if not self.current_device_controller:
                ui.notify('No device connected', type='warning')
                ui.navigate.to('/')
                return

            device = self.current_device_controller.device
            self.device_view = DeviceView(
                device, on_back=self._on_back_to_main)
            self.device_view.render()

            # Register for metric updates
            self.current_device_controller.register_metric_callback(
                self.device_view.update_metrics
            )

    async def _on_search_clicked(self):
        """Handle search button click."""
        self.main_view.show_searching()
        await self.discovery_controller.search_for_devices()
        self.main_view.hide_searching()

    def _on_devices_found(self, devices):
        """Callback when devices are discovered."""
        self.main_view.display_devices(devices)

    def _on_discovery_error(self, error_message):
        """Callback when discovery encounters an error."""
        self.main_view.show_error(error_message)

    async def _on_device_selected(self, device: Device):
        """Handle device selection from main view."""
        try:
            logger.info(f"User selected device: {device.epr}")

            # Show loading notification
            notification = ui.notification(
                'Connecting to device...', type='ongoing')

            # Create device controller
            self.current_device_controller = DeviceController(
                device,
                self.discovery_controller.discovery_service.discovery
            )

            # Set up callbacks
            self.current_device_controller.set_on_connected_callback(
                lambda: self._on_device_connected(notification)
            )
            self.current_device_controller.set_on_error_callback(
                lambda msg: self._on_device_error(msg, notification)
            )

            # Connect to device
            await self.current_device_controller.connect()

        except Exception as e:
            logger.error(f"Error connecting to device: {e}")
            if notification:
                notification.dismiss()
            ui.notify(f'Failed to connect: {str(e)}', type='negative')

    def _on_device_connected(self, notification):
        """Callback when device connection is established."""
        notification.dismiss()
        ui.notify('Connected successfully!', type='positive')

        # Navigate to device monitoring view
        ui.navigate.to('/device')

    def _on_device_error(self, error_message, notification):
        """Callback when device connection fails."""
        notification.dismiss()
        ui.notify(f'Connection error: {error_message}', type='negative')

    def _on_back_to_main(self):
        """Handle back button from device view."""
        # Disconnect from device
        if self.current_device_controller:
            self.current_device_controller.disconnect()
            self.current_device_controller = None

        # Navigate back to main view
        ui.navigate.to('/')


def main():
    """Application entry point."""
    try:
        # Create and initialize app
        sdc_app = SDCMonitorApp()
        sdc_app.initialize()

        devices = sdc_app.discovery_controller.discovery_service.search_devices(
            5)
        print(f"Test found {len(devices)} devices")

        # Run the application
        sdc_app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
