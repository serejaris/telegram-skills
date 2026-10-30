"""Exactly-once crediting for Telegram Stars payments. Standard library only, no network.

Call parse_payment() on every raw Update, then record_payment() in the same
database transaction that creates the order. Delivery runs from pending():
a crash between the two leaves the row pending, it is neither lost nor doubled.
"""
from dataclasses import dataclass
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS star_payments (
    charge_id TEXT NOT NULL,
    period_end INTEGER NOT NULL DEFAULT 0,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    payload TEXT NOT NULL,
    delivered INTEGER NOT NULL DEFAULT 0,
    refunded INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (charge_id, period_end)
)
"""


@dataclass(frozen=True)
class Payment:
    charge_id: str
    period_end: int  # subscription_expiration_date, 0 for a one-time payment
    user_id: int
    amount: int
    payload: str


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _common(event, name):
    if not isinstance(event, dict):
        raise ValueError(f'{name} is not an object')
    charge_id = event.get('telegram_payment_charge_id')
    if not isinstance(charge_id, str) or not charge_id:
        raise ValueError(f'{name} has no telegram_payment_charge_id')
    if event.get('currency') != 'XTR':
        raise ValueError(f'{name} currency is not XTR')
    amount = event.get('total_amount')
    if not _is_int(amount) or amount < 1:
        raise ValueError(f'{name} total_amount is not a positive integer')
    payload = event.get('invoice_payload')
    if not isinstance(payload, str):
        raise ValueError(f'{name} invoice_payload is not a string')
    return charge_id, amount, payload


def _message(update):
    if not isinstance(update, dict):
        raise ValueError('update is not an object')
    message = update.get('message')
    return message if isinstance(message, dict) else None


def parse_payment(update):
    """Return a Payment, None for any other update, ValueError for a broken payment."""
    message = _message(update)
    if message is None or 'successful_payment' not in message:
        return None
    event = message['successful_payment']
    charge_id, amount, payload = _common(event, 'successful_payment')
    period_end = event.get('subscription_expiration_date', 0)
    if not _is_int(period_end) or period_end < 0:
        raise ValueError('subscription_expiration_date is not a Unix time')
    sender = message.get('from')
    user_id = sender.get('id') if isinstance(sender, dict) else None
    if not _is_int(user_id) or user_id < 1:
        raise ValueError('successful_payment message has no sender id')
    return Payment(charge_id, period_end, user_id, amount, payload)


def parse_refund_charge_id(update):
    """Return the refunded charge id, None for any other update, ValueError for a broken refund."""
    message = _message(update)
    if message is None or 'refunded_payment' not in message:
        return None
    return _common(message['refunded_payment'], 'refunded_payment')[0]


def init(conn):
    conn.execute(SCHEMA)


def record_payment(conn, payment):
    """Insert the payment. True for the first sighting, False for a duplicate."""
    cursor = conn.execute(
        'INSERT OR IGNORE INTO star_payments '
        '(charge_id, period_end, user_id, amount, payload) VALUES (?, ?, ?, ?, ?)',
        (payment.charge_id, payment.period_end, payment.user_id, payment.amount, payment.payload),
    )
    return cursor.rowcount == 1


def pending(conn):
    """Payments recorded but not yet delivered, refunded ones excluded."""
    rows = conn.execute(
        'SELECT charge_id, period_end, user_id, amount, payload FROM star_payments '
        'WHERE delivered = 0 AND refunded = 0 ORDER BY rowid'
    )
    return [Payment(*row) for row in rows]


def mark_delivered(conn, payment):
    """True when this call moved the row to delivered, False when it already was or is refunded."""
    cursor = conn.execute(
        'UPDATE star_payments SET delivered = 1 '
        'WHERE charge_id = ? AND period_end = ? AND delivered = 0 AND refunded = 0',
        (payment.charge_id, payment.period_end),
    )
    return cursor.rowcount == 1


def record_refund(conn, charge_id):
    """Mark the newest period of the charge refunded. False when unknown or already refunded."""
    row = conn.execute(
        'SELECT period_end FROM star_payments WHERE charge_id = ? AND refunded = 0 '
        'ORDER BY period_end DESC LIMIT 1',
        (charge_id,),
    ).fetchone()
    if row is None:
        return False
    conn.execute(
        'UPDATE star_payments SET refunded = 1 WHERE charge_id = ? AND period_end = ?',
        (charge_id, row[0]),
    )
    return True


def connect(path=':memory:'):
    conn = sqlite3.connect(path)
    init(conn)
    return conn
