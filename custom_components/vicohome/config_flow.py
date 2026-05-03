"""Config flow for VicoHome integration."""

import voluptuous as vol
from typing import Any
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.config_entries import ConfigEntry, ConfigEntryBaseFlow
import aiohttp
import logging

from .const import DOMAIN, CONF_REGION, DEFAULT_REGION, DEFAULT_POLLING_INTERVAL, CONF_POLLING_INTERVAL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_EMAIL): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(["eu", "us"]),
    vol.Optional(CONF_POLLING_INTERVAL, default=DEFAULT_POLLING_INTERVAL): vol.All(
        vol.Coerce(int), vol.Range(min=60, max=3600)
    ),
})


async def validate_credentials(email: str, password: str, region: str) -> bool:
    """Validate VicoHome credentials by logging in."""
    base = f"https://api-{region}.vicohome.io"
    payload = {"email": email, "password": password, "loginType": 0}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base}/account/login",
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                return data.get("result") == 0
    except Exception as err:
        _LOGGER.error("Credential validation failed: %s", err)
        return False


class VicoHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VicoHome."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]
            region = user_input.get(CONF_REGION, DEFAULT_REGION)

            await self.async_set_unique_id(email)
            self._abort_if_unique_id_configured()

            if await validate_credentials(email, password, region):
                return self.async_create_entry(
                    title=f"VicoHome ({email})",
                    data=user_input,
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
