"""Data Classes for AudioControl library."""

from dataclasses import dataclass
from typing import Any

def temp_conversion(temp: float, unit: str) -> float:
    """Convert temperature to the specified unit.

    Args:
        temp: Temperature value to convert
        unit: Target unit ('C' for Celsius, 'F' for Fahrenheit)

    Returns:
        Converted temperature value
    """
    if unit == "C":
        return temp
    if unit == "F":
        return round((temp - 32) / 1.8, 1)  # Convert Fahrenheit to Celsius
    else:
        raise ValueError("Invalid temperature unit. Use 'C' or 'F'.")

@dataclass
class InputSource:
    """Represents an input source for the AudioControl Amp.

    Attributes:
        name: Name of the input source
        id: Unique identifier for the input source
    """
    name: str | None = None
    id: int | None = None
    digital: bool = False

    def populate_from_dict(self, data: dict[str, Any]) -> None:
        """Populate the InputSource attributes from a dictionary."""
        self.name = data.get("name")
        self.id = data.get("value")
        self.digital = (self.id == 8 or self.id == 9)  # Assumes 8 and 9 are digital inputs

    @classmethod
    def from_inputs_list(cls, inputs_list: list[dict[str, Any]]) -> list["InputSource"]:
        """Create a list of InputSource instances from a list of dictionaries."""
        sources = []
        for input_data in inputs_list:
            source = cls()
            source.populate_from_dict(input_data)
            sources.append(source)
        return sources

@dataclass
class Zone: # pylint: disable=too-many-instance-attributes
    """Represents a zone in the AudioControl Amp.

    Attributes:
        name: Name of the zone
        id: Unique identifier for the zone
        input_source: Input source assigned to the zone
        volume: Current volume level of the zone
        mute: Mute status of the zone
    """
    name: str | None = None
    id: int | None = None
    input_source: InputSource | None = None
    volume: int = 0
    temp: float = 0.0
    power: bool = False
    mute: bool = False
    stereo: bool = True

    def __post_init__(self):
        if self.volume < 0 or self.volume > 100:
            raise ValueError("Volume must be between 0 and 100.")

    def power_cmd(self, power: bool) -> dict[str, str]:
        """Returns the command to power on the zone."""
        return {f"zonePower_{self.id}": "1" if power else "0"}

    def volume_cmd(self, volume: int) -> dict[str, str]:
        """Returns the command to set the volume of the zone."""
        if volume < 0 or volume > 100:
            raise ValueError("Volume must be between 0 and 100.")
        return {f"outputZone_{self.id}_volume": str(volume)}

    def mute_cmd(self, mute: bool) -> dict[str, str]:
        """Returns the command to mute the zone."""
        return {f"outputZone_{self.id}_mute": "1" if mute else "0"}

    def stereo_cmd(self, stereo: bool) -> dict[str, str]:
        """Returns the command to set the stereo mode of the zone."""
        return {f"mono_{self.id}": "0" if stereo else "1"}

    def input_cmd(self, input_source: InputSource) -> dict[str, str]:
        """Returns the command to set the input source of the zone."""
        return {f"outputZone_{self.id}_inputSource": str(input_source.id)}

    def populate_from_dict(self, data: dict[str, Any], temp_unit: str = "F") -> None:
        """Populate the Zone attributes from a dictionary."""
        self.name = data.get("name")
        self.temp = temp_conversion(data.get("tempValue", 0.0), temp_unit)
        self.power = bool(data.get("zonePower", 0))
        self.mute = bool(data.get("mute", 0))
        if "value" in data:
            self.id = data.get("value")
        if "volume" in data:
            self.volume = data.get("volume", 0)
        if "mono" in data:
            self.stereo = not bool(data.get("mono", 0))

    @classmethod
    def from_zones_list(cls, zones_list: list[dict[str, Any]], temp_unit: str = "F") -> list["Zone"]:
        """Create a list of Zone instances from a list of dictionaries."""
        zones = []
        for zone_data in zones_list:
            zone = cls()
            zone.populate_from_dict(data=zone_data, temp_unit=temp_unit)
            zones.append(zone)
        return zones


@dataclass
class Amp: # pylint: disable=too-many-instance-attributes
    """Represents the AudioControl Amp.

    Attributes:
        name: Name of the amp
        inputs: List of input sources in the amp
        zones: List of zones in the amp
        temp: Current temperature of the amp
    """
    name: str | None = None
    model: str | None = None
    version: str | None = None
    inputs: list[InputSource] | None = None
    zones: list[Zone] | None = None
    temp: float = 0.0
    temp_unit: str = "F"  # Default to Fahrenheit
    power: bool = False

    def input_from_name(self, name: str) -> InputSource | None:
        """Returns the input source with the given name."""
        for input_source in self.inputs or []:
            if input_source.name == name:
                return input_source
        return None

    def power_cmd(self, power: bool) -> dict[str, str]:
        """Returns the command to power on the amp."""
        return {"mainPower": "1" if power else "0"}

    def populate_from_dict(self, data: dict[str, Any]) -> None:
        """Populate the Amp attributes from a dictionary."""
        self.name = data.get("ampName")
        self.model = data.get("ampModel")
        self.power = bool(data.get("mainPower", 0))
        self.temp_unit = "C" if data.get("displayCentigrade", 0) == 1 else "F"
        if "build" in data:
            self.version = data.get("build")
        if "temp" in data:
            self.temp = temp_conversion(data.get("temp", 0.0), self.temp_unit)

        if "inputNames" in data:
            self.inputs = InputSource.from_inputs_list(data.get("inputNames", []))
        elif "inputChannel" in data:
            self.inputs = InputSource.from_inputs_list(data.get("inputChannel", []))

        if "outputZones" in data:
            self.zones = Zone.from_zones_list(data.get("outputZones", []), temp_unit=self.temp_unit)
        elif "outputZone" in data:
            self.zones = Zone.from_zones_list(data.get("outputZone", []), temp_unit=self.temp_unit)
