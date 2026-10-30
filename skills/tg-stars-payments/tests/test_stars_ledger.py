import copy
import importlib.util
from pathlib import Path
import sys
import unittest

SPEC = importlib.util.spec_from_file_location('stars_ledger', Path(__file__).parents[1] / 'scripts/stars_ledger.py')
ledger = importlib.util.module_from_spec(SPEC)
sys.modules['stars_ledger'] = ledger
SPEC.loader.exec_module(ledger)


def paid(update_id=1, charge='stx-1', **extra):
    event = {'currency': 'XTR', 'total_amount': 5, 'invoice_payload': 'sku-1',
             'telegram_payment_charge_id': charge, 'provider_payment_charge_id': '', **extra}
    return {'update_id': update_id,
            'message': {'message_id': 9, 'from': {'id': 42}, 'chat': {'id': 42}, 'successful_payment': event}}


def refunded(charge='stx-1'):
    event = {'currency': 'XTR', 'total_amount': 5, 'invoice_payload': 'sku-1',
             'telegram_payment_charge_id': charge}
    return {'update_id': 7, 'message': {'from': {'id': 42}, 'refunded_payment': event}}


class Parsing(unittest.TestCase):
    def test_reads_payment_fields(self):
        payment = ledger.parse_payment(paid())
        self.assertEqual(payment, ledger.Payment('stx-1', 0, 42, 5, 'sku-1'))

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


class Crediting(unittest.TestCase):
    def setUp(self):
        self.conn = ledger.connect()
        self.addCleanup(self.conn.close)

    def test_duplicate_with_new_update_id_delivers_once(self):
        first, second = paid(update_id=100), paid(update_id=200)
        self.assertTrue(ledger.record_payment(self.conn, ledger.parse_payment(first)))
        self.assertFalse(ledger.record_payment(self.conn, ledger.parse_payment(second)))
        due = ledger.pending(self.conn)
        self.assertEqual(len(due), 1)
        self.assertTrue(ledger.mark_delivered(self.conn, due[0]))
        self.assertFalse(ledger.mark_delivered(self.conn, due[0]))
        self.assertEqual(ledger.pending(self.conn), [])

    def test_same_update_id_with_new_charge_is_a_new_payment(self):
        self.assertTrue(ledger.record_payment(self.conn, ledger.parse_payment(paid(update_id=5, charge='a'))))
        self.assertTrue(ledger.record_payment(self.conn, ledger.parse_payment(paid(update_id=5, charge='b'))))
        self.assertEqual(len(ledger.pending(self.conn)), 2)

    def test_renewal_counts_whether_or_not_the_charge_id_repeats(self):
        for charges in (('sub', 'sub'), ('sub-1', 'sub-2')):
            conn = ledger.connect()
            self.addCleanup(conn.close)
            ledger.record_payment(conn, ledger.parse_payment(
                paid(charge=charges[0], subscription_expiration_date=1000, is_recurring=True)))
            renewal = ledger.parse_payment(
                paid(charge=charges[1], subscription_expiration_date=2000, is_recurring=True))
            self.assertTrue(ledger.record_payment(conn, renewal))
            self.assertFalse(ledger.record_payment(conn, copy.deepcopy(renewal)))
            self.assertEqual(len(ledger.pending(conn)), 2)

    def test_crash_before_delivery_leaves_payment_pending(self):
        payment = ledger.parse_payment(paid())
        ledger.record_payment(self.conn, payment)
        self.conn.commit()
        self.assertEqual(ledger.pending(self.conn), [payment])
        self.assertFalse(ledger.record_payment(self.conn, payment))
        self.assertEqual(ledger.pending(self.conn), [payment])

    def test_refund_blocks_delivery_and_is_idempotent(self):
        payment = ledger.parse_payment(paid())
        ledger.record_payment(self.conn, payment)
        charge = ledger.parse_refund_charge_id(refunded())
        self.assertTrue(ledger.record_refund(self.conn, charge))
        self.assertFalse(ledger.record_refund(self.conn, charge))
        self.assertEqual(ledger.pending(self.conn), [])
        self.assertFalse(ledger.mark_delivered(self.conn, payment))

    def test_refund_of_unknown_charge_changes_nothing(self):
        self.assertFalse(ledger.record_refund(self.conn, 'unknown'))

    def test_refund_touches_newest_period_only(self):
        for period_end in (1000, 2000):
            ledger.record_payment(self.conn, ledger.parse_payment(
                paid(charge='sub', subscription_expiration_date=period_end)))
        ledger.record_refund(self.conn, 'sub')
        self.assertEqual([p.period_end for p in ledger.pending(self.conn)], [1000])


if __name__ == '__main__':
    unittest.main()
