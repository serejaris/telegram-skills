from contextlib import contextmanager
from dataclasses import dataclass
import os
import sqlite3

PENDING = 'pending'
CLAIMED = 'claimed'
DELIVERED = 'delivered'
REFUNDED = 'refunded'

DEFAULT_LEASE = 300
BUSY_TIMEOUT = 30

MESSAGE_FIELDS = ('message', 'edited_message', 'channel_post', 'edited_channel_post',
                  'business_message', 'edited_business_message', 'guest_message')

SCHEMA = (
    f"""
    CREATE TABLE IF NOT EXISTS star_payments (
        charge_id TEXT NOT NULL,
        subscription_expires_at INTEGER NOT NULL DEFAULT 0,
        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        payload TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT '{PENDING}'
            CHECK (state IN ('{PENDING}', '{CLAIMED}', '{DELIVERED}', '{REFUNDED}')),
        lease_until INTEGER NOT NULL DEFAULT 0,
        estimated_period INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (charge_id, subscription_expires_at)
    )
    """,
    'CREATE TABLE IF NOT EXISTS star_refunds_unmatched (charge_id TEXT PRIMARY KEY)',
)


@dataclass(frozen=True)
class Payment:
    charge_id: str
    subscription_expires_at: int
    user_id: int
    amount: int
    payload: str

    @property
    def key(self):
        return self.charge_id, self.subscription_expires_at


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _parse_charge(event, name):
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
    for field in MESSAGE_FIELDS:
        message = update.get(field)
        if isinstance(message, dict):
            return message
    return None


def parse_payment(update):
    message = _message(update)
    if message is None or 'successful_payment' not in message:
        return None
    event = message['successful_payment']
    charge_id, amount, payload = _parse_charge(event, 'successful_payment')
    expires_at = event.get('subscription_expiration_date', 0)
    if not _is_int(expires_at) or expires_at < 0:
        raise ValueError('subscription_expiration_date is not a Unix time')
    sender = message.get('from')
    user_id = sender.get('id') if isinstance(sender, dict) else None
    if not _is_int(user_id) or user_id < 1:
        raise ValueError('successful_payment message has no sender id')
    return Payment(charge_id, expires_at, user_id, amount, payload)


def parse_refund_charge_id(update):
    message = _message(update)
    if message is None or 'refunded_payment' not in message:
        return None
    return _parse_charge(message['refunded_payment'], 'refunded_payment')[0]


def connect(path):
    if not isinstance(path, (str, os.PathLike)) or os.fspath(path) in ('', ':memory:'):
        raise ValueError('the ledger needs a file path')
    conn = sqlite3.connect(path, timeout=BUSY_TIMEOUT, isolation_level=None)
    with transaction(conn):
        for statement in SCHEMA:
            conn.execute(statement)
    return conn


@contextmanager
def transaction(conn):
    if conn.in_transaction:
        yield
        return
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield
    except BaseException:
        conn.rollback()
        raise
    conn.commit()


def _insert(conn, payment, estimated_period=0):
    refunded = conn.execute('DELETE FROM star_refunds_unmatched WHERE charge_id = ?',
                            (payment.charge_id,)).rowcount
    cursor = conn.execute(
        'INSERT OR IGNORE INTO star_payments '
        '(charge_id, subscription_expires_at, user_id, amount, payload, state, estimated_period) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        (*payment.key, payment.user_id, payment.amount, payment.payload,
         REFUNDED if refunded else PENDING, estimated_period),
    )
    return cursor.rowcount == 1


def _settle_estimate(conn, payment):
    if not payment.subscription_expires_at:
        return False
    rows = conn.execute(
        'SELECT subscription_expires_at, estimated_period FROM star_payments '
        'WHERE charge_id = ? AND estimated_period > 0',
        (payment.charge_id,),
    ).fetchall()
    for estimated, period in rows:
        if abs(estimated - payment.subscription_expires_at) <= period // 2:
            conn.execute(
                'UPDATE star_payments SET subscription_expires_at = ?, estimated_period = 0 '
                'WHERE charge_id = ? AND subscription_expires_at = ?',
                (payment.subscription_expires_at, payment.charge_id, estimated),
            )
            return True
    return False


def record_payment(conn, payment):
    with transaction(conn):
        return not _settle_estimate(conn, payment) and _insert(conn, payment)


def reconcile_transaction(conn, star_transaction):
    if not isinstance(star_transaction, dict):
        raise ValueError('StarTransaction is not an object')
    charge_id = star_transaction.get('id')
    amount = star_transaction.get('amount')
    date = star_transaction.get('date')
    if not isinstance(charge_id, str) or not charge_id:
        raise ValueError('StarTransaction has no id')
    if not _is_int(amount) or not _is_int(date):
        raise ValueError('StarTransaction amount and date must be integers')
    receiver = star_transaction.get('receiver')
    if _is_invoice_partner(receiver):
        return record_refund(conn, charge_id)
    source = star_transaction.get('source')
    if not _is_invoice_partner(source):
        return False
    user = source.get('user')
    user_id = user.get('id') if isinstance(user, dict) else None
    payload = source.get('invoice_payload')
    period = source.get('subscription_period', 0)
    if not _is_int(user_id) or user_id < 1 or not isinstance(payload, str):
        raise ValueError('StarTransaction source has no user id or invoice_payload')
    if not _is_int(period) or period < 0:
        raise ValueError('subscription_period is not a positive integer')
    with transaction(conn):
        if not period:
            return _insert(conn, Payment(charge_id, 0, user_id, amount, payload))
        recorded = conn.execute(
            'SELECT subscription_expires_at FROM star_payments WHERE charge_id = ?', (charge_id,)
        ).fetchall()
        if any(abs(expires_at - period - date) <= period // 2 for expires_at, in recorded):
            return False
        return _insert(conn, Payment(charge_id, date + period, user_id, amount, payload), period)


def _is_invoice_partner(partner):
    return (isinstance(partner, dict) and partner.get('type') == 'user'
            and partner.get('transaction_type') == 'invoice_payment')


def pending(conn, now):
    rows = conn.execute(
        'SELECT charge_id, subscription_expires_at, user_id, amount, payload FROM star_payments '
        'WHERE state = ? OR (state = ? AND lease_until <= ?) ORDER BY rowid',
        (PENDING, CLAIMED, now),
    )
    return [Payment(*row) for row in rows]


def claim(conn, payment, now, lease=DEFAULT_LEASE):
    cursor = conn.execute(
        'UPDATE star_payments SET state = ?, lease_until = ? '
        'WHERE charge_id = ? AND subscription_expires_at = ? '
        'AND (state = ? OR (state = ? AND lease_until <= ?))',
        (CLAIMED, now + lease, *payment.key, PENDING, CLAIMED, now),
    )
    return cursor.rowcount == 1


def release(conn, payment):
    cursor = conn.execute(
        'UPDATE star_payments SET state = ?, lease_until = 0 '
        'WHERE charge_id = ? AND subscription_expires_at = ? AND state = ?',
        (PENDING, *payment.key, CLAIMED),
    )
    return cursor.rowcount == 1


def mark_delivered(conn, payment):
    cursor = conn.execute(
        'UPDATE star_payments SET state = ?, lease_until = 0 '
        'WHERE charge_id = ? AND subscription_expires_at = ? AND state = ?',
        (DELIVERED, *payment.key, CLAIMED),
    )
    return cursor.rowcount == 1


def record_refund(conn, charge_id):
    with transaction(conn):
        rows = conn.execute(
            'SELECT subscription_expires_at, state FROM star_payments WHERE charge_id = ? '
            'ORDER BY subscription_expires_at DESC',
            (charge_id,),
        ).fetchall()
        if not rows:
            cursor = conn.execute(
                'INSERT OR IGNORE INTO star_refunds_unmatched (charge_id) VALUES (?)', (charge_id,))
            return cursor.rowcount == 1
        for expires_at, state in rows:
            if state != REFUNDED:
                conn.execute(
                    'UPDATE star_payments SET state = ?, lease_until = 0 '
                    'WHERE charge_id = ? AND subscription_expires_at = ?',
                    (REFUNDED, charge_id, expires_at),
                )
                return True
        return False
