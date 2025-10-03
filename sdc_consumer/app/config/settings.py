"""Application configuration settings."""
import uuid


class Settings:
    """Central configuration for the SDC Monitor application."""

    # Network Configuration
    DISCOVERY_ADDRESS = "10.239.42.255"
    DISCOVERY_TIMEOUT = 10  # seconds

    # Device Configuration
    BASE_UUID = uuid.UUID('{cc013678-79f6-403c-998f-3cc0cc050230}')

    # UI Configuration
    CHART_MAX_POINTS = 100  # Maximum data points to display in charts
    UPDATE_INTERVAL = 1.0   # seconds

    # Logging
    LOG_LEVEL = "INFO"

    # Chart colors
    CHART_COLORS = {
        'hr': '#ef4444',      # Red for heart rate
        'spo2': '#3b82f6',    # Blue for SpO2
        'temp': '#10b981',    # Green for temperature
        'default': '#6b7280'  # Gray for others
    }

    # Metric display names
    METRIC_NAMES = {
        'metric.hr': 'Heart Rate',
        'metric.spo2': 'SpO₂',
        'metric.temp': 'Temperature'
    }


settings = Settings()
