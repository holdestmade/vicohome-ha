"""Binary sensor platform for VicoHome motion detection."""

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
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
    """Set up VicoHome binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VicoHomeMotionSensor(coordinator)])


class VicoHomeMotionSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that turns on when a new event is detected."""

    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_motion"
        self._attr_name = "VicoHome Motion"
        self._attr_device_class = BinarySensorDeviceClass.MOTION
        self._attr_device_info = _device_info(coordinator)
        self._last_triggered = None
        self._last_event_count = 0

    @property
    def is_on(self) -> bool:
        events = self.coordinator.data.get("events", [])
        count = len(events)
        # Only trigger on new events (count increased since last poll)
        if count > 0 and count != self._last_event_count:
            self._last_event_count = count
            self._last_triggered = self.coordinator.data.get("last_update")
            return True
        return False

    @property
    def extra_state_attributes(self):
        return {
            "last_triggered": self._last_triggered,
            "event_count_in_window": self.coordinator.data.get("event_count", 0),
        }
