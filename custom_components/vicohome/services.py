"""Services for VicoHome."""

from homeassistant.core import HomeAssistant, callback
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_call
import voluptuous as vol

from .const import DOMAIN
from .coordinator import VicoHomeCoordinator

# Keine eigenen Services nötig – alles über Entities steuerbar via HA Automationen
# Diese Datei kann später erweitert werden (z.B. manueller Event-Refresh)

SERVICES = {}

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the services for VicoHome."""
    pass

async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload VicoHome services."""
    pass
