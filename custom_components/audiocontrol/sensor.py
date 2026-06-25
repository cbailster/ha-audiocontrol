"""Sensor platform for the Audio Control integration."""

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AudioControlCoordinator
from .data import AudioControlConfigEntry

async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass` pylint: disable=unused-argument
    entry: AudioControlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the temp sensors from a config entry."""
    entities: list[SensorEntity] = []

    entities.append(MainTempSensor(entry.runtime_data.coordinator, entry))

    # Add output zones
    zones = getattr(entry.runtime_data.coordinator.data, "zones", {}).values()
    for zone in zones:
        if not zone.digital:
            entities.append(ZoneTempSensor(entry.runtime_data.coordinator, zone, entry))

    async_add_entities(entities)

class TempSensor(CoordinatorEntity, SensorEntity): # pyright: ignore[reportIncompatibleVariableOverride] pylint: disable=abstract-method
    """Base class for temp sensors."""

    _attr_icon = "mdi:thermometer"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"


    def __init__(
        self, coordinator: AudioControlCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the input status sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data.get("host"))},
        } # pyright: ignore[reportAttributeAccessIssue]

class ZoneTempSensor(TempSensor):
    """ Temperature sensor for each amp zone."""

    def __init__(
            self, coordinator: AudioControlCoordinator, zone: Any, entry: ConfigEntry
    ) -> None:
        """Initialize the main temp sensor."""
        super().__init__(coordinator, entry)
        self._zone_id = getattr(zone, "internal_id", -1)

        zone_name = getattr(zone, "name", f"{self._zone_id} Zone")

        self._attr_name = f"{zone_name} Temperature"
        self._attr_unique_id = f"{DOMAIN}_zone_temp_{self._zone_id}"

    @property
    def native_value(self) -> bool | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the native value of the sensor."""
        zones = getattr(self._coordinator.data,"zones",{})
        if self._zone_id in zones:
            return getattr(zones[self._zone_id], "temp", None)
        return None

class MainTempSensor(TempSensor):
    """ Temperature sensor for the amplifier."""

    def __init__(
            self, coordinator: AudioControlCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the main temp sensor."""
        super().__init__(coordinator, entry)

        self._attr_name = "Amp Temperature"
        self._attr_unique_id = f"{DOMAIN}_amp_temp"

    @property
    def native_value(self) -> bool | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the native value of the sensor."""
        return getattr(self._coordinator.data, "temp", None)
