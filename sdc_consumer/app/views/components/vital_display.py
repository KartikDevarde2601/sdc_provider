"""Component for displaying a single vital sign value."""
from nicegui import ui


class VitalDisplay:
    """Displays a vital sign with large readable numbers."""

    def __init__(self, name: str, unit: str, icon: str = 'monitor_heart', color: str = 'blue'):
        """
        Initialize vital display component.

        Args:
            name: Display name of the vital
            unit: Unit of measurement
            icon: Material icon name
            color: Color theme (red, blue, green, etc.)
        """
        self.name = name
        self.unit = unit
        self.icon = icon
        self.color = color
        self.value_label = None
        self.card = None

    def render(self):
        """Render the vital display component."""
        color_classes = {
            'red': 'border-red-500 bg-red-50',
            'blue': 'border-blue-500 bg-blue-50',
            'green': 'border-green-500 bg-green-50',
            'yellow': 'border-yellow-500 bg-yellow-50'
        }

        icon_colors = {
            'red': 'text-red-600',
            'blue': 'text-blue-600',
            'green': 'text-green-600',
            'yellow': 'text-yellow-600'
        }

        card_class = color_classes.get(
            self.color, 'border-gray-500 bg-gray-50')
        icon_class = icon_colors.get(self.color, 'text-gray-600')

        with ui.card().classes(f'w-full border-l-4 {card_class}') as self.card:
            with ui.row().classes('w-full items-center'):
                ui.icon(self.icon, size='lg').classes(icon_class)
                ui.label(self.name).classes('text-lg font-semibold ml-2')

            with ui.row().classes('w-full items-baseline mt-2'):
                self.value_label = ui.label('--').classes('text-5xl font-bold')
                ui.label(self.unit).classes('text-2xl text-gray-600 ml-2')

        return self

    def update_value(self, value: float):
        """
        Update the displayed value.

        Args:
            value: New value to display
        """
        if self.value_label:
            # Format based on value type
            if value >= 100:
                formatted_value = f'{value:.0f}'
            elif value >= 10:
                formatted_value = f'{value:.1f}'
            else:
                formatted_value = f'{value:.2f}'

            self.value_label.text = formatted_value

    def set_color(self, color: str):
        """Change the color theme of the component."""
        self.color = color
        # Re-render would be needed for color change
