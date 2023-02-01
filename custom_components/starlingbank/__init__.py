"""The starlingbank component."""
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    Platform,
    CONF_NAME,
    CONF_TOKEN
)

from .const import (
    DOMAIN,
)


_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=3)

CONFIG_SCHEMA = vol.Schema(
    cv.deprecated(DOMAIN),
    {
        DOMAIN: vol.Schema(
            {
                 vol.Required(CONF_CLIENT_ID): cv.string,
                 vol.Required(CONF_CLIENT_SECRET): cv.string,
                 vol.Required(CONF_TOKEN): cv.string,
                 vol.Optional(CONF_NAME, None): cv.string
            },
        )
    },
    extra=vol.ALLOW_EXTRA,
)

class StarlingData:
    """Get the latest data and update the states."""

    def __init__(self, config):
        """Init the starling data object."""

        self.config = config
        self.available = False
        self.spaces = []
        self.starling_account = StarlingAccount(
            config[CONF_TOKEN], sandbox=config[CONF_SANDBOX]
        )

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from starling."""
        self.starling_account.update_balance_data()
        self.starling_account.update_savings_goal_data()
        self.available = True
        self.spaces = self.starling_account.savings_goals.items()

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Starling component."""
    if DOMAIN not in config:
        return True
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config[DOMAIN],
        )
    )

    return True

def create_and_update_instance(entry: ConfigEntry) -> PlaidData:
    """Create and update a Starling instance."""
    instance = PlaidData(entry.data)
    instance.update()
    return instance

async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""

    await hass.config_entries.async_reload(config_entry.entry_id)

    registry = entity_registry.async_get(hass)
    entities = entity_registry.async_entries_for_config_entry(
        registry, config_entry.entry_id
    )