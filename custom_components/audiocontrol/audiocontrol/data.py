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
        if temp < 32:
            return 0
        return round((temp - 32) / 1.8, 1)  # Convert Fahrenheit to Celsius

    raise ValueError("Invalid temperature unit. Use 'C' or 'F'.")

@dataclass
class InputSource:
    """Represents an input source for the AudioControl Amp.

    Attributes:
        name: Name of the input source
        id: Unique identifier for the input source
    """
    name: str | None = None # In both JSON files
    id: int | None = None   # In both JSON files
    digital: bool = False   # Inferred from id (8 and 9 are digital inputs)

    def populate_from_dict(self, data: dict[str, Any]) -> None:
        """Populate the InputSource attributes from a dictionary."""
        self.name = data.get("name")
        self.id = data.get("value")
        self.digital = bool(self.id in (8,9))  # Assumes 8 and 9 are digital inputs

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
    name: str | None = None                 # In both JSON files
    internal_id: str | None = None          # In both JSON files
    id: int | None = None                   # In only signalprocessing.json
    input_source: int | None = None         # In both JSON files
    volume: int | None = None               # In only signalprocessing.json
    temp: float = 0.0                       # In both JSON files
    power: bool = False                     # In both JSON files
    mute: bool = False                      # In both JSON files
    stereo: bool = True                     # In only operation.json

    def __post_init__(self):
        if self.volume is not None and (self.volume < 0 or self.volume > 100):
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
        self.internal_id = data.get("identifier")
        self.input_source = data.get("inputSource", 0)
        self.temp = temp_conversion(data.get("tempValue", 0.0), temp_unit)
        self.power = bool(data.get("zonePower", 0))
        self.mute = bool(data.get("mute", 0))
        if "value" in data:
            self.id = data.get("value")
        if "volume" in data:
            self.volume = data.get("volume", 0)
        if "mono" in data:
            self.stereo = not bool(data.get("mono", 0))

@dataclass
class Amp: # pylint: disable=too-many-instance-attributes
    """Represents the AudioControl Amp.

    Attributes:
        name: Name of the amp
        inputs: List of input sources in the amp
        zones: List of zones in the amp
        temp: Current temperature of the amp
    """
    name: str | None = None     # In both JSON files
    model: str | None = None    # In both JSON files
    version: str | None = None  # In only operation.json
    temp: float = 0.0           # In only operation.json
    temp_unit: str = "F"        # In both JSON files [Default to Fahrenheit]
    power: bool = False         # In both JSON files
    inputs: dict[int, InputSource] = {}
    zones: dict[str, Zone] = {}


    def input_from_name(self, name: str) -> InputSource | None:
        """Returns the input source with the given name."""
        input_list = [] if self.inputs is None else self.inputs.values()
        for input_source in input_list or []:
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
        if "tempValue" in data:
            self.temp = temp_conversion(data.get("tempValue", 0.0), self.temp_unit)

        input_data: list[dict[str, Any]] = []
        if "inputNames" in data:
            input_data = data.get("inputNames", [])
        elif "inputChannel" in data:
            input_data = data.get("inputChannel", [])

        for i in input_data:
            val: int = i.get("value", 0)
            if id in self.inputs:
                self.inputs[val].populate_from_dict(i)
            else:
                self.inputs[val] = InputSource()
                self.inputs[val].populate_from_dict(i)


        zone_data: list[dict[str, Any]] = []
        if "outputZones" in data:
            zone_data = data.get("outputZones", [])
        elif "outputZone" in data:
            zone_data = data.get("outputZone", [])

        for z in zone_data:
            identifier: str = z.get("identifier", 0)
            if identifier in self.zones:
                self.zones[identifier].populate_from_dict(z)
            else:
                self.zones[identifier] = Zone()
                self.zones[identifier].populate_from_dict(z)
