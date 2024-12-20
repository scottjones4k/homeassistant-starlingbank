"""Support for balance data via the Starling Bank API."""
from __future__ import annotations

from .starling_update_coordinator import StarlingUpdateCoordinator
from typing import Any
from collections.abc import Callable
from dataclasses import dataclass
import voluptuous as vol

from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_platform
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    SERVICE_SPACE_DEPOSIT,
    SERVICE_SPACE_WITHDRAW
)
from .entity import StarlingBaseEntity

BALANCE_TYPES = ["cleared_balance", "effective_balance"]

CONF_ACCOUNTS = "accounts"
CONF_BALANCE_TYPES = "balance_types"
CONF_SANDBOX = "sandbox"

DEFAULT_SANDBOX = False
DEFAULT_ACCOUNT_NAME = "Starling"

ATTR_NATIVE_BALANCE = "Balance in native currency"

DEFAULT_COIN_ICON = "mdi:cash"

ATTRIBUTION = "Data provided by Starling bank"

POT_SERVICE_SCHEMA = {
    vol.Required('amount_in_minor_units'): vol.All(vol.Coerce(int), vol.Range(0, 65535)),
}

@dataclass(frozen=True, kw_only=True)
class StarlingSensorEntityDescription(SensorEntityDescription):
    """Describes Starling sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType]

ACCOUNT_SENSORS = (
    StarlingSensorEntityDescription(
        key="cleared_balance",
        translation_key="cleared_balance",
        value_fn=lambda data: data.account.cleared_balance / 100,
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
    ),
    StarlingSensorEntityDescription(
        key="effective_balance",
        translation_key="effective_balance",
        value_fn=lambda data: data.account.effective_balance / 100,
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
    ),
)
SPACE_SENSORS = (
    StarlingSensorEntityDescription(
        key="total_saved",
        translation_key="total_saved",
        value_fn=lambda data: data.total_saved_minor_units / 100,
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
    ),
    StarlingSensorEntityDescription(
        key="target_amount",
        translation_key="target_amount",
        value_fn=lambda data: (data.target_minor_units or 0) / 100,
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Plaid sensor platform."""
    coordinator: StarlingUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    name: str = hass.data[DOMAIN][config_entry.entry_id]["name"]

    accounts = [
        StarlingSensor(
            coordinator,
            entity_description,
            index,
            account.name,
            name
        )
        for entity_description in ACCOUNT_SENSORS
        for index, account in coordinator.data.items() if index.startswith("MASTER")
    ]

    spaces = [
        StarlingSensor(
            coordinator,
            entity_description,
            index,
            account.name,
            name
        )
        for entity_description in SPACE_SENSORS
        for index, account in coordinator.data.items() if not index.startswith("MASTER")
    ]

    async_add_entities(accounts + spaces)

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SPACE_DEPOSIT,
        POT_SERVICE_SCHEMA,
        "space_deposit",
    )

    platform.async_register_entity_service(
        SERVICE_SPACE_WITHDRAW,
        POT_SERVICE_SCHEMA,
        "space_withdraw",
    )

class StarlingSensor(StarlingBaseEntity, SensorEntity):
    """Representation of a Balance sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entity_description,
        idx,
        device_model: str,
        account_name: str
    ) -> None:
        """Initialize the sensor."""
        self.idx = idx
        super().__init__(coordinator, idx, device_model, account_name)

        self._attr_state_class = SensorStateClass.TOTAL

        self.entity_description = entity_description

        self._attr_unique_id = f"{self.idx}_{account_name}_{self.entity_description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the state."""

        try:
            state = self.entity_description.value_fn(self.data)
        except (KeyError, ValueError):
            return None

        return state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }
    
    async def space_deposit(self, amount_in_minor_units: int | None = None):
        if self.idx.startswith("MASTER"):
            raise HomeAssistantError("supported only on space sensors")
        await self.coordinator.space_deposit(self.idx, amount_in_minor_units)

    async def space_withdraw(self, amount_in_minor_units: int | None = None):
        if self.idx.startswith("MASTER"):
            raise HomeAssistantError("supported only on space sensors")
        await self.coordinator.space_withdraw(self.idx, amount_in_minor_units)