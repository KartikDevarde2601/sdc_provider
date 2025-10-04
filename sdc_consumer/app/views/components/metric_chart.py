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

        # Chart configuration (created once)
        self.chart_config = {
            'data': [{
                'x': [],
                'y': [],
                'type': 'scatter',
                'mode': 'lines+markers',
                'line': {'color': self.color, 'width': 3},
                'marker': {'size': 4, 'color': self.color},
                'fill': 'tozeroy',
                'fillcolor': self._get_fill_color(),
                'name': self.title,
            }],
            'layout': {
                'margin': {'l': 60, 'r': 20, 't': 40, 'b': 50},
                'xaxis': {
                    'title': 'Time',
                    'showgrid': True,
                    'gridcolor': '#e5e7eb',
                    'zeroline': False,
                    'autorange': True,
                },
                'yaxis': {
                    'title': self.unit,
                    'showgrid': True,
                    'gridcolor': '#e5e7eb',
                    'zeroline': False,
                    'autorange': True,
                },
                'plot_bgcolor': '#fafafa',
                'paper_bgcolor': '#ffffff',
                'height': 280,
                'showlegend': False,
                'hovermode': 'closest',
            }
        }

    def render(self):
        """Render the chart component."""
        with ui.card().classes('w-full'):
            ui.label(self.title).classes('text-lg font-semibold mb-2')

            # Create the chart using plotly
            self.chart = ui.plotly(self.chart_config).classes('w-full')

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

        # Update chart data only (not layout)
        if self.chart:
            # Use Plotly's restyle method for efficient updates
            # This only updates the data traces, not the entire figure
            self.chart.figure['data'][0]['x'] = list(self.time_labels)
            self.chart.figure['data'][0]['y'] = list(self.data_points)

            # Force update
            self.chart.update()

    def _get_fill_color(self):
        """Get a semi-transparent fill color based on the line color."""
        # Convert hex to rgba with 20% opacity
        hex_color = self.color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({r},{g},{b},0.15)'

    def clear(self):
        """Clear all data from the chart."""
        self.data_points.clear()
        self.time_labels.clear()
        if self.chart:
            self.chart.figure['data'][0]['x'] = []
            self.chart.figure['data'][0]['y'] = []
            self.chart.update()

    def set_y_range(self, min_val: float, max_val: float):
        """
        Set a fixed Y-axis range (useful for metrics with known ranges).

        Args:
            min_val: Minimum Y value
            max_val: Maximum Y value
        """
        if self.chart:
            self.chart.figure['layout']['yaxis']['range'] = [min_val, max_val]
            self.chart.figure['layout']['yaxis']['autorange'] = False
            self.chart.update()

    def enable_auto_range(self):
        """Enable automatic Y-axis ranging."""
        if self.chart:
            self.chart.figure['layout']['yaxis']['autorange'] = True
            self.chart.update()
