"""The VicoHome integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import VicoHomeCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VicoHome from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    coordinator = VicoHomeCoordinator(hass, entry)
    
    # Run first refresh; don't let API hiccups kill the whole integration
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        _LOGGER.warning("VicoHome first refresh failed, will retry on next poll")
        # Ensure coordinator exists so platforms can set up (entities show 'unavailable' until next successful poll)
        pass
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
