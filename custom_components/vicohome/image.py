"""Image platform for VicoHome."""

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
import aiohttp

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
    """Set up VicoHome image entity."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VicoHomeImage(coordinator)])


class VicoHomeImage(CoordinatorEntity, ImageEntity):
    """Image entity showing the latest event snapshot directly in HA."""

    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_image"
        self._attr_name = "VicoHome Letztes Bild"
        self._attr_device_info = _device_info(coordinator)

    @property
    def available(self) -> bool:
        """Return True if there are events to display."""
        return self.coordinator.last_update_success and bool(self.coordinator.data.get("events"))

    @property
    def image_last_updated(self):
        """Return timestamp of last update."""
        return self.coordinator.data.get("last_update")

    async def async_image(self) -> bytes | None:
        """Fetch and return the latest event snapshot image."""
        events = self.coordinator.data.get("events", [])
        if not events:
            return None
        image_url = events[0].get("imageUrl")
        if not image_url:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    return await resp.read()
        except Exception:
            return None
