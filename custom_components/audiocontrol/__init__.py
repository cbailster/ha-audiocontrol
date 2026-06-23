"""The Audio Control integration."""

# from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.loader import async_get_loaded_integration

from .const import DOMAIN, LOGGER
from .coordinator import AudioControlCoordinator
from .audiocontrol.client import AudioControlClient
from .data import AudioControlData, AudioControlConfigEntry
from .config_flow import DEFAULT_SCAN_INTERVAL, DEFAULT_PORT

# Platforms to set up for this integration
PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.MEDIA_PLAYER, Platform.SENSOR]
PLATFORMS: list[Platform] = [Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: AudioControlConfigEntry) -> bool:
    """Set up BluStream from a config entry."""
    host = str(entry.data.get(CONF_HOST))
    port = int(entry.data.get(CONF_PORT, DEFAULT_PORT))
    scan_interval = int(entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

    coordinator = AudioControlCoordinator(
        hass = hass,
        logger = LOGGER,
        name = DOMAIN,
        update_interval = timedelta(seconds=scan_interval),
    )

    entry.runtime_data = AudioControlData(
        client = AudioControlClient(host, http_port=port),
        coordinator = coordinator,
        integration = async_get_loaded_integration(hass, entry.domain)
    )

    await coordinator.async_config_entry_first_refresh()

    device_registry = dr.async_get(hass)
    identifiers = {(DOMAIN, host)}


    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers=identifiers,
        manufacturer="AudioControl",
        name=getattr(entry.runtime_data.client.amp_info, "name", entry.title) or host,
        model=getattr(entry.runtime_data.client.amp_info, "model", None),
        sw_version=getattr(entry.runtime_data.client.amp_info, "version", None),
    )

    # Set up platforms after the coordinator has initial data
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AudioControlConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant,
    entry: AudioControlConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
