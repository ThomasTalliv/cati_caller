"""Export factory."""
from __future__ import annotations

from cati.export.base import Exporter


def get_exporter(format: str) -> Exporter:
    from config.settings import get_settings
    settings = get_settings()
    export_dir = settings.export.export_dir

    if format == "txt":
        from cati.export.txt_exporter import TXTExporter
        return TXTExporter(export_dir=export_dir)
    elif format in ("excel", "xlsx"):
        from cati.export.excel_exporter import ExcelExporter
        return ExcelExporter(export_dir=export_dir)
    elif format in ("word", "docx"):
        from cati.export.word_exporter import WordExporter
        return WordExporter(export_dir=export_dir)
    elif format == "gsheets":
        from cati.export.gsheets_exporter import GoogleSheetsExporter
        return GoogleSheetsExporter(
            service_account_json=settings.export.google_service_account_json,
            folder_id=settings.export.google_sheets_folder_id,
        )
    else:
        raise ValueError(f"Unknown export format: {format!r}")
