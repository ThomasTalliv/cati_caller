"""Manage owned SignalWire phone numbers."""
from __future__ import annotations

import asyncio
from typing import Any

import structlog

log = structlog.get_logger(__name__)


class PhoneNumberPool:
    """Interface for listing and provisioning SignalWire numbers."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            from config.settings import get_settings
            from signalwire.rest import Client  # type: ignore[import]
            s = get_settings().signalwire
            self._client = Client(s.project_id, s.api_token, signalwire_space_url=s.space_url)
        return self._client

    async def list_numbers(self) -> list[dict[str, Any]]:
        """Return all owned phone numbers."""
        client = self._get_client()
        numbers = await asyncio.get_event_loop().run_in_executor(
            None, lambda: list(client.incoming_phone_numbers.list())
        )
        return [
            {"number": n.phone_number, "sid": n.sid, "friendly_name": n.friendly_name}
            for n in numbers
        ]

    async def provision_number(self, area_code: str = "415", country: str = "US") -> dict[str, Any]:
        """Search for and purchase an available phone number."""
        client = self._get_client()

        def _do_provision():
            available = client.available_phone_numbers(country).local.list(
                area_code=area_code, limit=1
            )
            if not available:
                raise RuntimeError(f"No numbers available in area code {area_code}")
            number = available[0].phone_number
            purchased = client.incoming_phone_numbers.create(phone_number=number)
            return {"number": purchased.phone_number, "sid": purchased.sid}

        result = await asyncio.get_event_loop().run_in_executor(None, _do_provision)
        log.info("phone_number_provisioned", **result)
        return result
