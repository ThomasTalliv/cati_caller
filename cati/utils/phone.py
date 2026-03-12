"""Phone number utilities."""
import re


def normalize_e164(phone: str) -> str:
    """Normalize a phone number to E.164 format.

    Accepts formats like +1 555 123 4567, (555) 123-4567, +15551234567.
    Assumes US numbers if no country code prefix is present.
    """
    digits = re.sub(r"[^\d+]", "", phone)
    if digits.startswith("+"):
        return digits
    # Strip leading 0 for international numbers without +
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return f"+{digits}"


def is_valid_e164(phone: str) -> bool:
    return bool(re.match(r"^\+[1-9]\d{7,14}$", phone))
