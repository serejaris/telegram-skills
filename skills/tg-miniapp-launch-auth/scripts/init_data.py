"""Check Telegram Mini App initData. Pure functions, standard library, no network."""

import base64
import hashlib
import hmac
import re
import time
from urllib.parse import parse_qsl

DEFAULT_MAX_AGE = 86400
_HASH = re.compile(r'[0-9a-fA-F]{64}')
_SIGNATURE = re.compile(r'[A-Za-z0-9_-]+={0,2}')


class InitDataError(ValueError):
    """initData is malformed, unsigned, forged or expired. `code` names the reason."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def parse_init_data(raw):
    """Decode the raw query string into a dict of strings. Rejects repeated keys."""
    if not isinstance(raw, str) or not raw:
        raise InitDataError('malformed')
    try:
        pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True,
                          encoding='utf-8', errors='strict')
    except (ValueError, UnicodeError) as error:
        raise InitDataError('malformed') from error
    fields = dict(pairs)
    if len(fields) != len(pairs) or '' in fields:
        raise InitDataError('malformed')
    return fields


def _check_string(fields, excluded):
    return '\n'.join(f'{key}={fields[key]}' for key in sorted(fields) if key not in excluded)


def data_check_string(fields):
    """Bot-token scheme: every field except `hash`. `signature` stays in the string."""
    return _check_string(fields, {'hash'})


def compute_hash(fields, bot_token):
    """Hex HMAC-SHA-256 of the data-check-string under the WebAppData-derived key."""
    if not isinstance(bot_token, str) or not bot_token:
        raise InitDataError('malformed')
    secret_key = hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()
    return hmac.new(secret_key, data_check_string(fields).encode(), hashlib.sha256).hexdigest()


def validate(raw, bot_token, max_age=DEFAULT_MAX_AGE, now=None):
    """Return decoded fields of valid initData, else raise InitDataError.

    `max_age` is seconds since `auth_date`; 0 skips the age check. `now` is Unix time,
    defaulting to the system clock. JSON fields such as `user` stay strings for the caller.
    """
    fields = parse_init_data(raw)
    received = fields.get('hash')
    if received is None:
        raise InitDataError('missing_hash')
    if not _HASH.fullmatch(received):
        raise InitDataError('malformed')
    if not hmac.compare_digest(compute_hash(fields, bot_token), received.lower()):
        raise InitDataError('invalid_hash')
    auth_date = fields.get('auth_date', '')
    if not (auth_date.isascii() and auth_date.isdecimal()):
        raise InitDataError('invalid_auth_date')
    if isinstance(max_age, bool) or not isinstance(max_age, int) or max_age < 0:
        raise InitDataError('malformed')
    current = time.time() if now is None else now
    if max_age and current - int(auth_date) > max_age:
        raise InitDataError('expired')
    return fields


def third_party_payload(raw, bot_id):
    """Return (message, signature) to pass to an Ed25519 verifier with Telegram's public key.

    The standard library has no Ed25519, so verification stays with the caller. Telegram
    sends the signature as base64url without padding; this function restores it.
    """
    if isinstance(bot_id, bool) or not isinstance(bot_id, int) or bot_id <= 0:
        raise InitDataError('malformed')
    fields = parse_init_data(raw)
    signature = fields.get('signature')
    if signature is None:
        raise InitDataError('missing_signature')
    if not _SIGNATURE.fullmatch(signature):
        raise InitDataError('malformed')
    stripped = signature.rstrip('=')
    try:
        decoded = base64.urlsafe_b64decode(stripped + '=' * (-len(stripped) % 4))
    except ValueError as error:
        raise InitDataError('malformed') from error
    if len(decoded) != 64:
        raise InitDataError('malformed')
    message = f'{bot_id}:WebAppData\n' + _check_string(fields, {'hash', 'signature'})
    return message.encode(), decoded
