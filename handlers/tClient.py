import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from db import BotDB
from config import *
from language import t
from io import BytesIO
from PIL import Image

db = BotDB()

class Passenger:
    def __init__(self):
        pass

    def init(self):
        print('This is a Passenger class')

    async def getClientOrders(self, message, offset, message_id, chat_id):
        if (not db.userGet(message.from_user.id, 'client')):
            await message.bot.send_message(message.from_user.id, t('Client not found'))
        else:
            clientModel = db.userGet(message.from_user.id, 'client')
            if (not clientModel):
                await message.bot.send_message(message.from_user.id, t("Unable to find customer"))
                pass
            else:
                modelOrders = db.get_client_orders_by_one(message.from_user.id, offset)
                modelOrdersCn = len(db.get_client_orders(message.from_user.id))
                if (modelOrdersCn) == 0:
                    await message.bot.send_message(message.from_user.id, t("You haven`t orders"))
                else:
                    for row in modelOrders:
                        try:
                            status = db.statuses[row['status']]
                        except:
                            status = db.statuses['unknown']
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
                        ))
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
    async def rules(self, message):
        caption = '''<b>Для пассажиров</b>
    Бот поможет удобно и недорого заказать такси (частного водителя).

     • Как рассчитывается цена поездки?
    Стоимость за 1км = {rate1KM:d}{currency:s}
    ℹ️ Стоимость поездки рассчитается автоматически и зависит от длины маршрута в километрах (км).
    К примеру стоимость поездки на расстояние {kilometers:d}км составит {amountKM:d}{currency:s} ({kilometers:d}км * {rate1KM:d}{currency:s} = {amountKM:d}{currency:s})

     • Как оплатить поездку?
    Поездка оплачивается наличными напрямую водителю
    ℹ️ Заранее позаботьтесь о наличии разменных денег или спросите у водителя есть ли у него сдача
    ℹ️ поездка должна быть оплачена в сумме не меньшей, чем указано при оформлении заказа. Чаевые водителю приветствуются

     • Как сделать заказ?
    Внимательно следуйте инструкциям бота, когда захотите сделать заказ. Основные этапы формирования заказа описаны ниже:
     1. Укажите ваше Имя, ваш номер телефона ℹ️ указывайте телефон начиная со знака «+», далее только цифры, без скобок и тире
     2. Укажите координаты отправления и координаты назначения, воспользовавшись ОДНИМ из 3-х способов:
      1️⃣ способ - напишите название и отправьте
      2️⃣ способ - выберите название в КАТАЛОГЕ МЕСТ
      3️⃣ способ - укажите координаты на карте через СКРЕПКУ+ЛОКАЦИЯ
     (Как это сделать инфо на скриншоте) к этому тексту
     3. Проверьте информацию о заказе и подтвердите его
     4. Ожидайте когда на ваш заказ будет назначен водитель
     5. Когда водитель будет назначен, вы можете связаться с ним для уточнения деталей поездки
     6. После заказа оцените поездку

     • кто меня повезет?
    Наш бот автоматически назначает свободного водителя, который находится ближе остальных. Бот также учитывает рейтинг водителя, и дает приоритет водителям с более высокими оценками

     • Есть вопросы и пожелания?
    Свяжитесь с техподдержкой бота {adminTg:s}

    👉 Ставьте оценку водителю после каждой поездки
    👉 При заказе убедитесь, что верно указали место отправления и прибытия
    👉 Приглашайте новых водителей в этот бот
    '''
        kilometers = 14
        amountKM = RATE_1_KM * 14
        caption = caption.format(
            rate1KM = RATE_1_KM,
            amountKM = amountKM,
            kilometers = kilometers,
            adminTg = ADMIN_TG,
            currency = CURRENCY
        )
        backClientMenu = InlineKeyboardMarkup(row_width=1)
        backClientMenu.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client'))
        await message.bot.send_message(message.from_user.id, caption)
        bio = BytesIO()
        image = Image.open('rules_1.jpeg')
        image.save(bio, 'JPEG')
        bio.seek(0)
        await message.bot.send_photo(message.from_user.id, bio, reply_markup = backClientMenu)
        pass

