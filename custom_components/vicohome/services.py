"""Services for VicoHome."""

from homeassistant.core import HomeAssistant, callback
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_call
import voluptuous as vol

from .const import DOMAIN
from .coordinator import VicoHomeCoordinator

# No custom services needed - everything is controllable via entities in HA automations
# This file can be extended later (e.g. a manual event refresh)

SERVICES = {}

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the services for VicoHome."""
    pass

async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload VicoHome services."""
    pass
