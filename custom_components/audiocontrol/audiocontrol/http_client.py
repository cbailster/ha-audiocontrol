"""HTTP client for communicating with HDMI matrix devices."""

import asyncio
from typing import Any

import aiohttp

from .exceptions import AudioControlCommandError, AudioControlConnectionError, AudioControlTimeoutError


class HTTPClient:
    """HTTP client for communicating with AudioControl Amp over HTTP protocol.

    Attributes:
        host: IP address or hostname of the matrix device
        port: HTTP port number (default: 80)
        timeout: Request timeout in seconds
    """
    OPERATION_ENDPOINT = "/json/operation.json"
    DETAILED_ENDPOINT = "/json/signalprocessing.json"
    SUMMARY_ENDPOINT = "/json/realTimeData.json"

    def __init__(
        self,
        host: str,
        port: int = 80,
        timeout: int = 10,
    ) -> None:
        """Initialize HTTP client.

        Args:
            host: IP address or hostname of the matrix device
            port: HTTP port number (default: 80)
            timeout: Request timeout in seconds (default: 10)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.cached_response: dict[str, Any] | None = None

    async def _make_request(
        self, endpoint: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        decode: bool = True
    ) -> dict[str, Any]:
        """Send a {method} request to the matrix device.

        Args:
            endpoint: API endpoint path
            method: HTTP method (default: "GET")
            params: Query parameters

        Returns:
            Dictionary containing status code and response text

        Raises:
            AudioControlConnectionError: If unable to connect to device
            AudioControlTimeoutError: If request times out
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:  # noqa: SIM117
                async with session.request(method, url, params=params, data=data) as response:
                    text = await response.text()
                    if (decode and
                        (response.headers.get("Content-Type", "").startswith("application/json")
                         or response.headers.get("Content-Type", "").startswith("text/javascript"))):
                        text = await response.json(content_type=None)
                    return {
                        "status": response.status,
                        "text": text,
                        "headers": dict(response.headers),
                    }
        except asyncio.TimeoutError as e:  # noqa: UP041
            raise AudioControlTimeoutError(
                f"Request to {url} timed out after {self.timeout}s"
            ) from e
        except aiohttp.ClientConnectionError as e:
            raise AudioControlConnectionError(
                f"Failed to connect to {self.host}:{self.port}"
            ) from e
        except aiohttp.ClientError as e:
            raise AudioControlConnectionError(
                f"Connection error to {self.host}:{self.port}: {e}"
            ) from e

    async def get(self, endpoint: str, params: dict[str, Any] | None = None, decode: bool = True) -> dict[str, Any]:
        """Send a GET request to the matrix device.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Dictionary containing status code and response text
        """
        return await self._make_request(endpoint, method="GET", params=params, decode=decode)

    async def post(self, endpoint: str, data: dict[str, Any] | None = None, decode: bool = True) -> dict[str, Any]:
        """Send a POST request to the matrix device.

        Args:
            endpoint: API endpoint path
            data: Form data to send in the request body

        Returns:
            Dictionary containing status code and response text
        """
        return await self._make_request(endpoint, method="POST", data=data, decode=decode)

    async def send_command(self, command: dict[str, Any], signal_processing = False, **kwargs) -> bool:
        """Send a command to the matrix device.

        Args:
            command: Command to execute
            **kwargs: Additional command parameters

        Returns:
            Boolean indicating success of HTTP request (2xx = True, else False)

        Raises:
            AudioControlCommandError: If command fails
        """

        command.update(kwargs)
        endpoint = self.OPERATION_ENDPOINT if not signal_processing else self.DETAILED_ENDPOINT
        print(f"sending command {command} to {endpoint}")
        try:
            response = await self.post(endpoint, data=command, decode=True)
            # Check if response status is successful (2xx)
            if 200 <= response["status"] < 300:
                self.cached_response = response["text"]
                return True
            self.cached_response = None
            return False
        except (AudioControlConnectionError, AudioControlTimeoutError) as e:
            raise AudioControlCommandError(f"Failed to send command '{command}': {e}") from e
