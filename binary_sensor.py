import asyncio

"""Support for getting information from Arduino analog pins."""
import logging

import voluptuous as vol

from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorDevice
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_PINS = "pins"
CONF_PULLUP = "pullup"

PIN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_PULLUP, default=False): cv.boolean
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_PINS): vol.Schema({cv.positive_int: PIN_SCHEMA})}
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Arduino platform."""
    board = hass.data[DOMAIN]

    pins = config[CONF_PINS]

    sensors = []
    for pinnum, pin in pins.items():
        sensors.append(ArduinoBinarySensor(pin.get(CONF_NAME), pinnum, pin.get(CONF_PULLUP), board))
    add_entities(sensors)


class ArduinoBinarySensor(BinarySensorDevice):
    """Representation of an Arduino Binary Sensor."""

    def __init__(self, name, pin, pullup, board):
        """Initialize the sensor."""
        self._pin = pin
        self._name = name
        self._value = None
        self._board = board

        if pullup:
            self._board.set_pin_mode_digital_input_pullup(self._pin, self._cb)
        else:
            self._board.set_pin_mode_digital_input(self._pin, self._cb)

    def _cb(self, data):
        self._value = data[2]
        self.async_write_ha_state()

    @property
    def is_on(self):
        return self._value

    @property
    def name(self):
        """Get the name of the pin"""
        return self._name

    @property
    def should_poll(self):
        """Return whether HA should poll for data updates."""
        return False
