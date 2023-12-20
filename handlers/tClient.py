import re, math, time, datetime
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from db import BotDB
from config import *
from language import t

BotDB = BotDB()

class Passenger:
    def __init__(self):
        pass

    def init(self):
        print('This is a Passenger class')

    async def getClientOrders(self, message, offset, message_id, chat_id):
        if (not BotDB.client_exists(message.from_user.id)):
            await message.bot.send_message(message.from_user.id, t('Client not found'))
        else:
            clientModel = BotDB.get_client(message.from_user.id)
            if (not clientModel):
                await message.bot.send_message(message.from_user.id, t("Unable to find customer"))
                pass
            else:
                modelOrders = BotDB.get_client_orders_by_one(message.from_user.id, offset)
                modelOrdersCn = len(BotDB.get_client_orders(message.from_user.id))
                if (modelOrdersCn) == 0:
                    await message.bot.send_message(message.from_user.id, t("You haven`t orders"))
                else:
                    for row in modelOrders:
                        try:
                            status = BotDB.statuses[row['status']]
                        except:
                            status = BotDB.statuses['unknown']
                        if not row['dt_order']:
                            dateFormat = 'Не указана'
                        else:
                            dateFormat = datetime.strptime(str(row['dt_order']), "%Y-%m-%d %H:%M:%S").strftime("%H:%M %d-%m-%Y")
                        text = '\n'.join((
                            '<b>Заказ №' + str(row['id']) + '</b>',
                            'Имя <b>' + str(clientModel['name']) + '</b>',
                            'Статус <b>' + status + '</b>',
                            'Дата <b>' + str(dateFormat) + '</b>',
                            'Стоимость <b>' + str(row['amount_client']) + ' ' + str(CURRENCY) + '</b>',
                            'Длина маршрута <b>' + str(row['route_length'] / 1000) + ' км.' + '</b>',
                            'Время поездки <b>' + str(row['route_time']) + ' мин.' + '</b>'
                        ));
                        if (message_id == 0):
                            message = await message.bot.send_message(message.from_user.id, '.')
                            message_id = message.message_id
                            chat_id = message.chat.id
                            pass
                        markupBack = InlineKeyboardMarkup(row_width=2)
                        callbackBackward = 'client-orders_' + str(offset - 1) + '_' + str(message_id) + '_' + str(chat_id)
                        callbackForward = 'client-orders_' + str(offset + 1) + '_' + str(message_id) + '_' + str(chat_id)
                        if (offset + 1) == modelOrdersCn:
                            markupBack.add(InlineKeyboardButton(text=('◀️'), callback_data = callbackBackward))
                        elif offset == 0:
                            markupBack.add(InlineKeyboardButton(text=('▶️'), callback_data = callbackForward))
                        else:
                            markupBack.add(
                                InlineKeyboardButton(text=('◀️'), callback_data = callbackBackward),
                                InlineKeyboardButton(text=('▶️'), callback_data = callbackForward)
                            )
                        markupBack.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client'))
                        await message.bot.edit_message_text(chat_id = chat_id, message_id = message_id, text = text, reply_markup = markupBack)
                        pass
                pass

