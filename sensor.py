import asyncio

"""Support for getting information from Arduino analog pins."""
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_PINS = "pins"
CONF_DIFF = "differential"

PIN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_DIFF, default=0): cv.positive_int
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
        sensors.append(ArduinoSensor(pin.get(CONF_NAME), pinnum, pin.get(CONF_DIFF), board))
    add_entities(sensors)


class ArduinoSensor(Entity):
    """Representation of an Arduino Sensor."""

    def __init__(self, name, pin, diff, board):
        """Initialize the sensor."""
        self._pin = pin
        self._name = name
        self._diff = diff  # diff=0 means that HA will poll for updates
        self._value = None

        asyncio.run(board.set_pin_mode_analog_input( pin,
            (self._cb if self._diff!=0 else None),
            self._diff if self._diff!=0 else None))
        self._board = board

    async def _cb(self, data):
        self._value = data[2]
        await self.async_write_ha_state()

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._value

    @property
    def name(self):
        """Get the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """Return whether HA should poll for data updates."""
        return self._diff==0

    async def async_update(self):
        """Get the latest value from the pin."""
        _LOGGER.info("pin: "+str(self._pin))
        self._value = (await self._board.analog_read(self._pin))[0]
