"""Config flow for Starling Bank integration."""
import voluptuous as vol

from homeassistant.const import CONF_TOKEN, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from typing import Any

from .const import (
    DOMAIN,
)

class StarlingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Starling Bank."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOKEN): str,
                    vol.Optional(
                        CONF_NAME, default=self.hass.config.location_name
                    ): str,
                }
            ),
            errors=errors,
        )