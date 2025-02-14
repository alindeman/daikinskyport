"""Support for displaying weather info from Daikin Skyport API."""
from datetime import datetime, timedelta
from pytz import timezone, utc
import logging

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_SPEED,
    WeatherEntity,
)
from homeassistant.const import TEMP_CELSIUS
from homeassistant.util import dt as dt_util
from .const import (
    _LOGGER,
    DOMAIN,
)
ATTR_FORECAST_TEMP_HIGH = "temphigh"
ATTR_FORECAST_PRESSURE = "pressure"
ATTR_FORECAST_VISIBILITY = "visibility"
ATTR_FORECAST_HUMIDITY = "humidity"

MISSING_DATA = -5002

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Daikin Skyport weather platform."""
    if discovery_info is None:
        return
    dev = list()
    data = hass.data[DOMAIN]
    for index in range(len(data.daikinskyport.thermostats)):
        thermostat = data.daikinskyport.get_thermostat(index)
        dev.append(DaikinSkyportWeather(data,thermostat["name"], index))

    add_entities(dev, True)


class DaikinSkyportWeather(WeatherEntity):
    """Representation of Daikin Skyport weather data."""

    def __init__(self, data, name, index):
        """Initialize the Daikin Skyport weather platform."""
        self.data = data
        self._name = name
        self._attr_unique_id = f"{data.daikinskyport.thermostats[index]['id']}-{self._name}"
        self._index = index
        self.weather = None

    def get_forecast(self, param):
        """Retrieve forecast parameter."""
        try:
            return self.weather[param]
        except (ValueError, IndexError, KeyError):
            raise ValueError

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def condition(self):
        """Return the current condition."""
        try:
            return self.get_forecast("weatherTodayCond")
        except ValueError:
            return None

    @property
    def native_temperature(self):
        """Return the temperature."""
        try:
            return float(self.get_forecast("weatherTodayTempC"))
        except ValueError:
            return None

    @property
    def native_temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def humidity(self):
        """Return the humidity."""
        try:
            return int(self.get_forecast("weatherTodayHum"))
        except ValueError:
            return None

    @property
    def forecast(self):
        """Return the forecast array."""
        try:
            forecasts = []
            date = dt_util.utcnow()
            for day in range(1, 5):
                forecast = {
                    ATTR_FORECAST_TIME: date.isoformat(),
                    ATTR_FORECAST_CONDITION: self.weather["weatherDay" + str(day) + "Cond"],
                    ATTR_FORECAST_TEMP: float(self.weather["weatherDay" + str(day) + "TempC"]),
                    ATTR_FORECAST_HUMIDITY: int(self.weather["weatherDay" + str(day) + "Hum"])
                    }
                date += timedelta(days=1)
                forecasts.append(forecast)
            return forecasts
        except (ValueError, IndexError, KeyError):
            return None

    def update(self):
        """Get the latest state of the sensor."""
        self.data.update()
        self.weather = dict()
        thermostat = self.data.daikinskyport.get_thermostat(self._index)
        for key in thermostat:
            if key.startswith('weather'):
                self.weather[key] = thermostat[key]
        self.weather["tz"] = thermostat["timeZone"]
