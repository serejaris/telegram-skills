import importlib.util
from pathlib import Path
import unittest

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from vectors import BOT_ID, PUBLIC_KEY, SIGNED_INIT_DATA

SPEC = importlib.util.spec_from_file_location(
    'init_data', Path(__file__).parents[1] / 'scripts/init_data.py')
init_data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(init_data)


class Ed25519Verification(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUBLIC_KEY))
        self.message, self.signature = init_data.third_party_payload(SIGNED_INIT_DATA, BOT_ID)

    def test_payload_verifies_with_the_test_key(self):
        self.key.verify(self.signature, self.message)

    def test_changed_message_is_rejected(self):
        with self.assertRaises(InvalidSignature):
            self.key.verify(self.signature, self.message + b'x')

    def test_other_bot_id_is_rejected(self):
        message, signature = init_data.third_party_payload(SIGNED_INIT_DATA, BOT_ID + 1)
        with self.assertRaises(InvalidSignature):
            self.key.verify(signature, message)


if __name__ == '__main__':
    unittest.main()
