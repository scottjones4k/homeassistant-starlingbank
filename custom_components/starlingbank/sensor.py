"""Support for balance data via the Starling Bank API."""
from __future__ import annotations

import logging

from starlingbank import StarlingAccount

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

BALANCE_TYPES = ["cleared_balance", "effective_balance"]

CONF_ACCOUNTS = "accounts"
CONF_BALANCE_TYPES = "balance_types"
CONF_SANDBOX = "sandbox"

DEFAULT_SANDBOX = False
DEFAULT_ACCOUNT_NAME = "Starling"

ATTR_NATIVE_BALANCE = "Balance in native currency"

DEFAULT_COIN_ICON = "mdi:cash"

ATTRIBUTION = "Data provided by Starling bank"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Plaid sensor platform."""
    instance = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SensorEntity] = []

    for balance_type in BALANCE_TYPES:
        entities.append(StarlingBalanceSensor(instance, "Starling", balance_type))

    for id, space in instance.starling_account.savings_goals.items():
        entities.append(StarlingSpaceSensor(instance, "Starling", id))

    async_add_entities(entities)


class StarlingBalanceSensor(SensorEntity):
    """Representation of a Starling balance sensor."""

    def __init__(self, starling_account, account_name, balance_data_type):
        """Initialize the sensor."""
        self._starling_data = starling_account
        self._balance_data_type = balance_data_type
        self._state = None
        self._account_name = account_name
        self._attr_state_class = SensorStateClass.TOTAL

    @property
    def available(self):
        """Return the name of the sensor."""
        return self._starling_data.available

    @property
    def name(self):
        """Return the name of the sensor."""
        return "{} {}".format(
            self._account_name, self._balance_data_type.replace("_", " ").capitalize()
        )

    @property
    def unique_id(self):
        """Return the Unique ID of the sensor."""
        return f"starling-{self._account_name}-{self._balance_data_type}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._starling_data.starling_account.currency

    @property
    def icon(self):
        """Return the entity icon."""
        return DEFAULT_COIN_ICON

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._starling_data.update()
        if self._balance_data_type == "cleared_balance":
            self._state = self._starling_data.starling_account.cleared_balance / 100
        elif self._balance_data_type == "effective_balance":
            self._state = self._starling_data.starling_account.effective_balance / 100

class StarlingSpaceSensor(SensorEntity):
    """Representation of a Starling space sensor."""

    def __init__(self, starling_account, account_name, uid):
        """Initialize the sensor."""
        self._starling_data = starling_account
        self.uid = uid
        self._state = None
        self._attr_state_class = SensorStateClass.TOTAL
        for id, space in self._starling_data.starling_account.savings_goals.items():
            if (
                id == self.uid
            ):
                self._name = f"{account_name} - {space.name}"
                self._state = space.total_saved_minor_units / 100
                self._currency = space.total_saved_currency

    @property
    def available(self):
        """Return the name of the sensor."""
        return self._starling_data.available

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the Unique ID of the sensor."""
        return f"starling-{self.uid}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._currency

    @property
    def icon(self):
        """Return the entity icon."""
        return DEFAULT_COIN_ICON

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._starling_data.update()
        for id, space in self._starling_data.starling_account.savings_goals.items():
            if (
                id == self.uid
            ):
                self._state = space.total_saved_minor_units / 100