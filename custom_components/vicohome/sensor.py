"""Sensor platform for VicoHome."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType

from .const import DOMAIN
from .coordinator import VicoHomeCoordinator


def _device_info(coordinator: VicoHomeCoordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.email)},
        name=f"VicoHome ({coordinator.email})",
        manufacturer="VicoHome",
        model="Cloud Camera",
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up VicoHome sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        VicoHomeEventCountSensor(coordinator),
        VicoHomeLastEventSensor(coordinator),
    ])


class VicoHomeEventCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing number of events in last hour."""

    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_event_count"
        self._attr_name = "VicoHome Events (1h)"
        self._attr_native_unit_of_measurement = "events"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        return self.coordinator.data.get("event_count", 0)

    @property
    def extra_state_attributes(self):
        return {
            "last_update": self.coordinator.data.get("last_update"),
        }


class VicoHomeLastEventSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing details of the last/most recent event."""

    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_last_event"
        self._attr_name = "VicoHome Last Event"
        self._attr_device_info = _device_info(coordinator)

    @property
    def available(self) -> bool:
        events = self.coordinator.data.get("events", [])
        return len(events) > 0

    @property
    def native_value(self):
        events = self.coordinator.data.get("events", [])
        if not events:
            return None
        # Most recent event's device name
        return events[0].get("deviceName", "unknown")

    @property
    def extra_state_attributes(self):
        events = self.coordinator.data.get("events", [])
        if not events:
            return {}
        ev = events[0]
        return {
            "trace_id": ev.get("traceId"),
            "timestamp": ev.get("timestamp"),
            "period_seconds": ev.get("period"),
            "file_size": ev.get("fileSize"),
            "ai_tags": ev.get("deviceAiEventList", []),
            "image_url": ev.get("imageUrl"),
            "video_url": ev.get("videoUrl"),
            "event_count": len(events),
        }
