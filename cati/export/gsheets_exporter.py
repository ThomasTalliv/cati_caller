"""Google Sheets export using gspread + service account."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from cati.export.base import Exporter, ExportResult


class GoogleSheetsExporter(Exporter):
    """Export survey data to a Google Sheets spreadsheet."""

    def __init__(self, service_account_json: str, folder_id: str = "") -> None:
        self._sa_json = service_account_json
        self._folder_id = folder_id
        self._gc = None

    def _get_client(self):
        if self._gc is None:
            try:
                import gspread
                from google.oauth2.service_account import Credentials
            except ImportError as exc:
                raise RuntimeError(
                    "gspread and google-auth not installed. Run: pip install gspread google-auth"
                ) from exc

            scopes = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(self._sa_json, scopes=scopes)
            self._gc = gspread.authorize(creds)
        return self._gc

    async def export(
        self,
        survey_id: uuid.UUID,
        *,
        call_ids: list[uuid.UUID] | None = None,
    ) -> ExportResult:
        import asyncio

        return await asyncio.get_event_loop().run_in_executor(
            None, self._export_sync, survey_id, call_ids
        )

    def _export_sync(
        self, survey_id: uuid.UUID, call_ids: list[uuid.UUID] | None
    ) -> ExportResult:
        import asyncio

        # Run DB queries in a new event loop (we're in a thread)
        loop = asyncio.new_event_loop()
        calls, questions, all_responses, all_transcripts = loop.run_until_complete(
            self._fetch_data(survey_id, call_ids)
        )
        loop.close()

        gc = self._get_client()
        title = f"CATI Export - {survey_id} - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        sh = gc.create(title)
        if self._folder_id:
            try:
                gc.move_file(sh.id, self._folder_id)
            except Exception:
                pass

        question_keys = [q["question_key"] for q in questions]

        # ── Sheet 1: Responses ────────────────────────────────────────────────
        ws_responses = sh.get_worksheet(0)
        ws_responses.update_title("Responses")
        header = ["Call ID", "Phone", "Duration (s)", "Date"] + question_keys
        rows = [header]
        resp_by_call: dict[str, dict] = {}
        for r in all_responses:
            resp_by_call.setdefault(str(r["call_id"]), {})[r["question_key"]] = r["parsed_value"]
        for call in calls:
            cid = str(call["id"])
            row = [
                cid,
                call["phone_number"],
                call["duration_s"] or 0,
                call["ended_at"] or "",
            ] + [resp_by_call.get(cid, {}).get(k, "") for k in question_keys]
            rows.append(row)
        ws_responses.update(rows)

        # ── Sheet 2: Transcripts ──────────────────────────────────────────────
        ws_transcripts = sh.add_worksheet(title="Transcripts", rows=5000, cols=4)
        t_rows = [["Call ID", "Speaker", "Text", "Timestamp"]]
        for t in all_transcripts:
            t_rows.append([str(t["call_id"]), t["speaker"], t["text"], t["created_at"]])
        ws_transcripts.update(t_rows)

        return ExportResult(
            export_id=uuid.uuid4(),
            format="gsheets",
            external_url=sh.url,
            call_count=len(calls),
        )

    async def _fetch_data(self, survey_id, call_ids):
        from cati.db.session import get_session_factory
        from cati.db.repositories.call_repo import CallRepository
        from cati.db.repositories.response_repo import ResponseRepository
        from cati.db.repositories.survey_repo import SurveyRepository

        factory = get_session_factory()
        async with factory() as session:
            survey_repo = SurveyRepository(session)
            call_repo = CallRepository(session)
            resp_repo = ResponseRepository(session)

            survey = await survey_repo.get(survey_id)
            questions = [
                {"question_key": q.question_key} for q in (survey.questions if survey else [])
            ]
            calls_orm = await call_repo.list(survey_id=survey_id, status="completed", limit=10000)
            if call_ids:
                calls_orm = [c for c in calls_orm if c.id in set(call_ids)]

            calls = [
                {
                    "id": c.id,
                    "phone_number": c.phone_number,
                    "duration_s": c.duration_s,
                    "ended_at": c.ended_at.isoformat() if c.ended_at else "",
                }
                for c in calls_orm
            ]

            all_responses = []
            all_transcripts = []
            for c in calls_orm:
                for r in await resp_repo.list_for_call(c.id):
                    all_responses.append({
                        "call_id": c.id,
                        "question_key": r.question_key,
                        "parsed_value": str(r.parsed_value or ""),
                    })
                for t in await resp_repo.list_transcript(c.id):
                    all_transcripts.append({
                        "call_id": c.id,
                        "speaker": t.speaker,
                        "text": t.text,
                        "created_at": t.created_at.isoformat(),
                    })

        return calls, questions, all_responses, all_transcripts

    @property
    def format_name(self) -> str:
        return "gsheets"
