"""Evidence-only detection of explicit monitor size requirements.

Structured buyer mandates remain authoritative; this additional narrow parser
prevents a plain-language "72-inch monitors" request from qualifying a 24-inch
screen or a monitor stand solely on price.
"""
import re
from decimal import Decimal, InvalidOperation

_MONITOR_INTENT = re.compile(r'\b(?:monitors?|displays?|screens?)\b', re.I)
_SIZE = re.compile(r'(?<![\w.])(\d+(?:\.\d+)?)\s*(?:-?\s*(?:inch(?:es)?|in)\b|["″])', re.I)
_ACCESSORY = re.compile(
    r'\b(?:monitor|display|screen)\s+(?:stand|arm|mount|bracket|riser|holder)s?\b'
    r'|\b(?:stand|mount|bracket|riser|holder)\s+for\s+(?:a\s+)?(?:monitor|display|screen)s?\b',
    re.I,
)
_SIZE_ATTRIBUTES = frozenset({
    'screen_size', 'screen size', 'display_size', 'display size',
    'screen_diagonal', 'screen diagonal', 'display_diagonal',
    'display diagonal', 'diagonal_size', 'diagonal size',
})


def requested_monitor_size(text):
    """Return an explicitly stated diagonal, otherwise None (no guessing)."""
    text = str(text or '')
    if not _MONITOR_INTENT.search(text):
        return None
    match = _SIZE.search(text)
    if not match:
        return None
    try:
        size = Decimal(match.group(1))
    except InvalidOperation:
        return None
    return size if 10 <= size <= 130 else None


def display_size_violations(requirements_text, product):
    """Fail closed when a requested diagonal lacks exact trustworthy evidence."""
    required = requested_monitor_size(requirements_text)
    if required is None:
        return []
    title = str(getattr(product, 'title', '') or '')
    if _ACCESSORY.search(title):
        return ['A monitor accessory is not a complete display']
    structured = getattr(product, 'structured_attributes', {}) or {}
    size_sources = []
    for key, value in structured.items():
        if str(key).strip().casefold() in _SIZE_ATTRIBUTES:
            size_sources.extend(value if isinstance(value, list) else [value])
    # Product titles can supply the diagonal only if they identify a display.
    if _MONITOR_INTENT.search(title):
        size_sources.append(title)
    observed = set()
    for source in size_sources:
        for match in _SIZE.finditer(str(source or '')):
            try:
                observed.add(Decimal(match.group(1)))
            except InvalidOperation:
                pass
    label = format(required, 'f').rstrip('0').rstrip('.') if required % 1 else str(int(required))
    if not observed:
        return [f'Required {label}-inch monitor diagonal is not evidenced']
    if observed != {required}:
        return [f'Required {label}-inch monitor diagonal does not match the listing']
    return []
