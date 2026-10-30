# Synthetic vectors. Nothing here came from Telegram or from a real account: the token,
# bot id and user are invented, and the Ed25519 key is not Telegram's.
# init_data.py did not produce the constants. They were computed beforehand with OpenSSL
# 4.1.0, and Node crypto.verify confirmed the signature:
#
#   seed=$(printf %s 'telegram-skills ed25519 test key' | openssl dgst -sha256 -r | cut -d' ' -f1)
#   printf '302e020100300506032b657004220420%s' "$seed" | xxd -r -p |
#     openssl pkey -inform DER -out key.pem
#   openssl pkey -in key.pem -pubout -outform DER | tail -c 32 | xxd -p -c 64     # PUBLIC_KEY
#   openssl pkeyutl -sign -inkey key.pem -rawin -in message -out sig              # SIGNATURE
#   openssl base64 -A -in sig | tr '+/' '-_' | tr -d '='
#   secret=$(printf %s "$TOKEN" | openssl dgst -sha256 -hmac WebAppData -r | cut -d' ' -f1)
#   openssl dgst -sha256 -mac HMAC -macopt hexkey:$secret -r check-string         # *_HASH
#
# `message` is "<BOT_ID>:WebAppData\n" plus the sorted fields without hash and signature.
# `check-string` is the sorted fields without hash, so it includes signature.
# Each line of both files is key=value; lines are joined with \n, no trailing newline.
from urllib.parse import quote

TOKEN = 'test-token-not-a-real-bot'
OTHER_TOKEN = 'other-test-token-not-a-real-bot'
BOT_ID = 1000001
AUTH_DATE = 1700000000
CHAT_INSTANCE = '1000003'
PUBLIC_KEY = '021c5fa975dba9e91686148317ddbedcb7dd0913ed407fd5686fa11edb319bd6'
SIGNATURE = 'zrfDJAaAko0BaJ45zj_7L8pEEuKtIs-VLVhRMfYt8AJ5WRANhmsHoAMcuxkK4V_5j9u1b3qniw_aKKQu4cbTCQ'
SIGNED_HASH = 'dfbe54f85b4a08c63dd070e0494d00d792a7c7413a0474e390af61cc4ada8046'
USER = ('{"id":1000002,"first_name":"Test + - ? \\/","last_name":"User","username":"example_user",'
        '"language_code":"en","is_premium":true,"allows_write_to_pm":true,'
        '"photo_url":"https:\\/\\/example.com\\/avatar.svg"}')
SIGNED_INIT_DATA = (f'user={quote(USER, safe="")}&chat_instance={CHAT_INSTANCE}&chat_type=private'
                    f'&auth_date={AUTH_DATE}&signature={SIGNATURE}&hash={SIGNED_HASH}')

PLAIN_USER = '{"id":1000002,"first_name":"Test"}'
PLAIN_HASH = '9b6a56a25937df89fcd15f79ef3bf7fd03582fc7b55ba09273709120caea3f2f'
PLAIN_INIT_DATA = (f'query_id=test-query&user={quote(PLAIN_USER, safe="")}'
                   f'&auth_date={AUTH_DATE}&hash={PLAIN_HASH}')
