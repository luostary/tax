BOT_TOKEN=""

BOT_ID = "UNIQ_BOT_ID"

CURRENCY = "тл."

CURRENCY_WALLET = "usd"

ENV = "PROD"

LANGUAGE = "RU"

LIMIT_THESE_USERS = []

WALLET = ""

PERCENT = 5

ONLINE_TIME_SEC = 600 # 10

ORDER_REPEAT_TIME_SEC = 60 # 2

RATE_1_KM = 11 # In local currency

RATE_1_USDT = 18

RATE_REFERER = 4 # In US dollars

MIN_AMOUNT = 80 # In local currency

MIN_BALANCE_AMOUNT = 10 # In US dollars

HAS_CONFIRM_STEPS_DRIVER = False

HAS_CONFIRM_STEPS_CLIENT = False

ALLOW_MANY_ORDERS = False

ADMIN_TG = "@your_admin_nickname"
ADMIN_ID = 0
DEVELOPER_ID = 0

GOOGLE_API_KEY = "YOUR_API_KEY_FROM_GOOGLE"

DB_TYPE = "sqlite"
DB_HOST = "127.0.0.1"
DB_USER = "database_user"
DB_PASSWORD = "database_password"
DB_NAME = "database_name"
DB_CONNECTION_TIMEOUT = 610
DB_RECONNECT_CONNECTION_AFTER_QUERY = True
DB_LOCATION_POSTFIX = ''


from os.path import exists
if exists('params.py'):
    from params import *
