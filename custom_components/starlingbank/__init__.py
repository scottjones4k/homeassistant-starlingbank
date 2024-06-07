"""The starlingbank component."""
from datetime import timedelta
import logging

from .starling_data import StarlingData
from .starling_update_coordinator import StarlingUpdateCoordinator
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    Platform,
    CONF_TOKEN
)

from .const import (
    DOMAIN,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=3)

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
    from starlingbank import StarlingAccount

    instance = await hass.async_add_executor_job(create_and_update_instance, entry)

    auth = StarlingAccount(
        instance[CONF_TOKEN]
    )
    client = StarlingData(auth)

    coordinator = StarlingUpdateCoordinator(hass, client)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

def create_and_update_instance(entry: ConfigEntry) -> StarlingData:
    """Create and update a Starling instance."""
    _LOGGER.debug(entry.data[CONF_TOKEN])
    instance = StarlingData(entry.data)
    return instance