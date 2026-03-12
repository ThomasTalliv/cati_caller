"""Abstract Exporter interface and ExportResult."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExportResult:
    export_id: uuid.UUID
    format: str
    file_path: str | None = None     # local filesystem path (Word, Excel, TXT)
    external_url: str | None = None  # Google Sheets URL
    call_count: int = 0


class Exporter(ABC):
    """Generate a survey export in a specific format."""

    @abstractmethod
    async def export(
        self,
        survey_id: uuid.UUID,
        *,
        call_ids: list[uuid.UUID] | None = None,
    ) -> ExportResult:
        """Generate the export.

        Args:
            survey_id: Survey to export.
            call_ids: Specific calls to include. None means all completed calls.

        Returns:
            ExportResult with file_path or external_url populated.
        """

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Export format identifier (e.g. 'word', 'excel', 'txt', 'gsheets')."""
