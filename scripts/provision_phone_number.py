#!/usr/bin/env python3
"""Provision a phone number via the SignalWire API and write it to .env.

Usage:
    python scripts/provision_phone_number.py --area-code 415
    python scripts/provision_phone_number.py --country US --area-code 212
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision a SignalWire phone number")
    parser.add_argument("--area-code", type=str, default="", help="US area code to search in")
    parser.add_argument("--country", type=str, default="US", help="ISO country code")
    parser.add_argument(
        "--update-env",
        action="store_true",
        default=True,
        help="Write the provisioned number to .env as SIGNALWIRE__OUTBOUND_NUMBER",
    )
    args = parser.parse_args()

    try:
        from config.settings import get_settings
        settings = get_settings()
        sw = settings.signalwire
    except Exception as exc:
        print(f"Failed to load settings: {exc}", file=sys.stderr)
        sys.exit(1)

    if not sw.project_id or not sw.api_token or not sw.space_url:
        print("Error: SIGNALWIRE__PROJECT_ID, SIGNALWIRE__API_TOKEN, and SIGNALWIRE__SPACE_URL must be set.", file=sys.stderr)
        sys.exit(1)

    try:
        from signalwire.rest import Client  # type: ignore[import]
    except ImportError:
        print("signalwire package not installed. Run: pip install signalwire-agents", file=sys.stderr)
        sys.exit(1)

    client = Client(sw.project_id, sw.api_token, signalwire_space_url=sw.space_url)

    # Search for available numbers
    search_kwargs: dict = {"limit": 10}
    if args.area_code:
        search_kwargs["area_code"] = args.area_code

    print(f"Searching for available {args.country} numbers (area code: {args.area_code or 'any'})...")
    available = client.available_phone_numbers(args.country).local.list(**search_kwargs)

    if not available:
        print("No numbers found matching your criteria.", file=sys.stderr)
        sys.exit(1)

    number = available[0]
    print(f"Found: {number.phone_number} — {number.friendly_name}")

    # Purchase the number
    purchased = client.incoming_phone_numbers.create(phone_number=number.phone_number)
    e164 = purchased.phone_number
    print(f"Provisioned: {e164}")

    if args.update_env:
        env_path = Path(".env")
        if env_path.exists():
            lines = env_path.read_text().splitlines()
            updated = False
            new_lines = []
            for line in lines:
                if line.startswith("SIGNALWIRE__OUTBOUND_NUMBER="):
                    new_lines.append(f"SIGNALWIRE__OUTBOUND_NUMBER={e164}")
                    updated = True
                else:
                    new_lines.append(line)
            if not updated:
                new_lines.append(f"SIGNALWIRE__OUTBOUND_NUMBER={e164}")
            env_path.write_text("\n".join(new_lines) + "\n")
            print(f"Updated .env: SIGNALWIRE__OUTBOUND_NUMBER={e164}")
        else:
            print(f"\nAdd to your .env:\nSIGNALWIRE__OUTBOUND_NUMBER={e164}")


if __name__ == "__main__":
    main()
