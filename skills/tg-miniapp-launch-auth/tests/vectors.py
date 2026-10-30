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
