"""Component for displaying real-time metric charts."""
from nicegui import ui
from datetime import datetime
from collections import deque


class MetricChart:
    """Displays a real-time line chart for a metric."""

    def __init__(self, title: str, unit: str, color: str = '#3b82f6', max_points: int = 50):
        """
        Initialize metric chart component.

        Args:
            title: Chart title
            unit: Unit of measurement
            color: Line color in hex format
            max_points: Maximum number of data points to display
        """
        self.title = title
        self.unit = unit
        self.color = color
        self.max_points = max_points
        self.chart = None
        self.data_points = deque(maxlen=max_points)
        self.time_labels = deque(maxlen=max_points)

    def render(self):
        """Render the chart component."""
        with ui.card().classes('w-full'):
            ui.label(self.title).classes('text-lg font-semibold mb-2')

            # Create the chart using plotly
            self.chart = ui.plotly({
                'data': [{
                    'x': list(self.time_labels),
                    'y': list(self.data_points),
                    'type': 'scatter',
                    'mode': 'lines',
                    'line': {'color': self.color, 'width': 2},
                    'fill': 'tozeroy',
                    'fillcolor': self._get_fill_color(),
                }],
                'layout': {
                    'margin': {'l': 50, 'r': 20, 't': 20, 'b': 40},
                    'xaxis': {
                        'title': 'Time',
                        'showgrid': True,
                        'gridcolor': '#e5e7eb'
                    },
                    'yaxis': {
                        'title': self.unit,
                        'showgrid': True,
                        'gridcolor': '#e5e7eb'
                    },
                    'plot_bgcolor': '#ffffff',
                    'paper_bgcolor': '#ffffff',
                    'height': 250
                }
            }).classes('w-full')

        return self

    def add_data_point(self, value: float, timestamp: datetime = None):
        """
        Add a new data point to the chart.

        Args:
            value: Metric value
            timestamp: Time of reading (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Add to deques (automatically removes oldest if at max_points)
        self.data_points.append(value)
        self.time_labels.append(timestamp.strftime('%H:%M:%S'))

        # Update chart
        if self.chart:
            self.chart.update_figure({
                'data': [{
                    'x': list(self.time_labels),
                    'y': list(self.data_points),
                    'type': 'scatter',
                    'mode': 'lines',
                    'line': {'color': self.color, 'width': 2},
                    'fill': 'tozeroy',
                    'fillcolor': self._get_fill_color(),
                }]
            })

    def _get_fill_color(self):
        """Get a semi-transparent fill color based on the line color."""
        # Convert hex to rgba with 20% opacity
        hex_color = self.color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({r},{g},{b},0.2)'

    def clear(self):
        """Clear all data from the chart."""
        self.data_points.clear()
        self.time_labels.clear()
        if self.chart:
            self.chart.update_figure({
                'data': [{
                    'x': [],
                    'y': [],
                    'type': 'scatter',
                    'mode': 'lines',
                    'line': {'color': self.color, 'width': 2}
                }]
            })
