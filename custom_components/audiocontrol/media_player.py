"""Media Player platform for the Audio Control integration."""

from typing import Any

from homeassistant.components.media_player import MediaPlayerEntity,MediaPlayerDeviceClass
from homeassistant.components.media_player.const import MediaPlayerEntityFeature,MediaPlayerState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AudioControlCoordinator
from .data import AudioControlConfigEntry
from .audiocontrol.client import AudioControlClient

async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass` pylint: disable=unused-argument
    entry: AudioControlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AudioControl media player from a config entry."""
    entities: list[MediaPlayerEntity] = []

    # Add a media player for each zone
    zones = getattr(entry.runtime_data.coordinator.data, "zones", {}).values()
    for zone in zones:
        if not zone.digital:
            entities.append(ZoneMediaPlayer(entry.runtime_data.coordinator, zone, entry))

    async_add_entities(entities)

class ZoneMediaPlayer(CoordinatorEntity, MediaPlayerEntity): # pyright: ignore[reportIncompatibleVariableOverride] pylint: disable=abstract-method
    """Base class for temp sensors."""

    _attr_icon = "mdi:speaker"
    _attr_volume_step = 0.05
    _attr_sound_mode_list = ["Stereo", "Mono"]
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER

    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    )

    def __init__(
        self, coordinator: AudioControlCoordinator, zone: Any, entry: ConfigEntry
    ) -> None:
        """Initialize the input status sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self.zone = zone
        self.inputs = self._coordinator.data.inputs

        zone_id = getattr(zone, "internal_id", -1)
        zone_name = getattr(zone, "name", f"{zone_id} Zone")

        self._attr_name = f"{zone_name} Zone"
        self._attr_unique_id = f"{DOMAIN}_zone_media_player_{zone_id}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data.get("host"))},
        } # pyright: ignore[reportAttributeAccessIssue]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        zone_id = self.zone.internal_id
        self.inputs = self._coordinator.data.inputs
        if zone_id in self._coordinator.data.zones:
            self.zone = self._coordinator.data.zones[zone_id]
            super()._handle_coordinator_update()
        self.async_write_ha_state()

    @property
    def client(self) -> AudioControlClient:
        """Shortcut to the client object."""
        return self._coordinator.config_entry.runtime_data.client

    @property
    def state(self) -> MediaPlayerState | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the state of the media player."""
        if self.zone.power:
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Volume level of the media player (0..1)."""
        return self.zone.volume / 100 if self.zone.volume is not None else None

    @property
    def is_volume_muted(self) -> bool | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Boolean if volume is currently muted."""
        return self.zone.mute

    @property
    def sound_mode(self) -> str | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the current sound mode."""
        return "Stereo" if self.zone.stereo else "Mono"

    @property
    def source(self) -> str | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the current input source."""
        return self.inputs[self.zone.input].name if self.zone.input in self.inputs else None

    @property
    def source_list(self) -> list[str] | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """List of available input sources."""
        return [input.name for input in self.inputs.values()] if self.inputs else None

    async def async_turn_on(self) -> None:
        """Turn the media player zone on."""
        await self.client.channel_power(self.zone.internal_id, True)
        self._coordinator.async_update_from_client()

    async def async_turn_off(self) -> None:
        """Turn the media player zone off."""
        await self.client.channel_power(self.zone.internal_id, False)
        self._coordinator.async_update_from_client()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        await self.client.channel_volume(self.zone.internal_id, int(volume * 100))
        self._coordinator.async_update_from_client()

    async def async_volume_up(self) -> None:
        """ Increase volume by set amount (volume step)"""
        new_vol = max(100, self.zone.volume + int(self._attr_volume_step * 100))
        await self.async_set_volume_level(new_vol / 100)

    async def async_volume_down(self) -> None:
        """ Decrease volume by set amount (volume step)"""
        new_vol = max(0, self.zone.volume - int(self._attr_volume_step * 100))
        await self.async_set_volume_level(new_vol / 100)

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute (true) or unmute (false) volume."""
        await self.client.channel_mute(self.zone.internal_id, mute)
        self._coordinator.async_update_from_client()

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        input_source = self.client.amp_info.input_from_name(source)
        if input_source is not None:
            await self.client.channel_input(self.zone.internal_id, input_source)
            self._coordinator.async_update_from_client()

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Select sound mode."""
        if sound_mode == "Stereo":
            await self.client.channel_stereo(self.zone.internal_id, True)
        elif sound_mode == "Mono":
            await self.client.channel_stereo(self.zone.internal_id, False)
        self._coordinator.async_update_from_client()
