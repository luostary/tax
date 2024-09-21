import time

from aiogram import executor
from dispatcher import dp
import handlers
from db import BotDB
from config import *

db = BotDB()

if __name__ == "__main__":
    schema = db.get_sleep_queries_cn()
    if schema['query_count'] > 50:
        print('Warning! You should kill sleep queries... And use the "CTRL+C" command')
    if ENV == "PROD":
        while True:
            try:
                executor.start_polling(dp, skip_updates=True)
            except Exception as e:
                time.sleep(2)
                print(e)
    else:
        executor.start_polling(dp, skip_updates=True)
    pass