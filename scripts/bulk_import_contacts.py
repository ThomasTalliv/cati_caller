#!/usr/bin/env python3
"""Bulk-import contacts from a CSV file.

CSV format (with header row):
    phone_number,name,do_not_call,metadata_json

Usage:
    python scripts/bulk_import_contacts.py contacts.csv [--dnc-column do_not_call]
"""
import asyncio
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cati.db.session import get_session_factory
from cati.survey.models import Contact
from cati.utils.phone import is_valid_e164, normalize_e164


async def import_contacts(csv_path: str) -> None:
    path = Path(csv_path)
    if not path.exists():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    factory = get_session_factory()
    imported = 0
    skipped = 0
    dnc_skipped = 0

    async with factory() as session:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_phone = row.get("phone_number", "").strip()
                if not raw_phone:
                    skipped += 1
                    continue

                e164 = normalize_e164(raw_phone)
                if not is_valid_e164(e164):
                    print(f"  SKIP invalid number: {raw_phone!r}")
                    skipped += 1
                    continue

                dnc_raw = row.get("do_not_call", "false").strip().lower()
                do_not_call = dnc_raw in ("true", "1", "yes")

                if do_not_call:
                    dnc_skipped += 1

                metadata_raw = row.get("metadata_json", "{}").strip()
                try:
                    metadata = json.loads(metadata_raw) if metadata_raw else {}
                except json.JSONDecodeError:
                    metadata = {}

                contact = Contact(
                    phone_number=e164,
                    name=row.get("name") or None,
                    do_not_call=do_not_call,
                    metadata_=metadata,
                )
                session.add(contact)
                imported += 1

        await session.commit()

    print(f"Import complete: {imported} imported, {skipped} skipped, {dnc_skipped} DNC.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <contacts.csv>")
        sys.exit(1)
    asyncio.run(import_contacts(sys.argv[1]))
