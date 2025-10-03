"""Device monitoring view showing real-time vitals."""
import logging
from nicegui import ui
from typing import Callable, Dict
from models.device import Device
from models.metric import MetricData
from views.components.vital_display import VitalDisplay
from views.components.metric_chart import MetricChart

logger = logging.getLogger(__name__)


class DeviceView:
    """Screen for monitoring a connected device."""

    def __init__(self, device: Device, on_back: Callable):
        """
        Initialize device view.

        Args:
            device: Device to monitor
            on_back: Callback when user wants to go back
        """
        self.device = device
        self.on_back = on_back
        self.vital_displays: Dict[str, VitalDisplay] = {}
        self.charts: Dict[str, MetricChart] = {}

    def render(self):
        """Render the device monitoring view."""
        with ui.column().classes('w-full h-screen p-6 bg-gray-50'):
            # Header
            with ui.card().classes('w-full mb-4'):
                with ui.row().classes('w-full items-center'):
                    ui.button(
                        icon='arrow_back',
                        on_click=self.on_back
                    ).props('flat')

                    with ui.column().classes('flex-grow ml-4'):
                        ui.label(self.device.get_display_name()
                                 ).classes('text-2xl font-bold')
                        ui.label(f'EPR: {self.device.epr}').classes(
                            'text-sm text-gray-600')

                    self.connection_status = ui.label('Connected').classes(
                        'px-4 py-2 rounded-full bg-green-200 text-green-800 font-semibold'
                    )

            # Main content area
            with ui.row().classes('w-full gap-4 flex-grow'):
                # Left column - Vital signs
                with ui.column().classes('w-1/3 gap-4'):
                    ui.label('Current Vitals').classes(
                        'text-xl font-semibold mb-2')

                    # Heart Rate
                    self.vital_displays['metric.hr'] = VitalDisplay(
                        name='Heart Rate',
                        unit='bpm',
                        icon='favorite',
                        color='red'
                    )
                    self.vital_displays['metric.hr'].render()

                    # SpO2
                    self.vital_displays['metric.spo2'] = VitalDisplay(
                        name='SpO₂',
                        unit='%',
                        icon='air',
                        color='blue'
                    )
                    self.vital_displays['metric.spo2'].render()

                    # Temperature
                    self.vital_displays['metric.temp'] = VitalDisplay(
                        name='Temperature',
                        unit='°C',
                        icon='thermostat',
                        color='green'
                    )
                    self.vital_displays['metric.temp'].render()

                # Right column - Charts
                with ui.column().classes('flex-grow gap-4'):
                    ui.label(
                        'Real-Time Trends').classes('text-xl font-semibold mb-2')

                    # Heart Rate Chart
                    self.charts['metric.hr'] = MetricChart(
                        title='Heart Rate',
                        unit='bpm',
                        color='#ef4444'
                    )
                    self.charts['metric.hr'].render()

                    # SpO2 Chart
                    self.charts['metric.spo2'] = MetricChart(
                        title='SpO₂',
                        unit='%',
                        color='#3b82f6'
                    )
                    self.charts['metric.spo2'].render()

        return self

    def update_metrics(self, metrics: list[MetricData]):
        """
        Update displayed metrics.

        Args:
            metrics: List of MetricData objects
        """
        for metric in metrics:
            # Update vital display
            if metric.handle in self.vital_displays:
                self.vital_displays[metric.handle].update_value(metric.value)

            # Update chart
            if metric.handle in self.charts:
                self.charts[metric.handle].add_data_point(
                    metric.value, metric.timestamp)

    def show_disconnected(self):
        """Show disconnected state."""
        self.connection_status.text = 'Disconnected'
        self.connection_status.classes(
            'bg-red-200 text-red-800',
            remove='bg-green-200 text-green-800'
        )
        ui.notify('Device disconnected', type='warning')

    def show_error(self, message: str):
        """Display error message."""
        ui.notify(f'Error: {message}', type='negative')
