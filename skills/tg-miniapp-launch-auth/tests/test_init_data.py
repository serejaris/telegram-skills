import importlib.util
from pathlib import Path
import unittest
from urllib.parse import quote

from vectors import (AUTH_DATE, BOT_ID, CHAT_INSTANCE, OTHER_TOKEN, PLAIN_HASH, PLAIN_INIT_DATA,
                     PLAIN_USER, SIGNATURE, SIGNED_HASH, SIGNED_INIT_DATA, TOKEN)

SPEC = importlib.util.spec_from_file_location(
    'init_data', Path(__file__).parents[1] / 'scripts/init_data.py')
init_data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(init_data)


def signed(fields, token=TOKEN):
    body = '&'.join(f'{key}={quote(value, safe="")}' for key, value in fields.items())
    return f'{body}&hash={init_data.compute_hash(fields, token)}'


class Validate(unittest.TestCase):
    def assert_code(self, code, *args, **kwargs):
        with self.assertRaises(init_data.InitDataError) as caught:
            init_data.validate(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def test_computed_hash_matches_the_openssl_constant(self):
        fields = init_data.parse_init_data(SIGNED_INIT_DATA)
        self.assertEqual(init_data.compute_hash(fields, TOKEN), SIGNED_HASH)

    def test_vector_without_signature(self):
        fields = init_data.validate(PLAIN_INIT_DATA, TOKEN, max_age=0)
        self.assertEqual(fields['hash'], PLAIN_HASH)
        self.assertEqual(fields['user'], PLAIN_USER)

    def test_signature_stays_in_the_hmac(self):
        fields = init_data.validate(SIGNED_INIT_DATA, TOKEN, max_age=0)
        self.assertEqual(fields['signature'], SIGNATURE)
        self.assertIn('signature=', init_data.data_check_string(fields))
        without = {key: value for key, value in fields.items() if key != 'signature'}
        self.assertNotEqual(init_data.compute_hash(without, TOKEN), fields['hash'])

    def test_field_order_does_not_matter(self):
        parts = SIGNED_INIT_DATA.split('&')
        self.assertTrue(init_data.validate('&'.join(reversed(parts)), TOKEN, max_age=0))

    def test_uppercase_hash_is_accepted(self):
        body, received = SIGNED_INIT_DATA.rsplit('hash=', 1)
        self.assertTrue(init_data.validate(f'{body}hash={received.upper()}', TOKEN, max_age=0))

    def test_wrong_token_and_tampering(self):
        self.assert_code('invalid_hash', SIGNED_INIT_DATA, OTHER_TOKEN, max_age=0)
        tampered = SIGNED_INIT_DATA.replace('1000002', '1000009')
        self.assert_code('invalid_hash', tampered, TOKEN, max_age=0)
        added = SIGNED_INIT_DATA + '&start_param=admin'
        self.assert_code('invalid_hash', added, TOKEN, max_age=0)
        dropped = SIGNED_INIT_DATA.replace(f'&signature={SIGNATURE}', '')
        self.assert_code('invalid_hash', dropped, TOKEN, max_age=0)

    def test_age_boundary(self):
        limit = AUTH_DATE + init_data.DEFAULT_MAX_AGE
        self.assertTrue(init_data.validate(SIGNED_INIT_DATA, TOKEN, now=limit))
        self.assert_code('expired', SIGNED_INIT_DATA, TOKEN, now=limit + 1)
        self.assert_code('expired', SIGNED_INIT_DATA, TOKEN)
        self.assertTrue(init_data.validate(SIGNED_INIT_DATA, TOKEN, max_age=60, now=AUTH_DATE + 60))

    def test_auth_date_is_checked_on_signed_data(self):
        for value in ('', 'soon', '-1', '1.5', '١٢٣'):
            self.assert_code('invalid_auth_date', signed({'auth_date': value}), TOKEN, max_age=0)
        self.assert_code('invalid_auth_date', signed({'user': '{}'}), TOKEN, max_age=0)

    def test_garbage_input(self):
        for raw in ('', ' ', 'a', '=', '=value', 'hash', '&&', 'a=1&&b=2', 'a=1&a=2', 'a=%FF',
                    'hash=zz', 'hash=' + 'g' * 64, 'hash=' + 'a' * 63, 'hash=' + 'a' * 65,
                    'hash=aa&hash=bb', None, 123, b'hash=aa', [], {}):
            with self.assertRaises(init_data.InitDataError) as caught:
                init_data.validate(raw, TOKEN)
            self.assertIn(caught.exception.code, ('malformed', 'missing_hash'), raw)
        self.assert_code('missing_hash', 'auth_date=1', TOKEN)

    def test_bad_settings(self):
        for token in ('', None, 123):
            self.assert_code('malformed', SIGNED_INIT_DATA, token)
        for max_age in (-1, 1.5, '60', None, True):
            self.assert_code('malformed', SIGNED_INIT_DATA, TOKEN, max_age=max_age)


class ThirdParty(unittest.TestCase):
    def test_payload_shape(self):
        message, signature = init_data.third_party_payload(SIGNED_INIT_DATA, BOT_ID)
        lines = message.decode().split('\n')
        self.assertEqual(lines[:4], [f'{BOT_ID}:WebAppData', f'auth_date={AUTH_DATE}',
                                     f'chat_instance={CHAT_INSTANCE}', 'chat_type=private'])
        self.assertEqual(len(lines), 5)
        self.assertNotIn(b'signature=', message)
        self.assertNotIn(b'hash=', message)
        self.assertEqual(len(signature), 64)

    def test_padded_signature_decodes_the_same(self):
        padded = SIGNED_INIT_DATA.replace(SIGNATURE, SIGNATURE + '%3D%3D')
        self.assertEqual(init_data.third_party_payload(padded, BOT_ID),
                         init_data.third_party_payload(SIGNED_INIT_DATA, BOT_ID))

    def test_garbage_input(self):
        cases = [(PLAIN_INIT_DATA, 1, 'missing_signature'), ('a=1', 1, 'missing_signature'),
                 ('signature=', 1, 'malformed'), ('signature=%21%21', 1, 'malformed'),
                 ('signature=abcd', 1, 'malformed'), ('signature=a', 1, 'malformed'),
                 (None, 1, 'malformed'), (SIGNED_INIT_DATA, 0, 'malformed'),
                 (SIGNED_INIT_DATA, True, 'malformed'), (SIGNED_INIT_DATA, '1', 'malformed')]
        for raw, bot_id, code in cases:
            with self.assertRaises(init_data.InitDataError) as caught:
                init_data.third_party_payload(raw, bot_id)
            self.assertEqual(caught.exception.code, code, raw)


if __name__ == '__main__':
    unittest.main()
