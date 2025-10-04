"""Utility functions for working with connected devices."""
import logging
from typing import Optional, List, Dict, Any
from models.device import Device

logger = logging.getLogger(__name__)


class DeviceHelper:
    """Helper class for common device operations."""

    @staticmethod
    def get_all_metrics(device: Device) -> Dict[str, Any]:
        """
        Get all current metric values from a connected device.

        Args:
            device: Connected Device object

        Returns:
            Dictionary of {handle: metric_state}
        """
        if not device.is_connected() or not device.mdib:
            logger.warning(f"Device {device.epr} is not connected")
            return {}

        try:
            metrics = {}
            # Get all numeric metric states
            for state in device.mdib.states.NODETYPE.get('NumericMetricState', []):
                if hasattr(state, 'MetricValue') and state.MetricValue is not None:
                    metrics[state.Handle] = state

            return metrics
        except Exception as e:
            logger.error(f"Error getting metrics from device: {e}")
            return {}

    @staticmethod
    def get_metric_value(device: Device, handle: str) -> Optional[float]:
        """
        Get the current value of a specific metric.

        Args:
            device: Connected Device object
            handle: Metric handle (e.g., 'metric.hr')

        Returns:
            Metric value or None
        """
        if not device.is_connected() or not device.mdib:
            return None

        try:
            state = device.mdib.states.handle.get_one(handle, allow_none=True)
            if state and hasattr(state, 'MetricValue') and state.MetricValue:
                return float(state.MetricValue.Value)
        except Exception as e:
            logger.error(f"Error getting metric {handle}: {e}")

        return None

    @staticmethod
    def get_metric_descriptor(device: Device, handle: str) -> Optional[Any]:
        """
        Get the descriptor (metadata) for a metric.

        Args:
            device: Connected Device object
            handle: Metric handle

        Returns:
            Metric descriptor or None
        """
        if not device.is_connected() or not device.mdib:
            return None

        try:
            return device.mdib.descriptions.handle.get_one(handle, allow_none=True)
        except Exception as e:
            logger.error(f"Error getting descriptor for {handle}: {e}")
            return None

    @staticmethod
    def get_metric_unit(device: Device, handle: str) -> str:
        """
        Get the unit of measurement for a metric.

        Args:
            device: Connected Device object
            handle: Metric handle

        Returns:
            Unit string (e.g., 'bpm', '%', '°C')
        """
        descriptor = DeviceHelper.get_metric_descriptor(device, handle)
        if descriptor and hasattr(descriptor, 'Unit') and descriptor.Unit:
            if hasattr(descriptor.Unit, 'Code'):
                return descriptor.Unit.Code
        return ""

    @staticmethod
    def get_all_metric_handles(device: Device) -> List[str]:
        """
        Get all available metric handles from a device.

        Args:
            device: Connected Device object

        Returns:
            List of metric handles
        """
        if not device.is_connected() or not device.mdib:
            return []

        try:
            handles = []
            for state in device.mdib.states.NODETYPE.get('NumericMetricState', []):
                handles.append(state.Handle)
            return handles
        except Exception as e:
            logger.error(f"Error getting metric handles: {e}")
            return []

    @staticmethod
    def invoke_operation(device: Device, operation_handle: str, arguments: Dict = None) -> bool:
        """
        Invoke an operation on the device (e.g., set alarm, start/stop).

        Args:
            device: Connected Device object
            operation_handle: Handle of the operation to invoke
            arguments: Optional arguments for the operation

        Returns:
            True if successful, False otherwise
        """
        if not device.is_connected() or not device.client:
            logger.warning(f"Device {device.epr} is not connected")
            return False

        try:
            # Get the operation from MDIB
            operation = device.mdib.descriptions.handle.get_one(
                operation_handle, allow_none=True)
            if not operation:
                logger.error(f"Operation {operation_handle} not found")
                return False

            # Invoke the operation
            future = device.client.invoke_operation(
                operation_handle, arguments or {})
            result = future.result(timeout=10)

            logger.info(f"Operation {operation_handle} invoked successfully")
            return True

        except Exception as e:
            logger.error(f"Error invoking operation {operation_handle}: {e}")
            return False

    @staticmethod
    def get_device_capabilities(device: Device) -> Dict[str, Any]:
        """
        Get information about device capabilities.

        Args:
            device: Connected Device object

        Returns:
            Dictionary with capability information
        """
        if not device.is_connected() or not device.mdib:
            return {}

        capabilities = {
            'metrics': len(DeviceHelper.get_all_metric_handles(device)),
            'has_location': device.location is not None,
            'manufacturer': device.manufacturer,
            'model': device.model_number,
            'firmware': device.firmware_version,
        }

        return capabilities

    @staticmethod
    def get_device_summary(device: Device) -> str:
        """
        Get a formatted summary of the device.

        Args:
            device: Device object

        Returns:
            Formatted string with device summary
        """
        summary = [
            "=" * 60,
            f"Device: {device.get_display_name()}",
            "=" * 60,
        ]

        if device.manufacturer:
            summary.append(f"Manufacturer: {device.manufacturer}")
        if device.model_number:
            summary.append(f"Model: {device.model_number}")
        if device.serial_number:
            summary.append(f"Serial Number: {device.serial_number}")
        if device.firmware_version:
            summary.append(f"Firmware: {device.firmware_version}")

        summary.append(f"Status: {device.status.value}")
        summary.append(f"EPR: {device.epr}")

        if device.ip_address:
            summary.append(f"IP: {device.ip_address}")

        if device.location:
            summary.append(f"Location: {device.location}")

        if device.is_connected():
            metrics = DeviceHelper.get_all_metric_handles(device)
            summary.append(f"Available Metrics: {len(metrics)}")
            if metrics:
                summary.append("  " + ", ".join(metrics[:5]))
                if len(metrics) > 5:
                    summary.append(f"  ... and {len(metrics) - 5} more")

        summary.append("=" * 60)
        return "\n".join(summary)


# Convenience functions for quick access
def print_device_info(device: Device):
    """Print device information to console."""
    print(DeviceHelper.get_device_summary(device))


def get_hr(device: Device) -> Optional[float]:
    """Quick access to heart rate."""
    return DeviceHelper.get_metric_value(device, 'metric.hr')


def get_spo2(device: Device) -> Optional[float]:
    """Quick access to SpO2."""
    return DeviceHelper.get_metric_value(device, 'metric.spo2')


def get_temp(device: Device) -> Optional[float]:
    """Quick access to temperature."""
    return DeviceHelper.get_metric_value(device, 'metric.temp')
