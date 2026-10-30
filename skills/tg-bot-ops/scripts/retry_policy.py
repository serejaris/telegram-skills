"""Decide what to do with a Bot API response. Standard library only, no network.

send() takes a factory because a multipart body is single-use: every attempt
must rebuild it, reopening the file. The transport is injected by the consumer.
"""
from dataclasses import dataclass
import json

DONE = 'done'
RETRY = 'retry'
MIGRATE = 'migrate'
FAIL = 'fail'
UNKNOWN = 'unknown'

DEFAULT_WAIT = 1
MAX_WAIT = 3600


@dataclass(frozen=True)
class Decision:
    action: str
    wait: int = 0
    chat_id: int | None = None
    reason: str = ''
    result: object = None


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def classify(status, body):
    """Map an HTTP status and a raw response body to a Decision.

    UNKNOWN means the request may have taken effect: report it, never resend it blindly.
    """
    if not _is_int(status):
        return Decision(UNKNOWN, reason='no HTTP status')
    try:
        data = json.loads(body)
    except (TypeError, ValueError):
        data = None
    if not isinstance(data, dict):
        return Decision(UNKNOWN, reason=f'HTTP {status} without a JSON object')
    if data.get('ok') is True and status < 300:
        return Decision(DONE, result=data.get('result'))
    params = data.get('parameters')
    params = params if isinstance(params, dict) else {}
    reason = str(data.get('description', f'HTTP {status}'))
    if status == 429:
        wait = params.get('retry_after')
        wait = wait if _is_int(wait) and wait > 0 else DEFAULT_WAIT
        return Decision(RETRY, wait=min(wait, MAX_WAIT), reason=reason)
    migrate_to = params.get('migrate_to_chat_id')
    if _is_int(migrate_to) and migrate_to != 0:
        return Decision(MIGRATE, chat_id=migrate_to, reason=reason)
    if 400 <= status < 500:
        return Decision(FAIL, reason=reason)
    return Decision(UNKNOWN, reason=reason)


class FloodGate:
    """One pause per scope. Only the clock ends a pause, a finished request cannot."""

    def __init__(self):
        self._until = {}

    def hold(self, scope, now, wait):
        self._until[scope] = max(self._until.get(scope, 0), now + wait)

    def delay(self, scope, now):
        return max(0, self._until.get(scope, 0) - now)


def send(make_request, transport, gate, scope, clock, sleep, max_attempts=3):
    """Run one Bot API call. Retries only on 429, with a fresh request each attempt.

    make_request() builds the request; transport(request) returns (status, body)
    and raises on a timeout or a dropped connection, which yields UNKNOWN.
    """
    if not _is_int(max_attempts) or max_attempts < 1:
        raise ValueError('max_attempts must be a positive integer')
    decision = Decision(UNKNOWN, reason='not attempted')
    for _ in range(max_attempts):
        pause = gate.delay(scope, clock())
        if pause:
            sleep(pause)
        try:
            status, body = transport(make_request())
        except (OSError, TimeoutError) as error:
            return Decision(UNKNOWN, reason=f'transport: {error}')
        decision = classify(status, body)
        if decision.action != RETRY:
            return decision
        gate.hold(scope, clock(), decision.wait)
    return Decision(FAIL, wait=decision.wait, reason=f'still limited: {decision.reason}')
