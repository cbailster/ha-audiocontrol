"""Main HDMI Matrix Client for high-level control operations."""

from .data import Amp, InputSource
from .exceptions import AudioControlConnectionError, AudioControlTimeoutError, AudioControlCommandError
from .http_client import HTTPClient

class AudioControlClient:
    """Main client for controlling AudioControl Amplifiers.

    Supports HTTP protocol for device communication.

    Attributes:
        host: IP address or hostname of the amplifier
        http_port: HTTP port if using HTTP (default: 80)
        timeout: Connection timeout in seconds (default: 10)
    """
    def __init__(self, host: str, http_port: int = 80, timeout: int = 10) -> None:
        """Initialize AudioControl Client.

        Args:
            host: IP address or hostname of the amplifier
            http_port: HTTP port if using HTTP (default: 80)
            timeout: Connection timeout in seconds (default: 10)

        Raises:
            ValueError: If invalid connection type specified
        """
        self.host = host
        self.timeout = timeout

        self.client = HTTPClient(host, http_port, timeout)
        self.amp_info = Amp()
        self.endpoint = HTTPClient.DETAILED_ENDPOINT

    async def get_device_info(self):
        """Get device information from the Amplifier.

        Raises:
            AudioControlConnectionError: If not connected
            AudioControlCommandError: If command fails
        """

        try:
            # Fetch the JSON response
            response = await self.client.get(self.endpoint, decode = True)

            # Check status code
            if response["status"] != 200:
                raise AudioControlCommandError(  # noqa: TRY301
                    f"Failed to get device info: HTTP {response['status']}"
                )

            self.amp_info.populate_from_dict(response["text"])
            self.flip_endpoint()

        except (AudioControlConnectionError, AudioControlTimeoutError) as e:
            raise AudioControlCommandError(f"Failed to retrieve device info: {e}") from e

    def flip_endpoint(self) -> None:
        """Switch endpoints for querying amp status based on which one was last called"""
        if self.endpoint == HTTPClient.DETAILED_ENDPOINT:
            self.endpoint = HTTPClient.OPERATION_ENDPOINT
        else:
            self.endpoint = HTTPClient.DETAILED_ENDPOINT

    async def send_command(self, command: dict[str, str], signal_processing = False):
        """Send a command to the amplifier.

        Args:
            command: Command to execute
            signal_processing: If True, send to signal processing endpoint otherwise using operation endpoint

        Raises:
            AudioControlCommandError: If command fails
        """
        result = await self.client.send_command(command=command, signal_processing=signal_processing)
        if result and self.client.cached_response is not None:
            self.amp_info.populate_from_dict(self.client.cached_response)
            self.client.cached_response = None

    async def amp_power(self, status: bool):
        """Send a command to turn on/off the amplifier."""
        cmd = self.amp_info.power_cmd(status)
        await self.send_command(command=cmd)

    async def channel_power(self, zone_id:str, status:bool):
        """Send a command to turn on/off a specific zone on the amplifier."""
        zone = self.amp_info.zones[zone_id]
        cmd = zone.power_cmd(status)
        await self.send_command(command=cmd)

    async def channel_mute(self, zone_id:str, status:bool):
        """Send a command to mute/unmute a specific zone on the amplifier."""
        zone = self.amp_info.zones[zone_id]
        cmd = zone.mute_cmd(status)
        await self.send_command(command=cmd, signal_processing=True)

    async def channel_stereo(self, zone_id:str, status:bool):
        """ Send a command to set a specific zone to stereo/mono output on the amplifier."""
        zone = self.amp_info.zones[zone_id]
        cmd = zone.stereo_cmd(status)
        await self.send_command(command=cmd)

    async def channel_volume(self, zone_id:str, volume:int):
        """Send a command to set the volume for a specific zone on the amplifier."""
        zone = self.amp_info.zones[zone_id]
        cmd = zone.volume_cmd(volume)
        await self.send_command(command=cmd, signal_processing=True)

    async def channel_input(self, zone_id:str, ipt: InputSource):
        """Send a command to set the input source for a specific zone on the amplifier."""
        zone = self.amp_info.zones[zone_id]
        cmd = zone.input_cmd(ipt)
        await self.send_command(command=cmd, signal_processing=True)

    def connect(self) -> None:
        """Establish connection to the amplifier."""
        # Implementation to be completed
        pass  # noqa: PIE790 pylint: disable=unnecessary-pass

    def disconnect(self) -> None:
        """Close connection to the amplifier."""
        # Implementation to be completed
        pass  # noqa: PIE790 pylint: disable=unnecessary-pass

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
