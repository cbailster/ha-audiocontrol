"""Common data types for the Audio Control integration."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.loader import Integration

if TYPE_CHECKING:
    from .coordinator import AudioControlCoordinator
    from .audiocontrol import AudioControlClient

type AudioControlConfigEntry = ConfigEntry["AudioControlData"]


@dataclass
class AudioControlData:
    """Data for the AudioControl integration."""

    client: "AudioControlClient"
    coordinator: "AudioControlCoordinator"
    integration: Integration
