"""Service for processing and storing metric data."""
import logging
from collections import deque
from typing import Dict, List, Callable
from datetime import datetime
from models.metric import MetricData
from config.settings import settings

logger = logging.getLogger(__name__)


class MetricService:
    """Manages metric data storage and processing."""

    def __init__(self, max_points: int = None):
        """
        Initialize metric service.

        Args:
            max_points: Maximum number of data points to store per metric
        """
        self.max_points = max_points or settings.CHART_MAX_POINTS
        # Store metric history: {handle: deque([MetricData, ...])}
        self._metric_history: Dict[str, deque] = {}
        # Callbacks to notify on metric updates: [callback_func, ...]
        self._update_callbacks: List[Callable] = []

    def process_metric_update(self, metrics_by_handle: dict, connection_service):
        """
        Process incoming metric updates from device.

        Args:
            metrics_by_handle: Dict of {handle: metric_state}
            connection_service: ConnectionService to get descriptor info
        """
        updated_metrics = []

        for handle, metric_state in metrics_by_handle.items():
            try:
                # Skip if no metric value
                if not hasattr(metric_state, 'MetricValue') or metric_state.MetricValue is None:
                    continue

                value = metric_state.MetricValue.Value

                # Get descriptor for unit and name
                descriptor = connection_service.get_metric_descriptor(handle)
                if descriptor is None:
                    logger.warning(f"No descriptor found for metric {handle}")
                    continue

                unit = descriptor.Unit.Code if hasattr(
                    descriptor, 'Unit') else ""
                name = settings.METRIC_NAMES.get(handle, handle)

                # Create metric data object
                metric_data = MetricData(
                    handle=handle,
                    name=name,
                    value=float(value),
                    unit=unit,
                    timestamp=datetime.now()
                )

                # Store in history
                self._add_to_history(metric_data)
                updated_metrics.append(metric_data)

            except Exception as e:
                logger.error(f"Error processing metric {handle}: {e}")

        # Notify callbacks
        if updated_metrics:
            self._notify_callbacks(updated_metrics)

    def _add_to_history(self, metric_data: MetricData):
        """Add metric data to history, maintaining max_points limit."""
        handle = metric_data.handle

        if handle not in self._metric_history:
            self._metric_history[handle] = deque(maxlen=self.max_points)

        self._metric_history[handle].append(metric_data)

    def get_metric_history(self, handle: str, limit: int = None) -> List[MetricData]:
        """
        Get historical data for a metric.

        Args:
            handle: Metric handle
            limit: Maximum number of recent points to return

        Returns:
            List of MetricData objects
        """
        if handle not in self._metric_history:
            return []

        history = list(self._metric_history[handle])
        if limit:
            history = history[-limit:]
        return history

    def get_latest_metric(self, handle: str) -> MetricData:
        """
        Get the most recent value for a metric.

        Args:
            handle: Metric handle

        Returns:
            Latest MetricData or None
        """
        history = self.get_metric_history(handle)
        return history[-1] if history else None

    def get_all_latest_metrics(self) -> Dict[str, MetricData]:
        """Get the latest value for all tracked metrics."""
        return {
            handle: self.get_latest_metric(handle)
            for handle in self._metric_history.keys()
        }

    def register_callback(self, callback: Callable):
        """
        Register a callback to be notified of metric updates.

        Args:
            callback: Function(List[MetricData]) to call on updates
        """
        if callback not in self._update_callbacks:
            self._update_callbacks.append(callback)

    def unregister_callback(self, callback: Callable):
        """Unregister a callback."""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)

    def _notify_callbacks(self, metrics: List[MetricData]):
        """Notify all registered callbacks of metric updates."""
        for callback in self._update_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Error in metric callback: {e}")

    def clear_history(self, handle: str = None):
        """
        Clear metric history.

        Args:
            handle: Specific metric to clear, or None to clear all
        """
        if handle:
            self._metric_history.pop(handle, None)
        else:
            self._metric_history.clear()
