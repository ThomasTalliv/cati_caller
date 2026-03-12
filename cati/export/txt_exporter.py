"""Plain text export — transcript + structured responses."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from cati.export.base import Exporter, ExportResult


class TXTExporter(Exporter):
    """Export survey data as plain text files."""

    def __init__(self, export_dir: str) -> None:
        self._export_dir = export_dir

    async def export(
        self,
        survey_id: uuid.UUID,
        *,
        call_ids: list[uuid.UUID] | None = None,
    ) -> ExportResult:
        from cati.db.session import get_session_factory
        from cati.db.repositories.response_repo import ResponseRepository
        from cati.db.repositories.call_repo import CallRepository

        factory = get_session_factory()
        async with factory() as session:
            call_repo = CallRepository(session)
            resp_repo = ResponseRepository(session)

            calls = await call_repo.list(survey_id=survey_id, status="completed", limit=10000)
            if call_ids:
                calls = [c for c in calls if c.id in set(call_ids)]

        lines: list[str] = [
            f"CATI Survey Export",
            f"Survey ID: {survey_id}",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Total calls: {len(calls)}",
            "=" * 60,
        ]

        async with factory() as session:
            resp_repo = ResponseRepository(session)
            for call in calls:
                lines.append(f"\nCALL: {call.id}")
                lines.append(f"Phone: {call.phone_number}")
                lines.append(f"Status: {call.status}")
                lines.append(f"Duration: {call.duration_s or 0}s")
                lines.append("-" * 40)
                lines.append("RESPONSES:")
                responses = await resp_repo.list_for_call(call.id)
                for r in responses:
                    refused = " [REFUSED]" if r.is_refused else ""
                    lines.append(f"  {r.question_key}: {r.parsed_value}{refused}")
                lines.append("\nTRANSCRIPT:")
                turns = await resp_repo.list_transcript(call.id)
                for t in turns:
                    lines.append(f"  [{t.speaker.upper()}] {t.text}")

        content = "\n".join(lines)
        os.makedirs(self._export_dir, exist_ok=True)
        filename = f"survey_{survey_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"
        path = os.path.join(self._export_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return ExportResult(
            export_id=uuid.uuid4(),
            format="txt",
            file_path=path,
            call_count=len(calls),
        )

    @property
    def format_name(self) -> str:
        return "txt"
