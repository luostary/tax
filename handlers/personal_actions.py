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
from datetime import datetime
import PIL
from PIL import Image
from pathlib import Path
from io import BytesIO

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
    'departure_latitude': '',
    'departure_longitude': '',
    'destination_latitude': '',
    'destination_longitude': '',
}
driver = {
    'name': '',
    'phone': '',
    'car_number': '',
    'status': '',
    'balance': '',
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
    # await setDriverPhone(message)




async def setLength(message):
    x1, y1 = order['departure_longitude'], order['departure_latitude']
    x2, y2 = order['destination_longitude'], order['destination_latitude']

    y = math.radians((y1 + y2) / 2)
    x = math.cos(y)
    n = abs(x1 - x2) * 111000 * x
    n2 = abs(y1 - y2) * 111000
    order['route_length'] = round(math.sqrt(n * n + n2 * n2))
    order['route_time'] = round(order['route_length'] / (40 * 1000) * 60)
    pass




async def startMenu(message):
    markup = InlineKeyboardMarkup(row_width=3)
    item1 = InlineKeyboardButton(text=t('I looking for a clients'), callback_data='driver')
    item2 = InlineKeyboardButton(t('I looking for a taxi'), callback_data='client')
    markup.add(item1).add(item2)
    if message.from_user.id == 419839605:
        item3 = InlineKeyboardButton(("Top up balance"), callback_data='driver-topup-balance')
        markup.add(item3)
    await message.bot.send_message(message.from_user.id, t("Welcome! Use the menu to get started."), reply_markup = markup)




# Перехватчик кликов по инлайновой клавиатуре
@dp.callback_query_handler(lambda message:True)
async def inlineClick(message, state: FSMContext):
    if message.data == "client":
        if(not BotDB.client_exists(message.from_user.id)):
            BotDB.add_client(message.from_user.id)
        await menuClient(message)
    elif message.data == 'client-profile':
        modelClient = BotDB.get_client(message.from_user.id)
        if (not modelClient):
            await message.bot.send_message(message.from_user.id, t("We couldn't find your profile"))
        else:
            caption = '\n'.join((
                '<b>Имя</b> ' + str(modelClient['name']),
                '<b>Телефон</b> ' + str(modelClient['phone']),
            ))
            await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML')
    elif message.data == 'make-order':
        order['client_id'] = BotDB.get_client_id(message.from_user.id)
        await setName(message)
    elif message.data == "driver":
        if(not BotDB.driver_exists(message.from_user.id)):
            BotDB.add_driver(message.from_user.id)
        await menuDriver(message)
        pass
    elif message.data == 'driver-profile':
        modelDriver = BotDB.get_driver(message.from_user.id)

        Path("merged").mkdir(parents=True, exist_ok=True)
        car = 'cars/' + str(message.from_user.id) + '.jpg';
        driverFileName = 'drivers/' + str(message.from_user.id) + '.jpg';
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
            bio.name = 'merged/' + str(message.from_user.id) + '.jpg'
            merged_image.save(bio, 'JPEG')
            bio.seek(0)
            await message.bot.send_photo(message.from_user.id, bio, caption=caption, parse_mode='HTML')
        else:
            await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML')
    elif message.data == "driver-form":
        async with state.proxy() as data:
            data['dir'] = 'cars/'
            data['savedKey'] = 'carPhotoSaved'
        await setCarPhoto(message)
    elif message.data == 'driver-topup-balance':
        await setDriverTopupWallet(message)
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
        driver = BotDB.get_driver(message.from_user.id)
        if driver['balance'] == None:
            driver['balance'] = 0
        modelDriver = BotDB.get_driver(message.from_user.id)
        if (driver['balance'] < minBalanceAmount):
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
    elif "bookOrder" in message.data:
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
            if driver['balance'] == None:
                driver['balance'] = 0
            income = int(modelOrder['amount_client'] / 100 * PERCENT)
            progressOrder = BotDB.get_order(order_id)
            await message.bot.send_message(message.from_user.id, t("You have taken the order go to the passenger"))

            try:
                BotDB.update_driver_status(message.from_user.id, 'route')
                BotDB.update_order_status(order_id, 'progress')
                BotDB.update_order_driver_id(order_id, driver['id'])
                BotDB.update_driver_balance(message.from_user.id, int(driver['balance'] - income))
                # Only here we take a departure-point to the Driver
                await message.bot.send_location(message.from_user.id, progressOrder['departure_latitude'], progressOrder['departure_longitude'])
            except:
                await message.bot.send_message(message.from_user.id, t("Order can not be taken"))
        else:
            await message.bot.send_message(message.from_user.id, t("This order cannot be taken, it is already taken"))
    elif message.data == 'switch-online':
        await switchDriverOnline(message)
        pass
    elif message.data == 'switch-offline':
        switchDriverOffline(message)
        pass
    elif message.data == 'departureLocationSaved':
        await setDestination(message)
        pass
    elif message.data == 'destinationLocationSaved':
        await setLength(message)
        await clientRegistered(message)
        pass
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




async def driverDoneOrder(message):
    # try:
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
    # except:
    #     await message.bot.send_message(message.from_user.id, ("Can`t set done order status"))
        # await message.bot.send_message(message.from_user.id, e)




async def menuDriver(message):
    markup = InlineKeyboardMarkup(row_width=3)
    item1 = InlineKeyboardButton(text=t('Driver form') + ' 📝', callback_data='driver-form')
    item2 = InlineKeyboardButton(text=t('Account'), callback_data='account')
    item4 = InlineKeyboardButton(text=t('How to top up an account') + ' ❓', callback_data='how-topup-account')
    item3 = InlineKeyboardButton(text=t('Orders'), callback_data='orders')
    item5 = InlineKeyboardButton(text=t('My profile') + ' 🔖', callback_data='driver-profile')
    item6 = InlineKeyboardButton(text=('Go online 🟢 30 minutes'), callback_data='switch-online')
    item7 = InlineKeyboardButton(text=('Go offline 🔴'), callback_data='switch-offline')
    item8 = InlineKeyboardButton(text=t('Done current order'), callback_data='driverDoneOrder')
    modelDriver = BotDB.get_driver(message.from_user.id)
    if modelDriver['status'] != None:
        markup.add(item5, item1)
    else:
        markup.add(item1)
    markup.add(item2, item4).add(item6, item7).add(item3)
    markup.add(item8)
    await message.bot.send_message(message.from_user.id, t("You are in the driver menu"), reply_markup = markup)




from threading import Timer
async def switchDriverOnline(message):
    onlineTime = 600
    BotDB.update_driver_status(message.from_user.id, 'online')
    localMessage = 'Вы онлайн. В течении {onlineTime:d} минут Вам будут приходить заказы'.format(onlineTime = round(onlineTime/60))
    await message.bot.send_message(message.from_user.id, localMessage)
    # выполнить функцию switchDriverOffline() через onlineTime секунд
    Timer(onlineTime, switchDriverOffline, args=(message,)).start()
    pass




def switchDriverOffline(message):
    BotDB.update_driver_status(message.from_user.id, 'offline')
    pass




async def setCarPhoto(message):
    await message.bot.send_message(message.from_user.id, t("Attach a photo of your car"))
async def setDriverPhoto(message):
    await message.bot.send_message(message.from_user.id, t("You can attach your photo if you wish"))
@dp.message_handler(content_types='photo')
async def process_car_photo(message: types.Message, state: FSMContext):
    print(1)
    async with state.proxy() as data:
        dir = data['dir']
        savedKey = data['savedKey']
    await message.photo[-1].download(destination_file=dir + str(message.from_user.id) + '.jpg')
    print(message.photo[-1])
    await message.bot.send_message(message.chat.id, t("Do you confirm?"), reply_markup = await inlineConfirm(savedKey))




async def setDriverTopupWallet(message):
    await FormDriver.wallet.set()
    await message.bot.send_message(message.from_user.id, ("Input wallet"), reply_markup = await markupRemove())
@dp.message_handler(state=FormDriver.wallet)
async def process_driver_deposit_wallet(message: types.Message, state: FSMContext):
    if (message.text == t('Confirm')):
        await state.finish()
        await setDriverTopupBalance(message)
    else:
        driver['wallet'] = message.text
        await message.bot.send_message(message.from_user.id, ('Do you confirm?'), reply_markup = await standartConfirm())




async def setDriverTopupBalance(message):
    await FormDriver.balance.set()
    await message.bot.send_message(message.from_user.id, ("Top up driver balance"))
@dp.message_handler(state=FormDriver.balance)
async def process_driver_deposit_balance(message: types.Message, state: FSMContext):
    if message.text == t('Confirm'):
        await state.finish()
        modelDriver = BotDB.get_driver_by_wallet(driver['wallet'])
        if (not modelDriver):
            await message.bot.send_message(message.from_user.id, ("Driver not found"))
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
        await state.finish()
        await driverRegistered(message)
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
    await message.bot.send_message(message.from_user.id, t("What's your car number?"))
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
    await FormDriver.wallet.set()
    await message.bot.send_message(message.from_user.id, t("Enter the sender's wallet"))
@dp.message_handler(state=FormDriver.wallet)
async def process_driver_wallet(message: types.Message, state: FSMContext):
    if (message.text == t('Confirm')):
        await state.finish()
        BotDB.update_driver_wallet(message.from_user.id, driver['wallet'])
        print(driver)
        await message.bot.send_message(message.from_user.id, t('Thank you, we will check the crediting of funds'), reply_markup = await markupRemove())
    else:
        driver['wallet'] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        markup.add(types.KeyboardButton(t('Confirm')))
        await message.bot.send_message(message.from_user.id, t('Confirm entry or correct value'), reply_markup = markup)




async def menuClient(message):
    markup = InlineKeyboardMarkup(row_width=1)
    item10 = InlineKeyboardButton(text=t('Profile'), callback_data='client-profile')
    item20 = InlineKeyboardButton(text=t('Make an order'), callback_data='make-order')
    item30 = InlineKeyboardButton(text=t('Free drivers'), callback_data='free-drivers')
    item40 = InlineKeyboardButton(text=t('My orders'), callback_data='client-orders')
    markup.add(item10).add(item20).add(item30).add(item40)
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
            modelOrders = BotDB.get_client_orders(client['id'])
            if len(modelOrders) == 0:
                await message.bot.send_message(message.from_user.id, ("You haven`t orders"))
            else:
                for row in modelOrders:
                    try:
                        status = BotDB.statuses[row['status']]
                    except:
                        status = BotDB.statuses['unknown']
                    dateFormat = datetime.strptime(row['dt_order'], "%Y-%m-%d %H:%M").strftime("%H:%M %d-%m-%Y")
                    text = '\n'.join((
                        'Имя <b>' + str(client['name']) + '</b>',
                        'Статус <b>' + status + '</b>',
                        'Дата <b>' + str(dateFormat) + '</b>',
                        'Стоимость <b>' + str(row['amount_client']) + '</b>',
                        'Длина маршрута, км. <b>' + str(row['route_length'] / 1000) + '</b>',
                        'Время поездки, мин. <b>' + str(row['route_time']) + '</b>'
                    ));
                    await message.bot.send_message(message.from_user.id, text)
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
        await message.bot.send_message(message.from_user.id, t("We saved your name"), reply_markup = await markupRemove())
        await setDate(message)
    else:
        async with state.proxy() as data:
            client['name'] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        markup.add(types.KeyboardButton(t('Confirm')))
        await message.bot.send_message(message.from_user.id, client['name'] + t(', do you confirm your name?'), reply_markup = markup)




async def setDate(message):
    markup = InlineKeyboardMarkup(row_width=6)
    item1 = InlineKeyboardButton(text=t('Now'), callback_data='dateRightNow')
    item2 = InlineKeyboardButton(text=t('After 10 minutes'), callback_data='dateAfter10min')
    item3 = InlineKeyboardButton(text=t('After 15 minutes'), callback_data='dateAfter15min')
    item4 = InlineKeyboardButton(text=t('In 30 minutes'), callback_data='dateIn30min')
    item5 = InlineKeyboardButton(text=t('In one hour'), callback_data='dateIn1hour')
    item6 = InlineKeyboardButton(text=t('In 2 hours'), callback_data='dateIn2hours')

    markup.add(item1).add(item2).add(item3,item4,item5,item6)
    await message.bot.send_message(message.from_user.id, t("What time do you need a taxi?"), reply_markup = markup)




async def setPhone(message):
    await FormClient.phone.set()
    await message.bot.send_message(message.from_user.id, t("Enter phone number?"))
@dp.message_handler(state=FormClient.phone)
async def process_phone(message: types.Message, state: FSMContext):

    if message.text == t('Confirm'):
        await state.finish()
        await message.bot.send_message(message.from_user.id, t("We saved your phone"), reply_markup = await markupRemove())
        await setAmount(message)
        pass
    else:
        if (message.text.isdigit()):
            match = re.match('^[\d]{11,12}$', message.text)
            if match:
                async with state.proxy() as data:
                    client['phone'] = message.text
                markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
                markup.add(types.KeyboardButton(t('Confirm')))
                await message.bot.send_message(message.from_user.id, t('Do you confirm your phone?'), reply_markup = markup)
                pass
            else:
                await message.bot.send_message(message.chat.id, t("Number of digits is incorrect"))
        else:
            await message.bot.send_message(message.chat.id, t("Only digits can be entered as a phone number"))




async def setAmount(message):
    await FormClient.amount.set()
    await message.bot.send_message(message.chat.id, t("How much do you want to pay?"))
    pass
@dp.message_handler(state=FormClient.amount)
async def process_amount(message: types.Message, state: FSMContext):
    if message.text == t('Confirm'):
        await state.finish()
        await message.bot.send_message(message.from_user.id, t("We saved your amount"), reply_markup = await markupRemove())
        await setDeparture(message)
        pass
    else:
        if (message.text.isdigit()):
            async with state.proxy() as data:
                order['amount_client'] = message.text
            await message.bot.send_message(message.chat.id, t("Do you confirm your amount?"), reply_markup = await standartConfirm())
        else:
            await message.bot.send_message(message.chat.id, t("Only digits can be entered as a amount"))




async def setDeparture(message):
    await message.bot.send_message(message.from_user.id, t("Set departure location"))
    pass
async def setDestination(message):
    await message.bot.send_message(message.from_user.id, t("Set destination location"))
    pass
@dp.message_handler(content_types=['location'])
async def process_location(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if order['departure_latitude'] == '':
        order['departure_latitude'] = message.location.latitude
        order['departure_longitude'] = message.location.longitude
        markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data='departureLocationSaved'))
    else:
        order['destination_latitude'] = message.location.latitude
        order['destination_longitude'] = message.location.longitude
        markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data='destinationLocationSaved'))
    await message.bot.send_message(message.chat.id, t("Confirm entry or correct value"), reply_markup = markup)
    pass



async def clientRegistered(message):
    BotDB.update_client(message.from_user.id, client)
    order['status'] = 'waiting'
    BotDB.create_order(order)
    await message.bot.send_message(message.from_user.id, t("Thank you for an order"))
    time.sleep(2)
    await message.bot.send_message(message.from_user.id, t("we are already looking for drivers for you..."))
    print(client)
    print(order)
async def driverRegistered(message):
    driver['status'] = 'offline'
    BotDB.update_driver(message.from_user.id, driver)
    time.sleep(2)
    await message.bot.send_message(message.from_user.id, t("We are looking for clients for you already"))
    print(driver)




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
