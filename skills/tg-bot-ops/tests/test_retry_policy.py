import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

SPEC = importlib.util.spec_from_file_location('retry_policy', Path(__file__).parents[1] / 'scripts/retry_policy.py')
policy = importlib.util.module_from_spec(SPEC)
sys.modules['retry_policy'] = policy
SPEC.loader.exec_module(policy)


def body(**fields):
    return json.dumps(fields)


LIMITED = (429, body(ok=False, error_code=429, description='Too Many Requests',
                     parameters={'retry_after': 7}))
SENT = (200, body(ok=True, result={'message_id': 1}))


class Clock:
    def __init__(self):
        self.now = 100
        self.slept = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


class Classify(unittest.TestCase):
    def test_success(self):
        decision = policy.classify(*SENT)
        self.assertEqual((decision.action, decision.result), (policy.DONE, {'message_id': 1}))

    def test_retry_after_is_honored(self):
        decision = policy.classify(*LIMITED)
        self.assertEqual((decision.action, decision.wait), (policy.RETRY, 7))

    def test_bad_retry_after_falls_back(self):
        for value in (None, 0, -5, '7', True, 1.5):
            params = {'retry_after': value}
            decision = policy.classify(429, body(ok=False, parameters=params))
            self.assertEqual((decision.action, decision.wait), (policy.RETRY, policy.DEFAULT_WAIT))
        self.assertEqual(policy.classify(429, body(ok=False, parameters='x')).wait, policy.DEFAULT_WAIT)

    def test_huge_retry_after_is_capped(self):
        decision = policy.classify(429, body(ok=False, parameters={'retry_after': 10 ** 9}))
        self.assertEqual(decision.wait, policy.MAX_WAIT)

    def test_group_migration(self):
        decision = policy.classify(400, body(ok=False, parameters={'migrate_to_chat_id': -1001234567890}))
        self.assertEqual((decision.action, decision.chat_id), (policy.MIGRATE, -1001234567890))

    def test_rejected_requests_fail(self):
        for status in (400, 401, 403, 404):
            self.assertEqual(policy.classify(status, body(ok=False, description='no')).action, policy.FAIL)

    def test_unclear_outcomes_are_unknown(self):
        for status, raw in ((500, body(ok=False)), (502, '<html>bad gateway</html>'), (200, 'not json'),
                            (200, '[]'), (200, 'null'), (200, ''), (200, None), (200, b'\xff'),
                            (200, body(ok=False)), (None, body(ok=True)), ('200', body(ok=True))):
            with self.subTest(status=status, raw=raw):
                self.assertEqual(policy.classify(status, raw).action, policy.UNKNOWN)


class Gate(unittest.TestCase):
    def test_finished_request_does_not_lift_the_pause(self):
        gate = policy.FloodGate()
        gate.hold('chat:1', now=100, wait=10)
        self.assertEqual(gate.delay('chat:1', now=103), 7)
        self.assertEqual(gate.delay('chat:2', now=103), 0)
        self.assertEqual(gate.delay('chat:1', now=111), 0)

    def test_shorter_wait_does_not_shrink_the_pause(self):
        gate = policy.FloodGate()
        gate.hold('bot', now=100, wait=10)
        gate.hold('bot', now=101, wait=1)
        self.assertEqual(gate.delay('bot', now=101), 9)


class Send(unittest.TestCase):
    def run_send(self, responses, make_request=None, **kwargs):
        clock = Clock()
        queue = list(responses)
        seen = []

        def transport(request):
            seen.append(request)
            item = queue.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        decision = policy.send(make_request or (lambda: 'request'), transport, policy.FloodGate(),
                               'chat:1', clock, clock.sleep, **kwargs)
        return decision, seen, clock

    def test_multipart_is_rebuilt_for_every_attempt(self):
        built = []

        def make_request():
            stream = io.BytesIO(b'file bytes')
            built.append(stream)
            return stream

        def consuming_transport(stream):
            data = stream.read()
            self.assertEqual(data, b'file bytes')
            return LIMITED if len(built) == 1 else SENT

        clock = Clock()
        decision = policy.send(make_request, consuming_transport, policy.FloodGate(),
                               'chat:1', clock, clock.sleep)
        self.assertEqual(decision.action, policy.DONE)
        self.assertEqual(len(built), 2)
        self.assertEqual(clock.slept, [7])

    def test_timeout_is_not_retried(self):
        decision, seen, _ = self.run_send([TimeoutError('read timed out'), SENT])
        self.assertEqual(decision.action, policy.UNKNOWN)
        self.assertEqual(len(seen), 1)

    def test_server_error_is_not_retried(self):
        decision, seen, _ = self.run_send([(502, 'bad gateway'), SENT])
        self.assertEqual(decision.action, policy.UNKNOWN)
        self.assertEqual(len(seen), 1)

    def test_gives_up_after_max_attempts(self):
        decision, seen, clock = self.run_send([LIMITED, LIMITED], max_attempts=2)
        self.assertEqual(decision.action, policy.FAIL)
        self.assertEqual(len(seen), 2)
        self.assertEqual(clock.slept, [7])

    def test_bad_max_attempts(self):
        for value in (0, -1, '3', True):
            with self.assertRaises(ValueError):
                self.run_send([SENT], max_attempts=value)


if __name__ == '__main__':
    unittest.main()
