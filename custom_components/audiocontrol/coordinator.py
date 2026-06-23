"""Data coordinator for Audio Control integration."""

from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import LOGGER
from .data import AudioControlConfigEntry
from .audiocontrol.exceptions import (
    AudioControlCommandError,
    AudioControlConnectionError,
    AudioControlTimeoutError,
)

MAX_FAILURES = 3

class AudioControlCoordinator(DataUpdateCoordinator):
    """Audio Control data update coordinator."""

    config_entry: AudioControlConfigEntry
    consecutive_failures: int = 0

    async def _async_setup(self) -> None:
        """Set up the coordinator. Make a double call to get_device info to ensure we get all the data necessary.
            Each call alternates the endpoint between operation and signalProcessing endpoints. We need both to correctly create devices and entities
        """
        await self.config_entry.runtime_data.client.get_device_info()
        await self.config_entry.runtime_data.client.get_device_info()

    async def _async_update_data(self) -> Any:
        """Fetch data from the Audio Control device."""
        try:
            LOGGER.debug("Updating Audio Control data")
            await self.config_entry.runtime_data.client.get_device_info()
            self.consecutive_failures = 0  # Reset on successful update
            return self.config_entry.runtime_data.client.amp_info
        except (AudioControlConnectionError, AudioControlTimeoutError) as err:
            self.consecutive_failures += 1
            LOGGER.error("Error connecting to Audio Control device: %s, consecutive failures: %s", err, self.consecutive_failures)
            if self.consecutive_failures >= MAX_FAILURES:
                raise UpdateFailed(f"Error connecting to Audio Control device: {err}") from err
        except AudioControlCommandError as err:
            self.consecutive_failures += 1
            LOGGER.error("Error fetching data from Audio Control device: %s, consecutive failures: %s", err, self.consecutive_failures)
            if self.consecutive_failures >= MAX_FAILURES:
                raise UpdateFailed(f"Error fetching data from Audio Control device: {err}") from err
