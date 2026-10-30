"""Vectors come from Telegram-Mini-Apps/tma.js (MIT): apps/docs/packages/tma-js-init-data/validating.md
and packages/init-data/test/fixtures.ts at commit a841aba28517c138af7debf4ad557fcf0c1f92fd.
These are public test values of that project, published with their test bot tokens.
"""

import importlib.util
from pathlib import Path
import unittest
from urllib.parse import quote

SPEC = importlib.util.spec_from_file_location(
    'init_data', Path(__file__).parents[1] / 'scripts/init_data.py')
init_data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(init_data)

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:
    Ed25519PublicKey = None

DOCS_TOKEN = '5768337691:AAH5YkoiEuPk8-FZa32hStHTqXiLPtAEhx8'
DOCS_INIT_DATA = (
    'query_id=AAHdF6IQAAAAAN0XohDhrOrc'
    '&user=%7B%22id%22%3A279058397%2C%22first_name%22%3A%22Vladislav%22%2C%22last_name%22'
    '%3A%22Kibenko%22%2C%22username%22%3A%22vdkfrost%22%2C%22language_code%22%3A%22ru%22'
    '%2C%22is_premium%22%3Atrue%7D'
    '&auth_date=1662771648'
    '&hash=c501b71e775f74ce10e377dea85a7ea24ecd640b223ea86dfe453e0eaed2e2b2')

# tma.js labels this "Real init data signed by Telegram", created 2024-12-07.
REAL_BOT_ID = 7342037359
REAL_TOKEN = f'{REAL_BOT_ID}:AAFZehRPBRs8Seg40oDjTMIW8uTGPuW1zfQ'
REAL_AUTH_DATE = 1733584787
REAL_SIGNATURE = ('zL-ucjNyREiHDE8aihFwpfR9aggP2xiAo3NSpfe-p7IbCisNlDKlo7Kb6G4D0Ao2mBrSgEk4'
                  'maLSdv6MLIlADQ')
REAL_INIT_DATA = (
    'user=%7B%22id%22%3A279058397%2C%22first_name%22%3A%22Vladislav%20%2B%20-%20%3F%20%5C%2F%22'
    '%2C%22last_name%22%3A%22Kibenko%22%2C%22username%22%3A%22vdkfrost%22%2C%22language_code%22'
    '%3A%22ru%22%2C%22is_premium%22%3Atrue%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22'
    '%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2F4FPEE4tmP3ATHa57u6MqTDih13'
    'LTOiMoKoLDRG4PnSA.svg%22%7D&chat_instance=8134722200314281151&chat_type=private'
    f'&auth_date={REAL_AUTH_DATE}&signature={REAL_SIGNATURE}'
    '&hash=2174df5b000556d044f3f020384e879c8efcab55ddea2ced4eb752e93e7080d6')
TELEGRAM_PRODUCTION_KEY = 'e7bf03a2fa4602af4580703d88dda5bb59f32ed8b02a56c187fe7d34caed242d'


def signed(fields, token=REAL_TOKEN):
    body = '&'.join(f'{key}={quote(value, safe="")}' for key, value in fields.items())
    return f'{body}&hash={init_data.compute_hash(fields, token)}'


class Validate(unittest.TestCase):
    def assert_code(self, code, *args, **kwargs):
        with self.assertRaises(init_data.InitDataError) as caught:
            init_data.validate(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def test_documented_vector_without_signature(self):
        fields = init_data.validate(DOCS_INIT_DATA, DOCS_TOKEN, max_age=0)
        self.assertEqual(fields['auth_date'], '1662771648')
        self.assertIn('"id":279058397', fields['user'])

    def test_real_string_with_signature_keeps_it_in_the_hmac(self):
        fields = init_data.validate(REAL_INIT_DATA, REAL_TOKEN, max_age=0)
        self.assertEqual(fields['signature'], REAL_SIGNATURE)
        self.assertIn('signature=', init_data.data_check_string(fields))
        without = {key: value for key, value in fields.items() if key != 'signature'}
        self.assertNotEqual(init_data.compute_hash(without, REAL_TOKEN), fields['hash'])

    def test_field_order_does_not_matter(self):
        parts = REAL_INIT_DATA.split('&')
        self.assertTrue(init_data.validate('&'.join(reversed(parts)), REAL_TOKEN, max_age=0))

    def test_uppercase_hash_is_accepted(self):
        body, received = REAL_INIT_DATA.rsplit('hash=', 1)
        self.assertTrue(init_data.validate(f'{body}hash={received.upper()}', REAL_TOKEN, max_age=0))

    def test_wrong_token_and_tampering(self):
        self.assert_code('invalid_hash', REAL_INIT_DATA, DOCS_TOKEN, max_age=0)
        tampered = REAL_INIT_DATA.replace('279058397', '279058398')
        self.assert_code('invalid_hash', tampered, REAL_TOKEN, max_age=0)
        added = REAL_INIT_DATA + '&start_param=admin'
        self.assert_code('invalid_hash', added, REAL_TOKEN, max_age=0)
        dropped = REAL_INIT_DATA.replace(f'&signature={REAL_SIGNATURE}', '')
        self.assert_code('invalid_hash', dropped, REAL_TOKEN, max_age=0)

    def test_age_boundary(self):
        limit = REAL_AUTH_DATE + init_data.DEFAULT_MAX_AGE
        self.assertTrue(init_data.validate(REAL_INIT_DATA, REAL_TOKEN, now=limit))
        self.assert_code('expired', REAL_INIT_DATA, REAL_TOKEN, now=limit + 1)
        self.assert_code('expired', REAL_INIT_DATA, REAL_TOKEN)
        self.assertTrue(init_data.validate(REAL_INIT_DATA, REAL_TOKEN, max_age=60,
                                           now=REAL_AUTH_DATE + 60))

    def test_auth_date_is_checked_on_signed_data(self):
        for value in ('', 'soon', '-1', '1.5', '١٢٣'):
            self.assert_code('invalid_auth_date', signed({'auth_date': value}), REAL_TOKEN, max_age=0)
        self.assert_code('invalid_auth_date', signed({'user': '{}'}), REAL_TOKEN, max_age=0)

    def test_garbage_input(self):
        for raw in ('', ' ', 'a', '=', '=value', 'hash', '&&', 'a=1&&b=2', 'a=1&a=2', 'a=%FF',
                    'hash=zz', 'hash=' + 'g' * 64, 'hash=' + 'a' * 63, 'hash=' + 'a' * 65,
                    'hash=aa&hash=bb', None, 123, b'hash=aa', [], {}):
            with self.assertRaises(init_data.InitDataError) as caught:
                init_data.validate(raw, REAL_TOKEN)
            self.assertIn(caught.exception.code, ('malformed', 'missing_hash'), raw)
        self.assert_code('missing_hash', 'auth_date=1', REAL_TOKEN)

    def test_bad_settings(self):
        for token in ('', None, 123):
            self.assert_code('malformed', REAL_INIT_DATA, token)
        for max_age in (-1, 1.5, '60', None, True):
            self.assert_code('malformed', REAL_INIT_DATA, REAL_TOKEN, max_age=max_age)


class ThirdParty(unittest.TestCase):
    def test_payload_shape(self):
        message, signature = init_data.third_party_payload(REAL_INIT_DATA, REAL_BOT_ID)
        lines = message.decode().split('\n')
        self.assertEqual(lines[:4], [f'{REAL_BOT_ID}:WebAppData', f'auth_date={REAL_AUTH_DATE}',
                                     'chat_instance=8134722200314281151', 'chat_type=private'])
        self.assertEqual(len(lines), 5)
        self.assertNotIn(b'signature=', message)
        self.assertNotIn(b'hash=', message)
        self.assertEqual(len(signature), 64)

    def test_padded_signature_decodes_the_same(self):
        padded = REAL_INIT_DATA.replace(REAL_SIGNATURE, REAL_SIGNATURE + '%3D%3D')
        self.assertEqual(init_data.third_party_payload(padded, REAL_BOT_ID),
                         init_data.third_party_payload(REAL_INIT_DATA, REAL_BOT_ID))

    def test_garbage_input(self):
        cases = [(DOCS_INIT_DATA, 1, 'missing_signature'), ('a=1', 1, 'missing_signature'),
                 ('signature=', 1, 'malformed'), ('signature=%21%21', 1, 'malformed'),
                 ('signature=abcd', 1, 'malformed'), ('signature=a', 1, 'malformed'),
                 (None, 1, 'malformed'), (REAL_INIT_DATA, 0, 'malformed'),
                 (REAL_INIT_DATA, True, 'malformed'), (REAL_INIT_DATA, '1', 'malformed')]
        for raw, bot_id, code in cases:
            with self.assertRaises(init_data.InitDataError) as caught:
                init_data.third_party_payload(raw, bot_id)
            self.assertEqual(caught.exception.code, code, raw)

    @unittest.skipIf(Ed25519PublicKey is None, 'cryptography is not installed')
    def test_real_signature_verifies_with_the_production_key(self):
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(TELEGRAM_PRODUCTION_KEY))
        message, signature = init_data.third_party_payload(REAL_INIT_DATA, REAL_BOT_ID)
        key.verify(signature, message)
        with self.assertRaises(InvalidSignature):
            key.verify(signature, message + b'x')


if __name__ == '__main__':
    unittest.main()
