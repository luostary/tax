BOT_TOKEN=""

LANGUAGE = "RU"

WALLET = ""

PERCENT = 5

ONLINE_TIME_SEC = 600 # 10

ORDER_REPEAT_TIME_SEC = 60 # 2

RATE_1_KM = 11

RATE_1_USDT = 18

MIN_AMOUNT = 80

MIN_BALANCE_AMOUNT = 10

HAS_CONFIRM_STEPS_DRIVER = False

HAS_CONFIRM_STEPS_CLIENT = False

ALLOW_MANY_ORDERS = False

from os.path import exists
if exists('params.py'):
    from params import *
