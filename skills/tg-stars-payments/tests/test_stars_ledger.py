import importlib.util
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import unittest

SCRIPT = Path(__file__).parents[1] / 'scripts/stars_ledger.py'
SPEC = importlib.util.spec_from_file_location('stars_ledger', SCRIPT)
ledger = importlib.util.module_from_spec(SPEC)
sys.modules['stars_ledger'] = ledger
SPEC.loader.exec_module(ledger)

DAY = 86400
PERIOD = 30 * DAY
START = 1_800_000_000
NOW = 1_900_000_000


def paid(update_id=1, charge='stx-1', field='message', **extra):
    event = {'currency': 'XTR', 'total_amount': 5, 'invoice_payload': 'sku-1',
             'telegram_payment_charge_id': charge, 'provider_payment_charge_id': '', **extra}
    return {'update_id': update_id,
            field: {'message_id': 9, 'from': {'id': 42}, 'chat': {'id': 42}, 'successful_payment': event}}


def refunded(charge='stx-1', field='message'):
    event = {'currency': 'XTR', 'total_amount': 5, 'invoice_payload': 'sku-1',
             'telegram_payment_charge_id': charge}
    return {'update_id': 7, field: {'from': {'id': 42}, 'refunded_payment': event}}


def incoming(charge='stx-1', date=START, period=None, **partner):
    source = {'type': 'user', 'transaction_type': 'invoice_payment', 'user': {'id': 42},
              'invoice_payload': 'sku-1', **partner}
    if period is not None:
        source['subscription_period'] = period
    return {'id': charge, 'amount': 5, 'date': date, 'source': source}


def renewal(charge='sub', expires_at=START + PERIOD):
    return ledger.parse_payment(paid(charge=charge, subscription_expiration_date=expires_at,
                                     is_recurring=True))


def states(conn):
    rows = conn.execute('SELECT subscription_expires_at, state FROM star_payments '
                        'ORDER BY subscription_expires_at')
    return rows.fetchall()


class Parsing(unittest.TestCase):
    def test_reads_payment_fields(self):
        payment = ledger.parse_payment(paid())
        self.assertEqual(payment, ledger.Payment('stx-1', 0, 42, 5, 'sku-1'))
        self.assertEqual(payment.key, ('stx-1', 0))

    def test_every_message_container_is_read(self):
        for field in ledger.MESSAGE_FIELDS:
            with self.subTest(field):
                self.assertEqual(ledger.parse_payment(paid(field=field)).charge_id, 'stx-1')
                self.assertEqual(ledger.parse_refund_charge_id(refunded(field=field)), 'stx-1')

    def test_payment_without_sender_raises_in_a_channel_post(self):
        update = paid(field='channel_post')
        del update['channel_post']['from']
        with self.assertRaises(ValueError):
            ledger.parse_payment(update)

    def test_other_updates_are_not_payments(self):
        for update in ({'update_id': 1}, {'update_id': 1, 'message': {'text': 'hi'}},
                       {'update_id': 1, 'pre_checkout_query': {'id': 'q'}}, {'message': None}):
            self.assertIsNone(ledger.parse_payment(update))
            self.assertIsNone(ledger.parse_refund_charge_id(update))

    def test_garbage_updates_raise(self):
        for update in (None, [], 'x', 1):
            with self.assertRaises(ValueError):
                ledger.parse_payment(update)

    def test_broken_payments_raise(self):
        cases = [
            {'telegram_payment_charge_id': ''},
            {'telegram_payment_charge_id': None},
            {'telegram_payment_charge_id': 7},
            {'currency': 'USD'},
            {'total_amount': 0},
            {'total_amount': -1},
            {'total_amount': '5'},
            {'total_amount': True},
            {'total_amount': 1.5},
            {'invoice_payload': None},
            {'subscription_expiration_date': 'soon'},
            {'subscription_expiration_date': -1},
        ]
        for fields in cases:
            with self.subTest(fields), self.assertRaises(ValueError):
                ledger.parse_payment(paid(**fields))

    def test_event_and_sender_shape(self):
        update = paid()
        update['message']['successful_payment'] = 'paid'
        with self.assertRaises(ValueError):
            ledger.parse_payment(update)
        for sender in (None, {}, {'id': 0}, {'id': True}, {'id': '42'}, 'user'):
            update = paid()
            update['message']['from'] = sender
            with self.subTest(sender), self.assertRaises(ValueError):
                ledger.parse_payment(update)

    def test_broken_refund_raises(self):
        update = refunded()
        del update['message']['refunded_payment']['telegram_payment_charge_id']
        with self.assertRaises(ValueError):
            ledger.parse_refund_charge_id(update)


class FileLedger(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = str(Path(folder.name) / 'ledger.sqlite3')
        self.conn = self.open()

    def open(self):
        conn = ledger.connect(self.path)
        self.addCleanup(conn.close)
        return conn


class Connecting(FileLedger):
    def test_path_is_required(self):
        with self.assertRaises(TypeError):
            ledger.connect()
        for path in ('', ':memory:', None, 7):
            with self.subTest(path), self.assertRaises(ValueError):
                ledger.connect(path)

    def test_recorded_payment_survives_reopening(self):
        payment = ledger.parse_payment(paid())
        ledger.record_payment(self.conn, payment)
        self.conn.close()
        self.assertEqual(ledger.pending(self.open(), NOW), [payment])

    def test_uncommitted_payment_is_gone_after_reopening(self):
        self.conn.execute('BEGIN IMMEDIATE')
        ledger.record_payment(self.conn, ledger.parse_payment(paid()))
        self.conn.close()
        self.assertEqual(ledger.pending(self.open(), NOW), [])

    def test_duplicate_leaves_no_open_transaction(self):
        payment = ledger.parse_payment(paid())
        ledger.record_payment(self.conn, payment)
        self.assertFalse(ledger.record_payment(self.conn, payment))
        self.assertFalse(self.conn.in_transaction)


class Crediting(FileLedger):
    def deliver(self, payment, now=NOW):
        self.assertTrue(ledger.claim(self.conn, payment, now))
        self.assertTrue(ledger.mark_delivered(self.conn, payment))

    def test_duplicate_with_new_update_id_delivers_once(self):
        first, second = paid(update_id=100), paid(update_id=200)
        self.assertTrue(ledger.record_payment(self.conn, ledger.parse_payment(first)))
        self.assertFalse(ledger.record_payment(self.conn, ledger.parse_payment(second)))
        due = ledger.pending(self.conn, NOW)
        self.assertEqual(len(due), 1)
        self.deliver(due[0])
        self.assertFalse(ledger.claim(self.conn, due[0], NOW))
        self.assertFalse(ledger.mark_delivered(self.conn, due[0]))
        self.assertEqual(ledger.pending(self.conn, NOW), [])

    def test_same_update_id_with_new_charge_is_a_new_payment(self):
        self.assertTrue(ledger.record_payment(self.conn, ledger.parse_payment(paid(update_id=5, charge='a'))))
        self.assertTrue(ledger.record_payment(self.conn, ledger.parse_payment(paid(update_id=5, charge='b'))))
        self.assertEqual(len(ledger.pending(self.conn, NOW)), 2)

    def test_renewal_counts_whether_or_not_the_charge_id_repeats(self):
        for number, charges in enumerate((('sub', 'sub'), ('sub-1', 'sub-2'))):
            conn = ledger.connect(f'{self.path}.{number}')
            self.addCleanup(conn.close)
            ledger.record_payment(conn, renewal(charges[0], 1000))
            self.assertTrue(ledger.record_payment(conn, renewal(charges[1], 2000)))
            self.assertFalse(ledger.record_payment(conn, renewal(charges[1], 2000)))
            self.assertEqual(len(ledger.pending(conn, NOW)), 2)

    def test_mark_delivered_needs_a_claim(self):
        payment = ledger.parse_payment(paid())
        ledger.record_payment(self.conn, payment)
        self.assertFalse(ledger.mark_delivered(self.conn, payment))

    def test_released_claim_can_be_taken_again(self):
        payment = ledger.parse_payment(paid())
        ledger.record_payment(self.conn, payment)
        self.assertTrue(ledger.claim(self.conn, payment, NOW))
        self.assertTrue(ledger.release(self.conn, payment))
        self.assertFalse(ledger.release(self.conn, payment))
        self.assertTrue(ledger.claim(self.conn, payment, NOW))

    def test_live_claim_blocks_a_second_connection(self):
        payment = ledger.parse_payment(paid())
        ledger.record_payment(self.conn, payment)
        second = self.open()
        self.assertTrue(ledger.claim(self.conn, payment, NOW))
        self.assertFalse(ledger.claim(second, payment, NOW))
        self.assertEqual(ledger.pending(second, NOW), [])

    def test_expired_lease_returns_the_payment(self):
        payment = ledger.parse_payment(paid())
        ledger.record_payment(self.conn, payment)
        ledger.claim(self.conn, payment, NOW, lease=60)
        self.assertEqual(ledger.pending(self.conn, NOW + 59), [])
        self.assertEqual(ledger.pending(self.conn, NOW + 60), [payment])
        self.assertTrue(ledger.claim(self.conn, payment, NOW + 60))

    def test_balance_and_mark_share_one_transaction(self):
        self.conn.execute('CREATE TABLE balance (user_id INTEGER, stars INTEGER)')
        payment = ledger.parse_payment(paid())
        ledger.record_payment(self.conn, payment)
        ledger.claim(self.conn, payment, NOW)
        with self.assertRaises(RuntimeError), ledger.transaction(self.conn):
            self.conn.execute('INSERT INTO balance VALUES (?, ?)', (payment.user_id, payment.amount))
            ledger.mark_delivered(self.conn, payment)
            raise RuntimeError('crash before commit')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM balance').fetchone(), (0,))
        self.assertEqual(states(self.conn), [(0, ledger.CLAIMED)])

    def test_refund_blocks_delivery_and_is_idempotent(self):
        payment = ledger.parse_payment(paid())
        ledger.record_payment(self.conn, payment)
        charge = ledger.parse_refund_charge_id(refunded())
        self.assertTrue(ledger.record_refund(self.conn, charge))
        self.assertFalse(ledger.record_refund(self.conn, charge))
        self.assertEqual(ledger.pending(self.conn, NOW), [])
        self.assertFalse(ledger.claim(self.conn, payment, NOW))

    def test_refund_during_delivery_wins_over_the_mark(self):
        payment = ledger.parse_payment(paid())
        ledger.record_payment(self.conn, payment)
        ledger.claim(self.conn, payment, NOW)
        ledger.record_refund(self.conn, payment.charge_id)
        self.assertFalse(ledger.mark_delivered(self.conn, payment))
        self.assertEqual(states(self.conn), [(0, ledger.REFUNDED)])

    def test_refund_touches_newest_period_only(self):
        for expires_at in (1000, 2000):
            ledger.record_payment(self.conn, renewal('sub', expires_at))
        ledger.record_refund(self.conn, 'sub')
        due = ledger.pending(self.conn, NOW)
        self.assertEqual([payment.subscription_expires_at for payment in due], [1000])

    def test_refund_before_payment_keeps_it_from_delivery(self):
        self.assertTrue(ledger.record_refund(self.conn, 'stx-1'))
        self.assertFalse(ledger.record_refund(self.conn, 'stx-1'))
        ledger.record_payment(self.conn, ledger.parse_payment(paid()))
        self.assertEqual(ledger.pending(self.conn, NOW), [])
        self.assertEqual(states(self.conn), [(0, ledger.REFUNDED)])

    def test_replayed_refund_spares_the_next_period(self):
        ledger.record_payment(self.conn, renewal('sub', 1000))
        ledger.record_refund(self.conn, 'sub')
        self.assertFalse(ledger.record_refund(self.conn, 'sub'))
        ledger.record_payment(self.conn, renewal('sub', 2000))
        self.assertEqual(len(ledger.pending(self.conn, NOW)), 1)


class ParallelWebhooks(FileLedger):
    HANDLERS = 8
    PAYMENTS = 20

    def test_handlers_deliver_each_payment_once(self):
        for number in range(self.PAYMENTS):
            ledger.record_payment(self.conn, ledger.parse_payment(paid(charge=f'stx-{number}')))
        start = threading.Barrier(self.HANDLERS)
        counted = threading.Lock()
        deliveries = []
        errors = []

        def handler():
            conn = ledger.connect(self.path)
            try:
                start.wait()
                for payment in ledger.pending(conn, NOW):
                    if ledger.claim(conn, payment, NOW):
                        with counted:
                            deliveries.append(payment.key)
                        ledger.mark_delivered(conn, payment)
            except Exception as error:
                errors.append(error)
            finally:
                conn.close()

        threads = [threading.Thread(target=handler) for _ in range(self.HANDLERS)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(deliveries), self.PAYMENTS)
        self.assertEqual(len(set(deliveries)), self.PAYMENTS)
        self.assertEqual(ledger.pending(self.conn, NOW), [])

    def test_parallel_copies_of_one_update_record_one_row(self):
        results = []
        start = threading.Barrier(self.HANDLERS)

        def handler():
            conn = ledger.connect(self.path)
            start.wait()
            results.append(ledger.record_payment(conn, ledger.parse_payment(paid())))
            conn.close()

        threads = [threading.Thread(target=handler) for _ in range(self.HANDLERS)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sorted(results), [False] * (self.HANDLERS - 1) + [True])


CRASH = """
import importlib.util, os, signal, sys
spec = importlib.util.spec_from_file_location('stars_ledger', sys.argv[1])
ledger = importlib.util.module_from_spec(spec)
sys.modules['stars_ledger'] = ledger
spec.loader.exec_module(ledger)
conn = ledger.connect(sys.argv[2])
payment = ledger.Payment('stx-1', 0, 42, 5, 'sku-1')
if sys.argv[3] == 'inside-transaction':
    conn.execute('BEGIN IMMEDIATE')
    ledger.record_payment(conn, payment)
else:
    ledger.record_payment(conn, payment)
    if sys.argv[3] == 'during-delivery':
        ledger.claim(conn, payment, int(sys.argv[4]), lease=60)
os.kill(os.getpid(), signal.SIGKILL)
"""


class ProcessCrash(FileLedger):
    def crash(self, moment):
        self.conn.close()
        done = subprocess.run([sys.executable, '-c', CRASH, str(SCRIPT), self.path, moment, str(NOW)],
                              check=False)
        self.assertEqual(done.returncode, -signal.SIGKILL)
        return self.open()

    def test_kill_inside_transaction_leaves_no_row(self):
        conn = self.crash('inside-transaction')
        self.assertEqual(ledger.pending(conn, NOW), [])
        self.assertTrue(ledger.record_payment(conn, ledger.Payment('stx-1', 0, 42, 5, 'sku-1')))

    def test_kill_before_claim_leaves_payment_pending(self):
        conn = self.crash('after-record')
        self.assertEqual([p.charge_id for p in ledger.pending(conn, NOW)], ['stx-1'])

    def test_kill_during_delivery_returns_payment_after_the_lease(self):
        conn = self.crash('during-delivery')
        self.assertEqual(ledger.pending(conn, NOW), [])
        due = ledger.pending(conn, NOW + 60)
        self.assertEqual([p.charge_id for p in due], ['stx-1'])
        self.assertTrue(ledger.claim(conn, due[0], NOW + 60))


class Reconciling(FileLedger):
    def test_recovers_a_lost_one_time_payment_once(self):
        self.assertTrue(ledger.reconcile_transaction(self.conn, incoming()))
        self.assertFalse(ledger.reconcile_transaction(self.conn, incoming()))
        self.assertFalse(ledger.record_payment(self.conn, ledger.parse_payment(paid())))
        self.assertEqual(ledger.pending(self.conn, NOW), [ledger.Payment('stx-1', 0, 42, 5, 'sku-1')])

    def test_transaction_matches_a_recorded_period(self):
        ledger.record_payment(self.conn, renewal(expires_at=START + PERIOD))
        late = START + 3600
        self.assertFalse(ledger.reconcile_transaction(self.conn, incoming('sub', late, PERIOD)))
        self.assertEqual(len(ledger.pending(self.conn, NOW)), 1)

    def test_recovered_renewal_delivers_once_when_the_update_arrives_late(self):
        renewed_at = START + 3600
        true_expiry = START + PERIOD
        self.assertTrue(ledger.reconcile_transaction(self.conn, incoming('sub', renewed_at, PERIOD)))
        due = ledger.pending(self.conn, NOW)
        self.assertEqual(due[0].subscription_expires_at, renewed_at + PERIOD)
        self.assertTrue(ledger.claim(self.conn, due[0], NOW))
        self.assertTrue(ledger.mark_delivered(self.conn, due[0]))
        self.assertFalse(ledger.record_payment(self.conn, renewal(expires_at=true_expiry)))
        self.assertEqual(ledger.pending(self.conn, NOW), [])
        self.assertEqual(states(self.conn), [(true_expiry, ledger.DELIVERED)])

    def test_late_update_during_delivery_keeps_the_claimed_key(self):
        renewed_at = START + 3600
        ledger.reconcile_transaction(self.conn, incoming('sub', renewed_at, PERIOD))
        due = ledger.pending(self.conn, NOW)[0]
        self.assertTrue(ledger.claim(self.conn, due, NOW))
        self.assertFalse(ledger.record_payment(self.conn, renewal(expires_at=START + PERIOD)))
        self.assertTrue(ledger.mark_delivered(self.conn, due))
        self.assertEqual(ledger.pending(self.conn, NOW + ledger.DEFAULT_LEASE), [])
        self.assertEqual(states(self.conn), [(due.subscription_expires_at, ledger.DELIVERED)])

    def test_next_period_on_the_same_charge_stays_a_new_payment(self):
        ledger.record_payment(self.conn, renewal(expires_at=START + PERIOD))
        next_date = START + PERIOD
        self.assertTrue(ledger.reconcile_transaction(self.conn, incoming('sub', next_date, PERIOD)))
        self.assertEqual(len(ledger.pending(self.conn, NOW)), 2)
        self.assertFalse(ledger.reconcile_transaction(self.conn, incoming('sub', next_date, PERIOD)))
        self.assertFalse(ledger.record_payment(self.conn, renewal(expires_at=START + 2 * PERIOD)))
        self.assertEqual(len(ledger.pending(self.conn, NOW)), 2)

    def test_outgoing_transaction_records_a_refund(self):
        ledger.record_payment(self.conn, ledger.parse_payment(paid()))
        refund = {'id': 'stx-1', 'amount': 5, 'date': START,
                  'receiver': {'type': 'user', 'transaction_type': 'invoice_payment', 'user': {'id': 42}}}
        self.assertTrue(ledger.reconcile_transaction(self.conn, refund))
        self.assertEqual(ledger.pending(self.conn, NOW), [])

    def test_refund_seen_first_stops_the_recovered_payment(self):
        refund = {'id': 'stx-1', 'amount': 5, 'date': START,
                  'receiver': {'type': 'user', 'transaction_type': 'invoice_payment', 'user': {'id': 42}}}
        ledger.reconcile_transaction(self.conn, refund)
        ledger.reconcile_transaction(self.conn, incoming())
        self.assertEqual(ledger.pending(self.conn, NOW), [])

    def test_other_partners_are_ignored(self):
        for partner in ({'type': 'fragment'}, {'type': 'user', 'transaction_type': 'gift_purchase'}):
            transaction = {'id': 'x', 'amount': 1, 'date': START, 'source': partner}
            self.assertFalse(ledger.reconcile_transaction(self.conn, transaction))
            self.assertFalse(ledger.reconcile_transaction(
                self.conn, {'id': 'x', 'amount': 1, 'date': START, 'receiver': partner}))
        self.assertEqual(ledger.pending(self.conn, NOW), [])

    def test_broken_transactions_raise(self):
        broken = [None, [], {}, {'id': ''}, {'id': 'x', 'amount': '1', 'date': START},
                  {'id': 'x', 'amount': 1, 'date': None},
                  incoming(invoice_payload=None), incoming(user={}), incoming(period=-1)]
        for transaction in broken:
            with self.subTest(transaction), self.assertRaises(ValueError):
                ledger.reconcile_transaction(self.conn, transaction)


if __name__ == '__main__':
    unittest.main()
