import re, math, time, datetime
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dispatcher import dp
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime, timedelta
from bot import BotDB
from language import t
from config import *
from os.path import exists
import PIL
from PIL import Image
from pathlib import Path
from io import BytesIO
import asyncio
from geopy.distance import geodesic

# sudo apt-get install xclip
import pyperclip

client = {
    'name': '',
    'phone': '',
}
order = {
    'client_id': '',
    'status': '',
    'dt_order': '',
    'amount_client': '',
    'departure_latitude': 0,
    'departure_longitude': 0,
    'destination_latitude': 0,
    'destination_longitude': 0,
}
driver = {
    'name': '',
    'phone': '',
    'car_number': '',
    'status': '',
    'balance': '',
    'wallet': '',
}

var = {
    'locationType': '',
    'orderTimer': False,
    'currentOrder': None,
}

# Данные вводимые с клавиатуры
class FormClient(StatesGroup):
    name = State()
    phone = State()
    amount = State()
class FormDriver(StatesGroup):
    name = State()
    phone = State()
    car_number = State()
    wallet = State()
    balance = State()
data = []
minBalanceAmount = 10




@dp.message_handler(commands=["start", "Back"])
async def start(message: types.Message):
    await startMenu(message)
    x = await getLength(35.155697,	33.897665, 35.253486,	33.899746)
    print(x)
    x = await getLengthV2(35.155697,	33.897665, 35.253486,	33.899746)
    print(x)
    # await setDriverPhone(message)


async def getLengthV2(dept_lt, dept_ln, dest_lt, dest_ln):
    distance = geodesic((dept_lt, dept_ln), (dest_lt, dest_ln)).kilometers
    return f'{distance:.2f}'


async def getLength(dept_lt, dept_ln, dest_lt, dest_ln):
    x1, y1 = (dept_ln), (dept_lt)
    x2, y2 = (dest_ln), (dest_lt)
    y = math.radians(float(y1 + y2) / 2)
    x = math.cos(y)
    n = abs(x1 - x2) * 111000 * x
    n2 = abs(y1 - y2) * 111000
    return float(round(math.sqrt(n * n + n2 * n2)))




async def setLength(message):
    order['route_length'] = await getLength(order['departure_latitude'], order['departure_longitude'], order['destination_latitude'], order['destination_longitude'])
    order['route_time'] = round(order['route_length'] / (40 * 1000) * 60)
    order['amount_client'] = math.floor((order['route_length'] / 1000) * RATE_1_KM)
    pass




async def startMenu(message):
    markup = InlineKeyboardMarkup(row_width=3)
    item1 = InlineKeyboardButton(text=t('I looking for a clients'), callback_data='driver')
    item2 = InlineKeyboardButton(t('I looking for a taxi'), callback_data='client')
    markup.add(item1).add(item2)
    if message.from_user.id == 419839605:
        item3 = InlineKeyboardButton(("Top up balance"), callback_data='drivers')
        markup.add(item3)
    await message.bot.send_message(message.from_user.id, ("Welcome!"), reply_markup = await markupRemove())
    await message.bot.send_message(message.from_user.id, ("Use the menu to get started"), reply_markup = markup)




async def clientProfile(message, client_id):
    modelClient = BotDB.get_client(client_id)
    if (not modelClient):
        await message.bot.send_message(message.from_user.id, t("Create at least one order and we will create your profile automatically"))
    else:
        caption = '\n'.join((
            '<b>Имя</b> ' + str(modelClient['name']),
            '<b>Телефон</b> ' + str(modelClient['phone']),
        ))
        await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML')
    pass




async def driverProfile(message, driver_id):
    modelDriver = BotDB.get_driver(driver_id)
    if (not modelDriver):
        await message.bot.send_message(message.from_user.id, "Can`t do it, begin to /start")
    else:
        Path("merged").mkdir(parents=True, exist_ok=True)
        car = 'cars/' + str(driver_id) + '.jpg';
        driverFileName = 'drivers/' + str(driver_id) + '.jpg';
        fileCarExist = exists(car)
        fileDriverExist = exists(driverFileName)
        statusIcon = str(BotDB.statuses[modelDriver['status']])
        caption = '\n'.join((
            '<b>Имя</b> ' + str(modelDriver['name']),
            '<b>Статус</b> ' + str(statusIcon),
            '<b>Телефон</b> ' + str(modelDriver['phone']),
            '<b>Номер машины</b> ' + str(modelDriver['car_number']),
        ))

        if fileCarExist & fileDriverExist:
            image1 = Image.open(car)
            image2 = Image.open(driverFileName)
            image1 = image1.resize((240, 320))
            image2 = image2.resize((240, 320))
            image1_size = image1.size
            image2_size = image2.size
            merged_image = Image.new(mode='RGB', size=(2*240, 320), color=(250,250,250))
            merged_image.paste(image1,(0,0))
            merged_image.paste(image2,(240,0))
            bio = BytesIO()
            bio.name = 'merged/' + str(driver_id) + '.jpg'
            merged_image.save(bio, 'JPEG')
            bio.seek(0)
            await message.bot.send_photo(message.from_user.id, bio, caption=caption, parse_mode='HTML')
        else:
            await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML')
    pass




# Перехватчик кликов по инлайновой клавиатуре
@dp.callback_query_handler(lambda message:True)
async def inlineClick(message, state: FSMContext):
    if message.data == "client":
        if(not BotDB.client_exists(message.from_user.id)):
            BotDB.add_client(message.from_user.id)
        await menuClient(message)
    elif message.data == 'client-profile':
        await clientProfile(message, message.from_user.id)
    elif message.data == 'make-order':
        order['client_id'] = message.from_user.id
        await setName(message)
    elif message.data == "driver":
        if(not BotDB.driver_exists(message.from_user.id)):
            BotDB.add_driver(message.from_user.id)
        await menuDriver(message)
        pass
    elif message.data == 'driver-profile':
        await driverProfile(message, message.from_user.id)
        pass
    elif message.data == "driver-form":
        async with state.proxy() as data:
            data['dir'] = 'cars/'
            data['savedKey'] = 'carPhotoSaved'
        await setCarPhoto(message)
    elif message.data == 'drivers':
        await getWalletDrivers(message)
    elif message.data == 'carPhotoSaved':
        async with state.proxy() as data:
            data['dir'] = 'drivers/'
            data['savedKey'] = 'driverPhotoSaved'
        await setDriverPhoto(message)
    elif message.data == 'driverPhotoSaved':
        await setDriverName(message)
    elif message.data == 'driverDoneOrder':
        await driverDoneOrder(message)
    elif message.data == 'account':
        driverBalance = (BotDB.get_driver(message.from_user.id))
        if None == driverBalance['balance']:
            driverBalance['balance'] = 0
        localMessage = t('Your balance is {driverBalance:d} usdt, min balance for use bot is {minBalance:d} usdt')
        localMessage = localMessage.format(driverBalance = driverBalance['balance'], minBalance = minBalanceAmount)
        await message.bot.send_message(message.from_user.id, (localMessage))
    elif message.data == 'how-topup-account':
        markupCopy = InlineKeyboardMarkup(row_width=1)
        # markupCopy.add(InlineKeyboardButton(text=t('Copy wallet'), callback_data='copy-wallet'))
        markupCopy.add(InlineKeyboardButton(text=t('Confirm the transfer'), callback_data='confirm-transfer'))
        localMessage = t('To work in the system, you must have at least {minAmount:d} usdt on your account. To replenish the account, you need to transfer the currency to the specified crypto wallet')
        localMessage = localMessage.format(minAmount = minBalanceAmount)
        await message.bot.send_message(message.from_user.id, localMessage)
        await message.bot.send_message(message.from_user.id, WALLET, reply_markup = markupCopy)
    elif message.data == 'copy-wallet':
        pyperclip.copy(WALLET)
        pass
    elif message.data == 'confirm-transfer':
        await setDriverWallet(message)
        pass
    elif message.data == 'orders':
        modelDriver = BotDB.get_driver(message.from_user.id)
        if (not modelDriver):
            await message.bot.send_message(message.from_user.id, "Can`t do it, begin to /start")
        else:
            if modelDriver['balance'] == None:
                modelDriver['balance'] = 0
            if (modelDriver['balance'] < minBalanceAmount):
                localMessage = t("You cant see orders, your balance is less than {minAmount:d} usdt")
                localMessage = localMessage.format(minAmount = minBalanceAmount)
                await message.bot.send_message(message.from_user.id, localMessage)
            elif modelDriver['phone'] == None:
                await message.bot.send_message(message.from_user.id, t('Phone is required, set it in client form'))
            elif modelDriver['status'] == 'offline':
                localMessage = ("You cant see orders, your are offline")
                await message.bot.send_message(message.from_user.id, localMessage)
            elif modelDriver['status'] == 'route':
                localMessage = ("You cant see orders, your are at route")
                await message.bot.send_message(message.from_user.id, localMessage)
            elif modelDriver['status'] == 'online':
                await getActiveOrders(message)
            else:
                await message.bot.send_message(message.from_user.id, ('You have unknown status'))
    elif message.data == 'client-orders':
        await getClientOrders(message)
        pass
    elif 'wallet' in message.data:
        Array = message.data.split('_')
        await setDriverTopupBalance(message, Array[1])
    elif "orderConfirm" in message.data:
        bookOrderArray = message.data.split('_')
        order_id = bookOrderArray[1]
        if BotDB.order_waiting_exists(order_id, 'waiting'):
            modelOrder = BotDB.get_order(order_id)
            if (not modelOrder):
                await message.bot.send_message(message.from_user.id, ("Order not found"))
            else:
                if modelOrder['amount_client'] == None:
                    modelOrder['amount_client'] = 0
            driver = BotDB.get_driver(message.from_user.id)
            if (not driver):
                await message.bot.send_message(message.from_user.id, "Can`t do it, begin to /start")
            else:
                if driver['balance'] == None:
                    driver['balance'] = 0
                if not modelOrder['amount_client']:
                    modelOrder['amount_client'] = 0
                income = int(math.ceil(modelOrder['amount_client'] / 100 * PERCENT) / RATE_1_USDT)
                progressOrder = BotDB.get_order(order_id)
                if (not progressOrder):
                    await message.bot.send_message(message.from_user.id, "Can`t do it, begin to /start")
                else:
                    await message.bot.send_message(message.from_user.id, t("You have taken the order go to the passenger"))
                    try:
                        BotDB.update_driver_status(message.from_user.id, 'route')
                        BotDB.update_order_status(order_id, 'progress')
                        BotDB.update_order_driver_id(order_id, driver['tg_user_id'])
                        BotDB.update_driver_balance(message.from_user.id, int(driver['balance'] - income))
                        if var['orderTimer'] != False:
                            var['orderTimer'].cancel()
                            var['orderTimer'] = False
                        # Only here we take a departure-point to the Driver
                        await message.bot.send_location(message.from_user.id, progressOrder['departure_latitude'], progressOrder['departure_longitude'])
                        markupDoneOrder = types.InlineKeyboardMarkup(row_width=1)
                        markupDoneOrder.add(types.InlineKeyboardButton(text=t('Done current order'), callback_data='driverDoneOrder_' + str(order_id)))
                        await message.bot.send_message(message.from_user.id, t('When you deliver the passenger, please press the button to done the order'), reply_markup = markupDoneOrder)
                    except:
                        await message.bot.send_message(message.from_user.id, t("Order can not be taken"))
        else:
            await message.bot.send_message(message.from_user.id, t("This order cannot be taken, it is already taken"))
    elif 'orderCancel' in message.data:
        Array = message.data.split('_')
        order_id = Array[1]
        if BotDB.order_waiting_exists(order_id, 'waiting'):
            BotDB.driver_order_increment_cancel_cn(message.from_user.id, order_id)
        else:
            await message.bot.send_message(message.from_user.id, ("This order cannot be canceled, it is already taken"))
        pass
    elif 'orderCancelClient' in message.data:
        # switch order to cancel
        # message to client about it
        pass
    elif 'orderWaitingClient' in message.data:
        #  What we doing here?
        pass
    elif message.data == 'switch-online':
        await setDriverLocation(message)
        pass
    elif message.data == 'switch-offline':
        await switchDriverOffline(message)
        pass
    elif message.data == 'departureLocationSaved':
        await setDestination(message)
        pass
    elif message.data == 'destinationLocationSaved':
        await setLength(message)
        await clientRegistered(message)
        pass
    elif message.data == 'driverLocationSaved':
        await switchDriverOnline(message)
    elif "date" in message.data:
        if message.data == 'dateRightNow':
            date = datetime.now()
            pass
        elif message.data == 'dateAfter10min':
            date = datetime.now() + timedelta(minutes=10)
            pass
        elif message.data == 'dateAfter15min':
            date = datetime.now() + timedelta(minutes=15)
            pass
        elif message.data == 'dateIn30min':
            date = datetime.now() + timedelta(minutes=30)
            pass
        elif message.data == 'dateIn1hour':
            date = datetime.now() + timedelta(hours=1)
            pass
        elif message.data == 'dateIn2hours':
            date = datetime.now() + timedelta(hours=2)
            pass
        order['dt_order'] = date.strftime("%Y-%m-%d %H:%M")
        await setPhone(message)
        pass
    elif 'driverDoneOrder' in message.data:
        Array = message.data.split('_')
        order_id = Array[1]
        modelOrder = BotDB.get_order(order_id)
        if (not modelOrder):
            await message.bot.send_message(message.from_user.id, ("Order not found"))
        else:
            try:
                BotDB.update_driver_status(message.from_user.id, 'offline')
                BotDB.update_order_status(order_id, 'done')
            except:
                print("Cant switch order to done")
            await message.bot.send_message(message.from_user.id, t("Order is done"))


async def driverDoneOrder(message):
    try:
        driverId = BotDB.get_driver_id(message.from_user.id)
        if (not driverId):
            await message.bot.send_message(message.from_user.id, ("Driver not found"))
        else:
            modelOrder = BotDB.get_order_progress_by_driver_id(driverId)
            if (not modelOrder):
                await message.bot.send_message(message.from_user.id, ("You haven`t current order"))
            else:
                BotDB.update_driver_status(message.from_user.id, 'offline')
                BotDB.update_order_status(modelOrder['id'], 'done')
                await message.bot.send_message(message.from_user.id, ('Congratulations! You have completed the order. You can go back to online to make a new order'))
    except:
        await message.bot.send_message(message.from_user.id, ("Can`t set done order status"))




async def menuDriver(message):
    markup = InlineKeyboardMarkup(row_width=3)
    item1 = InlineKeyboardButton(text=t('Driver form') + ' 📝', callback_data='driver-form')
    item2 = InlineKeyboardButton(text=t('Account'), callback_data='account')
    item4 = InlineKeyboardButton(text=t('How to top up') + ' ❓', callback_data='how-topup-account')
    item3 = InlineKeyboardButton(text=t('Orders'), callback_data='orders')
    item5 = InlineKeyboardButton(text=t('My profile') + ' 🔖', callback_data='driver-profile')
    item6 = InlineKeyboardButton(text=t("Go online 🟢"), callback_data='switch-online')
    item7 = InlineKeyboardButton(text=t('Go offline 🔴'), callback_data='switch-offline')
    item8 = InlineKeyboardButton(text=t('Back to menu'), callback_data='backToMenu')
    modelDriver = BotDB.get_driver(message.from_user.id)
    if (not modelDriver):
        await message.bot.send_message(message.from_user.id, "Can`t do it, begin to /start")
    else:
        if modelDriver['status'] != None:
            markup.add(item5, item1)
        else:
            markup.add(item1)
        markup.add(item2, item4).add(item6, item7).add(item3)
        markup.add(item8)
        await message.bot.send_message(message.from_user.id, t("You are in the driver menu"), reply_markup = markup)




async def switchDriverOnline(message):
    # await message.bot.send_message(message.from_user.id, 'You need set a current location')
    BotDB.update_driver_status(message.from_user.id, 'online')
    localMessage = 'Вы онлайн. В течении {onlineTime:d} минут Вам будут приходить заказы'.format(onlineTime = round(ONLINE_TIME_SEC/60))
    await message.bot.send_message(message.from_user.id, localMessage)

    # Запуск заявок
    time.sleep(3)
    await getNearWaitingOrder(message)

    # выполнить функцию switchDriverOffline() через onlineTime секунд
    Timer(ONLINE_TIME_SEC, switchDriverOffline, args=message)
    pass




async def getNearWaitingOrder(message):
    modelDriver = BotDB.get_driver(message.from_user.id)
    order = BotDB.get_near_order('waiting', modelDriver['latitude'], modelDriver['longitude'], message.from_user.id)
    await getOrderCard(message, order)
    var['orderTimer'] = Timer(ORDER_REPEAT_TIME_SEC, getNearWaitingOrder, args=message)




async def switchDriverOffline(message):
    modelDriver = BotDB.get_driver(message.from_user.id)
    if not modelDriver:
        print('cant switch to offline')
    else:
        if modelDriver['status'] != 'offline':
            BotDB.update_driver_status(message.from_user.id, 'offline')
            if var['orderTimer'] != False:
                var['orderTimer'].cancel()
                var['orderTimer'] = False
    await message.bot.send_message(message.from_user.id, t("You switch offline. Orders unavailable"), reply_markup = await markupRemove())
    pass




async def getOrderCard(message, order):
    modelDriver = BotDB.get_driver(message.from_user.id)
    distanceToClient = await getLengthV2(
        modelDriver['latitude'],
        modelDriver['longitude'],
        order['departure_latitude'],
        order['departure_longitude']
    )
    markup = InlineKeyboardMarkup(row_width=3)
    item1 = InlineKeyboardButton(text=t('Cancel') + ' ❌', callback_data='orderCancel_' + str(order['order_id']))
    item2 = InlineKeyboardButton(text=t('Confirm') + ' ✅', callback_data='orderConfirm_' + str(order['order_id']))
    markup.add(item1, item2)
    caption = '\n'.join((
        '<b>Заказ №' + str(order['order_id']) + '</b>',
        'Имя <b>' + str(order['name']) + '</b>',
        'Расстояние до клиента, км. <b>' + str(distanceToClient) + ' км' + '</b>',
        'Длина маршрута, км. <b>' + str(order['route_length'] / 1000) + ' км' + '</b>',
        'Сумма, tl. <b>' + str(order['amount_client']) + '</b>',
    ))
    await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML', reply_markup = markup)
async def getOrderCardClient(message, order):
    markup = InlineKeyboardMarkup(row_width=3)
    item1 = InlineKeyboardButton(text=t('Cancel trip') + ' ❌', callback_data='orderCancelClient_' + str(order['order_id']))
    item2 = InlineKeyboardButton(text=t('Waiting driver') + ' ⏳', callback_data='orderWaitingClient_' + str(order['order_id']))
    markup.add(item1, item2)
    caption = '\n'.join((
        '<b>Заказ №' + str(order['order_id']) + '</b>',
        'Имя <b>' + str(order['name']) + '</b>',
        'Расстояние <b>' + str(order['route_length'] / 1000) + ' км' + '</b>',
        'Сумма <b>' + str(order['amount_client']) + ' t.l.</b>',
    ))
    await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML', reply_markup = markup)




async def setCarPhoto(message):
    await message.bot.send_message(message.from_user.id, t("Attach a photo of your car"), reply_markup = await markupRemove())
async def setDriverPhoto(message):
    await message.bot.send_message(message.from_user.id, t("You can attach your photo if you wish"), reply_markup = await markupRemove())
@dp.message_handler(content_types='photo')
async def process_car_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        dir = data['dir']
        savedKey = data['savedKey']
    await message.photo[-1].download(destination_file=dir + str(message.from_user.id) + '.jpg')
    await message.bot.send_message(message.chat.id, t("Do you confirm?"), reply_markup = await inlineConfirm(savedKey))




async def getWalletDrivers(message):
    drivers = BotDB.get_drivers()
    markup = InlineKeyboardMarkup(row_width=3)
    for modelDriver in drivers:
        print(modelDriver)
        item = InlineKeyboardButton(text=modelDriver['tg_user_id'], callback_data='wallet_' + str(modelDriver['wallet']))
        markup.add(item)
    await message.bot.send_message(message.from_user.id, 'Выберите водителя', reply_markup = markup)




async def setDriverTopupBalance(message, wallet):
    driver['wallet'] = wallet
    await FormDriver.balance.set()
    await message.bot.send_message(message.from_user.id, ("Top up driver balance"), reply_markup = await markupRemove())
@dp.message_handler(state=FormDriver.balance)
async def process_driver_deposit_balance(message: types.Message, state: FSMContext):
    if message.text == t('Confirm'):
        await state.finish()
        modelDriver = BotDB.get_driver_by_wallet(driver['wallet'])
        if (not modelDriver):
            await message.bot.send_message(message.from_user.id, ("Wallet not found, you can see right wallet to your profile"), reply_markup = await markupRemove())
        else:
            if modelDriver['balance'] == None:
                modelDriver['balance'] = 0
            newBalance = modelDriver['balance'] + int(driver['balance'])
            BotDB.update_driver_balance(modelDriver['tg_user_id'], newBalance)
            time.sleep(2)
            await message.bot.send_message(message.from_user.id, ("Balance is filled"))
        pass
    else:
        if (message.text.isdigit()):
            match = re.match('^[\d]{1,10}$', message.text)
            if match:
                driver['balance'] = message.text
                await message.bot.send_message(message.from_user.id, ('Do you confirm?'), reply_markup = await standartConfirm())
            else:
                await message.bot.send_message(message.chat.id, t("You can input from 1 to 10 digits"))
        else:
            await message.bot.send_message(message.from_user.id, t("Only digits can be entered"))




async def setDriverPhone(message):
    await FormDriver.phone.set()
    await message.bot.send_message(message.from_user.id, t("Enter phone number?"), reply_markup = types.ReplyKeyboardRemove())
@dp.message_handler(state=FormDriver.phone)
async def process_driver_phone(message: types.Message, state: FSMContext):

    if message.text == t('Confirm'):
        try:
            await state.finish()
            await driverRegistered(message)
            await menuDriver(message)
        except:
            await message.bot.send_message(message.from_user.id, ("We cant create your form"), reply_markup = await markupRemove())
        pass
    else:
        if (message.text.isdigit()):
            match = re.match('^[\d]{11,12}$', message.text)
            if match:
                # async with state.proxy() as data:
                driver['phone'] = message.text
                await message.bot.send_message(message.from_user.id, t('Do you confirm your phone?'), reply_markup = await standartConfirm())
                pass
            else:
                await message.bot.send_message(message.chat.id, t("Number of digits is incorrect"))
        else:
            await message.bot.send_message(message.chat.id, t("Only digits can be entered as a phone number"))




async def setDriverName(message):
    await FormDriver.name.set()
    await message.bot.send_message(message.from_user.id, t("What's your name?"), reply_markup = types.ReplyKeyboardRemove())
@dp.message_handler(state=FormDriver.name)
async def process_driver_name(message: types.Message, state: FSMContext):
    if (message.text == t('Confirm')):
        await state.finish()
        await setDriverCarNumber(message)
    else:
        # async with state.proxy() as data:
        driver['name'] = message.text
        await message.bot.send_message(message.from_user.id, driver['name'] + t(', do you confirm your name?'), reply_markup = await standartConfirm())




async def setDriverCarNumber(message):
    await FormDriver.car_number.set()
    await message.bot.send_message(message.from_user.id, t("What's your car number?"), reply_markup = await markupRemove())
@dp.message_handler(state=FormDriver.car_number)
async def process_driver_car_number(message: types.Message, state: FSMContext):
    if (message.text == t('Confirm')):
        await state.finish()
        await setDriverPhone(message)
    else:
        # async with state.proxy() as data:
        driver['car_number'] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        markup.add(types.KeyboardButton(t('Confirm')))
        await message.bot.send_message(message.from_user.id, t('Do you confirm?'), reply_markup = markup)




async def getActiveOrders(message):
    waitingOrders = BotDB.get_orders(message.from_user.id, 'waiting')
    if len(waitingOrders) == 0:
        await message.bot.send_message(message.from_user.id, ('Has not waiting orders'))
    else:
        for row in waitingOrders:
            text = '\n'.join((
                'Статус <b>' + row['status'] + '</b>',
                'Дата <b>' + str(row['dt_order']) + '</b>',
                'Стоимость <b>' + str(row['amount_client']) + '</b>',
                'Длина маршрута, км. <b>' + str(row['route_length'] / 1000) + '</b>',
                'Время поездки, мин. <b>' + str(row['route_time']) + '</b>'
            ));
            # await message.bot.send_location(message.from_user.id, row['departure_latitude'], row['departure_longitude'])
            await message.bot.send_message(message.from_user.id, text, reply_markup = await bookOrder('bookOrder_' + str(row['id'])))
            pass




async def setDriverWallet(message):
    modelDriver = BotDB.get_driver(message.from_user.id)
    if (not modelDriver):
        await message.bot.send_message(message.from_user.id, t("You need fill the form"))
    else:
        await FormDriver.wallet.set()
        await message.bot.send_message(message.from_user.id, t("Enter the sender's wallet"))
@dp.message_handler(state=FormDriver.wallet)
async def process_driver_wallet(message: types.Message, state: FSMContext):
    if (message.text == t('Confirm')):
        await state.finish()
        BotDB.update_driver_wallet(message.from_user.id, driver['wallet'])
        await message.bot.send_message(message.from_user.id, t('Thank you, we will check the crediting of funds'), reply_markup = await markupRemove())
    else:
        driver['wallet'] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        markup.add(types.KeyboardButton(t('Confirm')))
        await message.bot.send_message(message.from_user.id, t('Confirm entry or correct value'), reply_markup = markup)




async def menuClient(message):
    markup = InlineKeyboardMarkup(row_width=1)
    item10 = InlineKeyboardButton(text=t('Profile'), callback_data='client-profile')
    item20 = InlineKeyboardButton(text=t('Make an order') + ' 🚕', callback_data='make-order')
    # item30 = InlineKeyboardButton(text=t('Free drivers'), callback_data='free-drivers')
    item40 = InlineKeyboardButton(text=t('My orders'), callback_data='client-orders')
    markup.add(item10).add(item20).add(item40)
    await message.bot.send_message(message.from_user.id, t("You are in the client menu"), reply_markup = markup)




async def getClientOrders(message):
    if (not BotDB.client_exists(message.from_user.id)):
        await message.bot.send_message(message.from_user.id, ('Client not found'))
    else:
        client = BotDB.get_client(message.from_user.id)
        if (not client):
            await message.bot.send_message(message.from_user.id, ("Unable to find customer"))
            pass
        else:
            modelOrders = BotDB.get_client_orders(message.from_user.id)
            if len(modelOrders) == 0:
                await message.bot.send_message(message.from_user.id, ("You haven`t orders"))
            else:
                for row in modelOrders:
                    try:
                        status = BotDB.statuses[row['status']]
                    except:
                        status = BotDB.statuses['unknown']
                    if not row['dt_order']:
                        dateFormat = 'Не указана'
                    else:
                        dateFormat = datetime.strptime(row['dt_order'], "%Y-%m-%d %H:%M").strftime("%H:%M %d-%m-%Y")
                    text = '\n'.join((
                        'Имя <b>' + str(client['name']) + '</b>',
                        'Статус <b>' + status + '</b>',
                        'Дата <b>' + str(dateFormat) + '</b>',
                        'Стоимость <b>' + str(row['amount_client']) + '</b>',
                        'Длина маршрута, км. <b>' + str(row['route_length'] / 1000) + '</b>',
                        'Время поездки, мин. <b>' + str(row['route_time']) + '</b>'
                    ));
                    await message.bot.send_message(message.from_user.id, t('Order'))
                    await message.bot.send_message(message.from_user.id, text)
                    if BotDB.get_driver(row['driver_id']):
                        await message.bot.send_message(message.from_user.id, t('Driver'))
                        await driverProfile(message, row['driver_id'])
                    pass
            pass




async def setName(message):
    await FormClient.name.set()
    await message.bot.send_message(message.from_user.id, t("What's your name?"))
@dp.message_handler(state=FormClient.name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Process user name
    """
    if (message.text == t('Confirm')):
        await state.finish()
        await setPhone(message)
        # to Phone()
    else:
        async with state.proxy() as data:
            client['name'] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        markup.add(types.KeyboardButton(t('Confirm')))
        await message.bot.send_message(message.from_user.id, client['name'] + t(', do you confirm your name?'), reply_markup = markup)




# async def setDate(message):
#     markup = InlineKeyboardMarkup(row_width=6)
#     item1 = InlineKeyboardButton(text=t('Now'), callback_data='dateRightNow')
#     item2 = InlineKeyboardButton(text=t('After 10 minutes'), callback_data='dateAfter10min')
#     item3 = InlineKeyboardButton(text=t('After 15 minutes'), callback_data='dateAfter15min')
#     item4 = InlineKeyboardButton(text=t('In 30 minutes'), callback_data='dateIn30min')
#     item5 = InlineKeyboardButton(text=t('In one hour'), callback_data='dateIn1hour')
#     item6 = InlineKeyboardButton(text=t('In 2 hours'), callback_data='dateIn2hours')
#
#     markup.add(item1).add(item2).add(item3,item4,item5,item6)
#     await message.bot.send_message(message.from_user.id, t("What time do you need a taxi?"), reply_markup = markup)



#  Need check via internet
async def setPhone(message):
    await FormClient.phone.set()
    await message.bot.send_message(message.from_user.id, t("Enter phone number?"))
    await message.bot.send_message(message.from_user.id, t("Examples of phone number: +905331234567, +79031234567"), reply_markup = await markupRemove())
@dp.message_handler(state=FormClient.phone)
async def process_phone(message: types.Message, state: FSMContext):

    if message.text == t('Confirm'):
        await state.finish()
        await setDeparture(message)
        # to departure
        pass
    else:
        match = re.match('^[+]{1,1}[\d]{11,12}$', message.text)
        if match:
            async with state.proxy() as data:
                client['phone'] = message.text
            markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
            markup.add(types.KeyboardButton(t('Confirm')))
            await message.bot.send_message(message.from_user.id, t('Do you confirm your phone?'), reply_markup = markup)
            pass
        else:
            await message.bot.send_message(message.chat.id, t("Number of digits is incorrect"))




# async def setAmount(message):
#     await FormClient.amount.set()
#     await message.bot.send_message(message.chat.id, t("How much do you want to pay?"))
#     pass
# @dp.message_handler(state=FormClient.amount)
# async def process_amount(message: types.Message, state: FSMContext):
#     if message.text == t('Confirm'):
#         await state.finish()
#         await message.bot.send_message(message.from_user.id, t("We saved your amount"), reply_markup = await markupRemove())
#         await setDeparture(message)
#         pass
#     else:
#         if (message.text.isdigit()):
#             async with state.proxy() as data:
#                 order['amount_client'] = message.text
#             await message.bot.send_message(message.chat.id, t("Do you confirm your amount?"), reply_markup = await standartConfirm())
#         else:
#             await message.bot.send_message(message.chat.id, t("Only digits can be entered as a amount"))



async def setDriverLocation(message):
    var['locationType'] = 'driverCurLoc'
    await message.bot.send_message(message.from_user.id, t('Set current location'))
    pass
async def setDeparture(message):
    var['locationType'] = 'clientDptLoc'
    await message.bot.send_message(message.from_user.id, t("Set departure location"), reply_markup = await markupRemove())
    pass
async def setDestination(message):
    var['locationType'] = 'clientDstLoc'
    await message.bot.send_message(message.from_user.id, t("Set destination location"), reply_markup = await markupRemove())
    pass
@dp.message_handler(content_types=['location'])
async def process_location(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if var['locationType'] == 'clientDptLoc':
        order['departure_latitude'] = message.location.latitude
        order['departure_longitude'] = message.location.longitude
        markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data='departureLocationSaved'))
    elif var['locationType'] == 'clientDstLoc':
        order['destination_latitude'] = message.location.latitude
        order['destination_longitude'] = message.location.longitude
        markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data='destinationLocationSaved'))
    elif var['locationType'] == 'driverCurLoc':
        BotDB.update_driver_location(message.from_user.id, message.location.latitude, message.location.longitude)
        markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data='driverLocationSaved'))
    else:
        await message.bot.send_message(message.chat.id, ("Sorry cant saved data"))
    await message.bot.send_message(message.chat.id, t("Confirm entry or correct value"), reply_markup = markup)
    pass




# Тимер для Асинхронных методов
class Timer:
    def __init__(self, timeout, callback, args):
        self._timeout = timeout
        self._callback = callback
        self._args = args
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback(self._args)

    def cancel(self):
        self._task.cancel()




async def clientRegistered(message):
    try:
        BotDB.update_client(message.from_user.id, client)
        order['status'] = 'waiting'
        BotDB.create_order(order)
        order['departure_latitude'] = 0
        order['departure_longitude'] = 0
        order['destination_latitude'] = 0
        order['destination_longitude'] = 0

        modelOrder = BotDB.get_last_order()
        await getOrderCardClient(message, modelOrder)

        await message.bot.send_message(message.from_user.id, t("Thank you for an order"))
        time.sleep(2)
        await message.bot.send_message(message.from_user.id, t("We are already looking for drivers for you.."))
    except:
        print('error method clientRegistered(message)')
        await gotoStart(message)
async def driverRegistered(message):
    driver['status'] = 'offline'
    BotDB.update_driver(message.from_user.id, driver)
    time.sleep(2)
    await message.bot.send_message(message.from_user.id, t("We are looking for clients for you already"))



async def gotoStart(message):
    await message.bot.send_message(message.from_user.id, t("Can't do it, start with the /start command"))
async def standartConfirm():
    markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
    markup.add(types.KeyboardButton(t('Confirm')))
    return markup
async def inlineConfirm(callback_data):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data=callback_data))
    return markup
async def markupRemove():
    return types.ReplyKeyboardRemove()
async def bookOrder(callback_data):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text=t('Book an order'), callback_data=callback_data))
    return markup
