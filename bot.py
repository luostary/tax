import aiogram
import asyncio
from aiogram import executor
from dispatcher import dp
import handlers
from db import BotDB
from config import *

BotDB = BotDB('taxi.db')

if __name__ == "__main__":
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