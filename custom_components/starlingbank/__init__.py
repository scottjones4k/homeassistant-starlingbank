"""The starlingbank component."""
from datetime import timedelta
import logging

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    Platform,
    CONF_NAME,
    CONF_TOKEN
)

from .const import (
    DOMAIN,
)

from homeassistant.core import HomeAssistant
from homeassistant.util import Throttle
from homeassistant.helpers import entity_registry
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=3)

class StarlingData:
    """Get the latest data and update the states."""

    def __init__(self, config):
        """Init the starling data object."""
        from starlingbank import StarlingAccount
        
        self.config = config
        self.available = False
        self.spaces = []
        self.starling_account = StarlingAccount(
            config[CONF_TOKEN]
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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Starling from a config entry."""

    instance = await hass.async_add_executor_job(create_and_update_instance, entry)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = instance

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

def create_and_update_instance(entry: ConfigEntry) -> StarlingData:
    """Create and update a Starling instance."""
    instance = StarlingData(entry.data)
    instance.update()
    return instance

async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""

    await hass.config_entries.async_reload(config_entry.entry_id)

    registry = entity_registry.async_get(hass)
    entities = entity_registry.async_entries_for_config_entry(
        registry, config_entry.entry_id
    )