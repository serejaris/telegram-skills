from dataclasses import dataclass
import json
import time

DONE = 'done'
RETRY = 'retry'
MIGRATE = 'migrate'
FAIL = 'fail'
UNKNOWN = 'unknown'

DEFAULT_WAIT = 1
MAX_INLINE_WAIT = 60


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
        return Decision(RETRY, wait=wait, reason=reason)
    migrate_to = params.get('migrate_to_chat_id')
    if _is_int(migrate_to) and migrate_to != 0:
        return Decision(MIGRATE, chat_id=migrate_to, reason=reason)
    if 400 <= status < 500:
        return Decision(FAIL, reason=reason)
    return Decision(UNKNOWN, reason=reason)


class FloodGate:
    def __init__(self, clock=time.monotonic, sleep=time.sleep):
        self._clock = clock
        self._sleep = sleep
        self._until = {}

    def hold(self, scope, wait):
        self._until[scope] = max(self._until.get(scope, 0), self._clock() + wait)

    def delay(self, scope):
        return max(0, self._until.get(scope, 0) - self._clock())

    def sleep(self, seconds):
        self._sleep(seconds)


def send(make_request, transport, gate, scope, max_attempts=3, max_inline_wait=MAX_INLINE_WAIT):
    if not _is_int(max_attempts) or max_attempts < 1:
        raise ValueError('max_attempts must be a positive integer')
    decision = Decision(UNKNOWN, reason='not attempted')
    for _ in range(max_attempts):
        pause = gate.delay(scope)
        if pause > max_inline_wait:
            return Decision(FAIL, wait=pause, reason=f'pause too long: {decision.reason}')
        if pause:
            gate.sleep(pause)
        request = make_request()
        try:
            status, body = transport(request)
        except Exception as error:
            return Decision(UNKNOWN, reason=f'transport: {error}')
        decision = classify(status, body)
        if decision.action != RETRY:
            return decision
        gate.hold(scope, decision.wait)
    return Decision(FAIL, wait=decision.wait, reason=f'still limited: {decision.reason}')
