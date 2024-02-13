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
import json
import pprint
import googlemaps
import qrcode
from . import tClient

# sudo apt-get install xclip
import pyperclip

# Данные вводимые с клавиатуры
class FormClient(StatesGroup):
    name = State()
    phone = State()
class FormDriver(StatesGroup):
    name = State()
    phone = State()
    car_number = State()
    wallet = State()
    balance = State()
minBalanceAmount = MIN_BALANCE_AMOUNT

PHONE_MASK = '^[+]{1,1}[\d]{11,12}$'

# Подключаем класс для работы с пассажиром
client = tClient.Passenger()

@dp.message_handler(commands=["start", "Back"], state='*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()

    if(not BotDB.driver_exists(message.from_user.id)):
        BotDB.add_driver(message.from_user.id, message.from_user.first_name)
    if(not BotDB.client_exists(message.from_user.id)):
        BotDB.add_client(message.from_user.id, message.from_user.first_name)

    await addReferer(message)

    await startMenu(message)
    # await setDriverPhone(message)

#return in kilometers
# deprecated
async def getLengthV2(dept_lt, dept_ln, dest_lt, dest_ln):
    distance = geodesic((dept_lt, dept_ln), (dest_lt, dest_ln)).kilometers
    return f'{distance:.2f}'

#return in meters
# deprecated
async def getLength(dept_lt, dept_ln, dest_lt, dest_ln):
    x1, y1 = (dept_lt), (dept_ln)
    x2, y2 = (dest_lt), (dest_ln)
    y = math.radians(float(y1 + y2) / 2)
    x = math.cos(y)
    n = abs(x1 - x2) * 111000 * x
    n2 = abs(y1 - y2) * 111000
    return float(round(math.sqrt(n * n + n2 * n2)))




async def setLength(message, orderData):
    orderLocal = {}
    gdata = await getGoogleData(orderData)
    orderLocal['route_length'] = gdata['distance']['value']
    orderLocal['route_time'] = float(gdata['duration']['value'] / 60)
    orderLocal['amount_client'] = math.ceil((orderLocal['route_length'] / 1000) * RATE_1_KM)
    if orderLocal['amount_client'] < MIN_AMOUNT:
        orderLocal['amount_client'] = MIN_AMOUNT
    return orderLocal
    pass




async def startMenu(message):
    markup = InlineKeyboardMarkup(row_width=3)
    item10 = InlineKeyboardButton(text=t('I looking for a clients'), callback_data='driver')
    item20 = InlineKeyboardButton(t('I looking for a taxi'), callback_data='client')
    item30 = InlineKeyboardButton(('Рассказать о нас другу 👍'), callback_data='inviteLink')
    markup.add(item10).add(item20).add(item30)
    if message.from_user.id in [5615867597, 419839605]:
        markup.add(InlineKeyboardButton(("Показать статистику"), callback_data='admin-short-statistic'))
        markup.add(InlineKeyboardButton(("Пополнить баланс"), callback_data='drivers'))
    if message.from_user.id == 419839605:
        markup.add(InlineKeyboardButton(("Предложить зарегистрироваться В."), callback_data='driver-incentive-fill-form'))
        markup.add(InlineKeyboardButton(text=('Coding') + ' 💻', callback_data='test'))
    await message.bot.send_message(message.from_user.id, t("Welcome!"), reply_markup = await markupRemove())
    await message.bot.send_message(message.from_user.id, t("Use the menu to get started"), reply_markup = markup)




async def clientProfile(message, client_id):
    modelClient = BotDB.get_client(client_id)
    if (not modelClient):
        await message.bot.send_message(message.from_user.id, t("Create at least one order and we will create your profile automatically"))
    else:
        caption = '\n'.join((
            '<b>Имя</b> ' + str(modelClient['name']),
            '<b>Телефон</b> ' + str(modelClient['phone']),
        ))
        markupBack = InlineKeyboardMarkup(row_width=1)
        markupBack.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client'))
        await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML', reply_markup = markupBack)
    pass





# Перехватчик кликов по инлайновой клавиатуре
@dp.callback_query_handler(lambda message:True, state='*')
async def inlineClick(message, state: FSMContext):
    if message.data == "client":
        await menuClient(message)
    elif message.data == 'back':
        await state.finish()
        await startMenu(message)
    elif message.data == 'inviteLink':
        await inviteLink(message)
    elif message.data == 'test':
        await testFunction(message)
    elif message.data == 'client-rules':
        await clientRules(message)
    elif message.data == 'driver-rules':
        await driverRules(message)
    elif message.data == 'client-profile':
        await clientProfile(message, message.from_user.id)
    elif message.data == 'admin-short-statistic':
        await shortStatistic(message)
    elif message.data == 'driver-incentive-fill-form':
        await incentiveDriverFillForm(message)
    elif message.data == 'make-order':
        if not ALLOW_MANY_ORDERS:
            modelOrders = BotDB.get_waiting_orders_by_client_id(message.from_user.id)
            if (modelOrders):
                modelOrder = BotDB.get_waiting_order_by_client_id(message.from_user.id)
                await menuClient(message)
                await message.bot.send_message(message.from_user.id, 'У Вас имеется текущий заказ')
                await getOrderCardClient(message, modelOrder, True)
                return
        print(message.from_user.id)
        BotDB.update_client_tg_username(message.from_user.id, message.from_user.username)
        await setName(message, state)
    elif message.data == 'clientNameSaved':
        await state.finish()
        await setPhone(message)
    elif message.data == 'clientPhoneSaved':
        await state.finish()
        await setDeparture(message, state)
    elif message.data == "driver":
        await menuDriver(message)
        pass
    elif message.data == 'driver-profile':
        await driverProfile(message, message.from_user.id, message.from_user.id, True, True)
        pass
    elif message.data == "driver-form":
        await setCarPhoto(message, state)
    elif message.data == 'drivers':
        await getWalletDrivers(message)
    elif message.data == 'carPhotoSaved':
        async with state.proxy() as data:
            dMessage = data['dMessage']
            pass
        # await deleteMessage(message, dMessage)
        await setDriverPhoto(message, state)
    elif message.data == 'driverCarNumberSaved':
        await state.finish()
        await setDriverPhone(message)
    elif message.data == 'driverNameSaved':
        await setDriverCarNumber(message)
    elif message.data == 'driverPhoneSaved':
        await menuDriver(message)
        try:
            await driverRegistered(message, state)
        except:
            await message.bot.send_message(message.from_user.id, t("We can`t create your form"), reply_markup = await markupRemove())
        pass
    elif message.data in ['driverPhotoSaved', 'driverPhotoMissed']:
        await setDriverName(message)
    elif message.data == 'driverDoneOrder':
        await driverDoneOrder(message)
    elif message.data == 'driverTopupBalanceConfirm':
        async with state.proxy() as data:
            localWallet = (data['wallet'])
            localBalance = int(data['changeBalance'])
        driverModel = BotDB.get_driver_by_wallet(localWallet)
        if (not driverModel):
            await message.bot.send_message(message.from_user.id, t("Wallet not found, you can see right wallet to your profile"), reply_markup = await markupRemove())
        else:
            if driverModel['balance'] == None:
                driverModel['balance'] = 0
            newBalance = driverModel['balance'] + localBalance
            BotDB.update_driver_balance(driverModel['tg_user_id'], newBalance)
            time.sleep(2)
            await message.bot.send_message(message.from_user.id, t("Balance is filled"))

            caption = ''
            if driverModel['name']:
                caption = driverModel['name'] + ', '
            caption += "Ваш баланс пополнен на " + str(localBalance) + " usdt"
            await message.bot.send_message(driverModel['tg_user_id'], caption)
        await state.finish()
        pass
    elif message.data == 'account':
        driverBalance = (BotDB.get_driver(message.from_user.id))
        if None == driverBalance['balance']:
            driverBalance['balance'] = 0
        localMessage = t('Your balance is {driverBalance:d} usdt, min balance for use bot is {minBalance:d} usdt')
        localMessage = localMessage.format(driverBalance = driverBalance['balance'], minBalance = minBalanceAmount)
        markupBack = InlineKeyboardMarkup(row_width=1)
        markupBack.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='driver'))
        await message.bot.send_message(message.from_user.id, (localMessage), reply_markup = markupBack)
    elif message.data == 'how-topup-account':
        markupCopy = InlineKeyboardMarkup(row_width=1)
        # markupCopy.add(InlineKeyboardButton(text=t('Copy wallet'), callback_data='copy-wallet'))
        markupCopy.add(InlineKeyboardButton(text=t('Confirm the transfer'), callback_data='confirm-transfer'))
        markupCopy.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='driver'))
        localMessage = t('To work in the system, you must have at least {minAmount:d} usdt on your account. To replenish the account, you need to transfer the currency to the specified crypto wallet. After the payment has been made Confirm the transfer with the button')
        localMessage = localMessage.format(minAmount = minBalanceAmount)

        data = WALLET
        qr = qrcode.make(data)
        qr.save('merged/wallet-qr-code.jpg')
        image = Image.open('merged/wallet-qr-code.jpg')
        bio = BytesIO()
        image.save(bio, 'JPEG')
        bio.seek(0)
        qrMsg = 'Если вы пользуетесь услугами обменного пункта - покажите кассиру QR-код кошелька'
        walletMsg = 'Наш криптокошелек: \n' + '<b>' + WALLET + '</b>'
        caption = localMessage + '\n\n' + walletMsg + '\n\n' + qrMsg
        await message.bot.send_photo(message.from_user.id, bio, caption = caption, parse_mode='HTML', reply_markup = markupCopy)
    elif message.data == 'copy-wallet':
        pyperclip.copy(WALLET)
        pass
    elif message.data == 'confirm-transfer':
        await setDriverWallet(message)
        pass
    elif message.data == 'driver-done-orders':
        driverModel = BotDB.get_driver(message.from_user.id)
        if (not driverModel):
            print('can`t get driver from db')
        else:
            if driverModel['balance'] == None:
                driverModel['balance'] = 0
            if driverModel['phone'] == None:
                await message.bot.send_message(message.from_user.id, t('Phone is required, set it in client form'))
            elif driverModel['status'] == 'offline':
                await getDriverDoneOrders(message)
            elif driverModel['status'] == 'route':
                localMessage = t("You can`t see orders, your are at route")
                await message.bot.send_message(message.from_user.id, localMessage)
            elif driverModel['status'] == 'online':
                localMessage = t("You can`t see orders, your are online")
                await message.bot.send_message(message.from_user.id, localMessage)
            else:
                await message.bot.send_message(message.from_user.id, t('You have unknown status'))
    elif 'catalog_' in message.data:
        Array = message.data.split('_')
        await getCategories(message, int(Array[1]), state)
    elif 'client-orders' in message.data:
        Array = message.data.split('_')
        await client.getClientOrders(message, int(Array[1]), int(Array[2]), int(Array[3]))
        pass
    elif 'wallet' in message.data:
        Array = message.data.split('_')
        await setDriverTopupBalance(message, Array[1], state)
    elif "orderConfirm" in message.data:
        bookOrderArray = message.data.split('_')
        order_id = bookOrderArray[1]
        if BotDB.order_waiting_exists(order_id, 'waiting'):
            modelOrder = BotDB.get_order(order_id)
            if (not modelOrder):
                await message.bot.send_message(message.from_user.id, t("Order not found"))
            else:
                if modelOrder['amount_client'] == None:
                    modelOrder['amount_client'] = 0
            driverModel = BotDB.get_driver(message.from_user.id)
            if (not driverModel):
                await message.bot.send_message(message.from_user.id, "Can`t do it, begin to /start")
            else:
                if driverModel['balance'] == None:
                    driverModel['balance'] = 0
                if not modelOrder['amount_client']:
                    modelOrder['amount_client'] = 0
                income = int(math.ceil((modelOrder['amount_client'] / 100 * PERCENT) / RATE_1_USDT))
                progressOrder = BotDB.get_order(order_id)
                if (not progressOrder):
                    await message.bot.send_message(message.from_user.id, "Can`t do it, begin to /start")
                else:
                    try:
                        BotDB.update_driver_status(message.from_user.id, 'route')
                        BotDB.update_order_status(order_id, 'progress')
                        progressOrder = BotDB.get_order(order_id)
                        BotDB.update_order_driver_id(order_id, driverModel['tg_user_id'])
                        BotDB.update_driver_balance(message.from_user.id, int(driverModel['balance'] - income))

                        await message.bot.send_message(message.from_user.id, t("You have taken the order"))
                        await getOrderCard(message, message.from_user.id, progressOrder, False)

                        await message.bot.send_message(message.from_user.id, t("Departure here"))
                        # Give departure-point location
                        await message.bot.send_location(message.from_user.id, progressOrder['departure_latitude'], progressOrder['departure_longitude'])
                        # Give destination-point location
                        await message.bot.send_message(message.from_user.id, t("Destination here"))
                        await message.bot.send_location(message.from_user.id, progressOrder['destination_latitude'], progressOrder['destination_longitude'])
                        markupDoneOrder = types.InlineKeyboardMarkup(row_width=1)
                        markupDoneOrder.add(types.InlineKeyboardButton(text=t('Done current order'), callback_data='driverDoneOrder_' + str(order_id)))
                        await message.bot.send_message(message.from_user.id, t('When you deliver the passenger, please press the button to done the order'), reply_markup = markupDoneOrder)

                        modelOrder = BotDB.get_order(order_id)
                        await sendClientNotification(message, modelOrder)
                    except:
                        await message.bot.send_message(message.from_user.id, t("Order can not be taken"))
        else:
            await message.bot.send_message(message.from_user.id, t("This order cannot be taken, it is not active"))
    elif 'orderCancel_' in message.data:
        Array = message.data.split('_')
        order_id = Array[1]
        if BotDB.order_waiting_exists(order_id, 'waiting'):
            if (not BotDB.driver_order_exists(message.from_user.id, order_id)):
                BotDB.driver_order_create(message.from_user.id, order_id)
            BotDB.driver_order_increment_cancel_cn(message.from_user.id, order_id)
            await message.bot.send_message(message.from_user.id, t("Order is cancel"))
        else:
            await message.bot.send_message(message.from_user.id, t("This order cannot be canceled, it is not active"))
        pass
    elif 'orderCancelClient_' in message.data:
        # switch order to cancel
        Array = message.data.split('_')
        order_id = Array[1]
        modelOrder = BotDB.get_order(order_id)
        if modelOrder['status'] == 'cancel':
            await message.bot.send_message(message.from_user.id, ("Заказ №" + str(modelOrder['id']) + " уже отменен ранее"))
            return
        BotDB.update_order_status(order_id, 'cancel')

        # Cancel fee begin
        if (modelOrder['driver_id']):
            driverModel = BotDB.get_driver(modelOrder['driver_id'])
            driver_id = driverModel['tg_user_id']
            income = int(math.ceil((modelOrder['amount_client'] / 100 * PERCENT) / RATE_1_USDT))
            try:
                BotDB.update_driver_status(driver_id, 'online')
    #            BotDB.update_order_driver_id(order_id, None)
                BotDB.update_driver_balance(driver_id, int(driverModel['balance'] + income))
            except:
                await message.bot.send_message(5615867597, ("Водителю " + driverModel['tg_user_id'] + " (@" + driverModel['tg_username'] + ") не удалось вернуть комиссию " + str(income) + " USDT в автоматическом режиме, необходимо вернуть вручную"))
                pass
        # Cancel fee end


        # message to client about it
        await message.bot.send_message(message.from_user.id, t("Order is cancel"))
        await menuClient(message)
        pass
    elif 'orderWaitingClient_' in message.data:
        #  What we doing here?
        Array = message.data.split('_')
        order_id = Array[1]
        BotDB.update_order_status(order_id, 'waiting')
        await clientRegistered(message)

        # Запускаем таймер для клиента
        message.data = order_id
        await timerForClient(message)


        await message.bot.send_message(message.from_user.id, ("Если не готовы ждать - вы можете отменить поездку"))
        modelOrder = BotDB.get_order(order_id)
        await getOrderCardClient(message, modelOrder, cancel = True, confirm = False)
        pass
    elif message.data == 'switch-online':
        await menuDriver(message)
        driverModel = BotDB.get_driver(message.from_user.id)
        modelOrder = BotDB.get_order_waiting_by_driver_id(message.from_user.id)
        if (not driverModel):
            print('can`t get driver from db')
        else:
            if driverModel['balance'] == None:
                driverModel['balance'] = 0
            if (driverModel['balance'] < minBalanceAmount):
                localMessage = t("You can`t switch to online, your balance is less than {minAmount:d} usdt")
                localMessage = localMessage.format(minAmount = minBalanceAmount)
                await message.bot.send_message(message.from_user.id, localMessage)
            elif driverModel['phone'] == None:
                await message.bot.send_message(message.from_user.id, t('Phone is required, set it in client form'))
            elif modelOrder:
                # Не даем переключаться в онлайн, если у водителя уже есть waiting-заказ
                await message.bot.send_message(message.from_user.id, t('You have active order'))
                await getOrderCard(message, message.from_user.id, modelOrder, True)
            elif driverModel['status'] == 'route':
                modelOrder = BotDB.get_order_progress_by_driver_id(message.from_user.id)
                if modelOrder:
                    localMessage = t("You cannot switch to online, you must complete the route")
                    await message.bot.send_message(message.from_user.id, localMessage)

                    # Give destination-point location
                    await message.bot.send_message(message.from_user.id, ("Доставить клиента сюда"))
                    await message.bot.send_location(message.from_user.id, modelOrder['destination_latitude'], modelOrder['destination_longitude'])

                    markupDoneOrder = types.InlineKeyboardMarkup(row_width=1)
                    markupDoneOrder.add(types.InlineKeyboardButton(text=t('Done current order'), callback_data='driverDoneOrder_' + str(modelOrder['id'])))
                    await message.bot.send_message(message.from_user.id, t('When you deliver the passenger, please press the button to done the order'), parse_mode='HTML', reply_markup = markupDoneOrder)

            elif driverModel['status'] == 'online':
                localMessage = t("You are online, already")
                await message.bot.send_message(message.from_user.id, localMessage)
            elif driverModel['status'] == 'offline':
                BotDB.update_driver_tg_username(message.from_user.id, message.from_user.username)
                await setDriverLocation(message, state)
            else:
                await message.bot.send_message(message.from_user.id, t('You have unknown status'))
        pass
    elif message.data == 'switch-offline':
        await switchDriverOffline(message)
        pass


    #Подтверждение локации отправления клиентом
    elif message.data == 'departureLocationSaved':
        await setDestination(message, state)
        pass
    elif 'departureLocationSavedByLocId_' in message.data:
        Array = message.data.split('_')
        location_id = int(Array[1])
        #Сохранение координатов
        locationModel = BotDB.get_location_by_id(location_id)
        async with state.proxy() as data:
            data['departure_latitude'] = float(locationModel['lat'])
            data['departure_longitude'] = float(locationModel['long'])
            pass
        await setDestination(message, state)
        pass


    #Подтверждение локации назначения клиентом
    elif message.data == 'destinationLocationSaved':
        await destinationLocationSaved(message, state)
        pass
    elif 'destinationLocationSavedByLocId_' in message.data:
        Array = message.data.split('_')
        location_id = int(Array[1])
        #Сохранение координатов
        locationModel = BotDB.get_location_by_id(location_id)
        async with state.proxy() as data:
            data['destination_latitude'] = float(locationModel['lat'])
            data['destination_longitude'] = float(locationModel['long'])
            pass
        await destinationLocationSaved(message, state)
        pass


    #Подтверждение локации водителем
    elif message.data == 'driverLocationSaved':
        await switchDriverOnline(message)
    elif 'driverLocationSavedByLocId_' in message.data:
        Array = message.data.split('_')
        location_id = int(Array[1])
        #Сохранение координатов
        locationModel = BotDB.get_location_by_id(location_id)
        BotDB.update_driver_location(message.from_user.id, locationModel['lat'], locationModel['long'])
        await switchDriverOnline(message, state)
        pass


    elif 'driverDoneOrder_' in message.data or 'clientDoneOrder_' in message.data:
        Array = message.data.split('_')
        order_id = Array[1]
        modelOrder = BotDB.get_order(order_id)
        if (not modelOrder):
            await message.bot.send_message(message.from_user.id, t("Order not found"))
        elif modelOrder['status'] == 'done':
            await message.bot.send_message(message.from_user.id, t("Order is close already"))
            return;
        else:
            try:
                BotDB.update_order_status(order_id, 'done')
                await message.bot.send_message(message.from_user.id, t("Order is done"))

                clientBack = InlineKeyboardMarkup(row_width=1)
                clientBack.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client'))
                driverBack = InlineKeyboardMarkup(row_width=1)
                driverBack.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='driver'))

                if 'driverDoneOrder_' in message.data:
                    await message.bot.send_message(modelOrder['client_id'], ("Заказ завершен водителем"), reply_markup = clientBack)
                elif 'clientDoneOrder_' in message.data:
                    await message.bot.send_message(modelOrder['driver_id'], ("Заказ завершен клиентом"), reply_markup = driverBack)

                orderProgressModel = BotDB.get_order_progress_by_driver_id(modelOrder['driver_id'])
                if orderProgressModel:
                    BotDB.update_driver_status(message.from_user.id, 'route')
                else:
                    BotDB.update_driver_status(message.from_user.id, 'offline')
            except:
                print("can`t switch order to done")

            # Если инициатор завершения заявки клиент, то ему выводим рекламный блок
            time.sleep(2)
            await getWikiBotInfo(message, modelOrder['client_id'])
            pass




async def timerForClient(message, onTimer = True):
    order_id = message.data
    orderModel = BotDB.get_order(order_id)
    if orderModel['status'] != 'waiting':
        onTimer = False
    if onTimer:
        # По задумке цикл должен работать раз в минуту
        driverModel = BotDB.get_near_driver(orderModel['departure_latitude'], orderModel['departure_longitude'], orderModel['id'])
        if not driverModel:
            await message.bot.send_message(message.from_user.id, 'На линии пока нет водителей')
            return
        await getOrderCard(message, driverModel['tg_user_id'], orderModel, True)

        Timer(ORDER_REPEAT_TIME_SEC, timerForClient, args=message)
        if (not BotDB.driver_order_exists(driverModel['tg_user_id'], order_id)):
            BotDB.driver_order_create(driverModel['tg_user_id'], order_id)
        BotDB.driver_order_increment_cancel_cn(driverModel['tg_user_id'], order_id)
        clientModel = BotDB.get_client(orderModel['client_id'])

        modelDriverOrder = BotDB.get_driver_order(driverModel['tg_user_id'], order_id)
        if modelDriverOrder['driver_cancel_cn'] == 2:
            msg = 'Клиент: ' + await activeName(clientModel) + " Заказ №: " + str(order_id) + " Предложен водителю: " + await activeName(driverModel)
            print(msg)
            await message.bot.send_message(ADMIN_ID, msg, parse_mode='HTML')





# Помоему метод вообще не работает
async def driverDoneOrder(message):
    try:
        driverId = BotDB.get_driver_id(message.from_user.id)
        if (not driverId):
            await message.bot.send_message(message.from_user.id, t("Driver not found"))
        else:
            modelOrder = BotDB.get_order_progress_by_driver_id(driverId)
            if (not modelOrder):
                await message.bot.send_message(message.from_user.id, t("You haven`t current order"))
            else:
                BotDB.update_order_status(modelOrder['id'], 'done')
                modelOrder = BotDB.get_order_progress_by_driver_id(driverId)
                if modelOrder:
                    BotDB.update_driver_status(message.from_user.id, 'route')
                else:
                    BotDB.update_driver_status(message.from_user.id, 'offline')
                await message.bot.send_message(message.from_user.id, t('Congratulations! You have completed the order. You can go back to online to make a new order'))
    except:
        await message.bot.send_message(message.from_user.id, t("Can`t set done order status"))




async def menuDriver(message):
    markup = InlineKeyboardMarkup(row_width=3)
    item1 = InlineKeyboardButton(text=t('Driver form') + ' 📝', callback_data='driver-form')
    item2 = InlineKeyboardButton(text=t('Account'), callback_data='account')
    item4 = InlineKeyboardButton(text=t('How to top up') + ' ❓', callback_data='how-topup-account')
    item3 = InlineKeyboardButton(text=t('Done orders'), callback_data='driver-done-orders')
    item5 = InlineKeyboardButton(text=t('My profile') + ' 🔖', callback_data='driver-profile')
    item6 = InlineKeyboardButton(text=t("Go online 🟢"), callback_data='switch-online')
    item7 = InlineKeyboardButton(text=t('Go offline 🔴'), callback_data='switch-offline')
    item71 = InlineKeyboardButton(text=t('Rules'), callback_data='driver-rules')
    item8 = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='back')
    driverModel = BotDB.get_driver(message.from_user.id)
    if (not driverModel):
        await message.bot.send_message(message.from_user.id, "Can`t do it, begin to /start")
    else:
        if driverModel['status'] != None:
            markup.add(item5, item1)
        else:
            markup.add(item1)
        markup.add(item2, item4).add(item6, item7).add(item3)
        markup.add(item71)
        markup.add(item8)
        await message.bot.send_message(message.from_user.id, t("You are in the driver menu"), reply_markup = markup)




async def switchDriverOnline(message):
    # await message.bot.send_message(message.from_user.id, 'You need set a current location')
    BotDB.update_driver_status(message.from_user.id, 'online')
    localMessage = 'Вы онлайн. В течении {onlineTime:d} минут Вам будут приходить заказы'.format(onlineTime = round(ONLINE_TIME_SEC/60))
    await message.bot.send_message(message.from_user.id, localMessage)

    # Запуск таймера Онлайн-статуса
    # выполнить функцию switchDriverOffline() через onlineTime секунд
    Timer(ONLINE_TIME_SEC, switchDriverOffline, args=message)
    pass



# Пока отключена
async def getNearWaitingOrder(message, onTimer = True):
    driverModel = BotDB.get_driver(message.from_user.id)
    if driverModel['status'] != 'online':
        onTimer = False
    modelOrder = BotDB.get_near_order('waiting', driverModel['latitude'], driverModel['longitude'], message.from_user.id)
    if modelOrder:
        if not modelOrder['order_id']:
            modelOrder['order_id'] = 0
        if modelOrder['order_id']:
            modelOrder = BotDB.get_order(modelOrder['order_id'])
            # Сюда можем отправлять только стандартную модель order
            await getOrderCard(message, message.from_user.id, modelOrder)
    if onTimer:
        Timer(ORDER_REPEAT_TIME_SEC, getNearWaitingOrder, args=message)




async def switchDriverOffline(message):
    driverModel = BotDB.get_driver(message.from_user.id)
    modelOrder = BotDB.get_order_progress_by_driver_id(message.from_user.id)
    if not driverModel:
        print('can`t switch to offline')
    elif modelOrder:
        BotDB.update_driver_status(message.from_user.id, 'route')
        await message.bot.send_message(message.from_user.id, t("You switch route. Orders unavailable"), reply_markup = await markupRemove())
    else:
        if driverModel['status'] != 'offline':
            BotDB.update_driver_status(message.from_user.id, 'offline')
        await message.bot.send_message(message.from_user.id, t("You switch offline. Orders unavailable"), reply_markup = await markupRemove())
    pass




async def getOrderCard(message, driver_id, modelOrder, buttons = True):
    driverModel = BotDB.get_driver(driver_id)
    modelDriverOrder = BotDB.get_driver_order(driver_id, modelOrder['id'])
    modelClient = BotDB.get_client(modelOrder['client_id'])
    data = {
        'departure_latitude': driverModel['latitude'],
        'departure_longitude': driverModel['longitude'],
        'destination_latitude': modelOrder['departure_latitude'],
        'destination_longitude': modelOrder['departure_longitude']
    }
    gdata = await getGoogleData(data)
    distanceToClient = gdata['distance']['text']
    markup = InlineKeyboardMarkup(row_width=3)
    if buttons:
        item1 = InlineKeyboardButton(text=t('Cancel') + ' ❌', callback_data='orderCancel_' + str(modelOrder['id']))
        item2 = InlineKeyboardButton(text=t('Confirm') + ' ✅', callback_data='orderConfirm_' + str(modelOrder['id']))
        markup.add(item1, item2)
    if not modelDriverOrder:
        driver_cancel_cn = 0
    else:
        driver_cancel_cn = modelDriverOrder['driver_cancel_cn']
    caption = [
        '<b>Заказ №' + str(modelOrder['id']) + '</b>',
        'Имя <b>' + str(modelClient['name']) + '</b>',
        'Расстояние до клиента <b>' + str(distanceToClient) + '</b>',
        'Длина маршрута <b>' + str(modelOrder['route_length'] / 1000) + ' км.' + '</b>',
        'Стоимость <b>' + str(modelOrder['amount_client']) + ' ' + str(CURRENCY) + '</b>',
        'Рейтинг <b>' + (await getRating(message) * '⭐') + '(' + str(await getRating(message)) + '/5)</b>',
    ]
    if modelOrder['status'] == 'progress':
        caption.insert(2, 'Телефон <b>' + str(modelClient['phone']) + '</b>')
    if driver_cancel_cn > 0:
        caption.append('Вы отклоняли <b>' + str(driver_cancel_cn) + ' раз</b>',)
    caption = '\n'.join(caption)
    await message.bot.send_message(driver_id, caption, parse_mode='HTML', reply_markup = markup)
async def getOrderCardClient(message, orderModel, cancel = False, confirm = False):
    clientModel = BotDB.get_client(orderModel['client_id'])
    markup = InlineKeyboardMarkup(row_width=3)
    if cancel & (not orderModel['driver_id']) & (orderModel['status'] in ['create', 'waiting']):
        item1 = InlineKeyboardButton(text=t('Cancel trip') + ' ❌', callback_data='orderCancelClient_' + str(orderModel['id']))
        markup.add(item1)
    if confirm:
        item2 = InlineKeyboardButton(text=t('Confirm') + ' ✅', callback_data='orderWaitingClient_' + str(orderModel['id']))
        markup.add(item2)
    gdata = await getGoogleData(orderModel)
    caption = [
        '<b>Заказ №' + str(orderModel['id']) + '</b>',
        'Имя <b>' + str(clientModel['name']) + '</b>',
        'Длина маршрута <b>' + str(orderModel['route_length'] / 1000) + ' км.' + '</b>',
        'Время в пути <b>' + str(gdata['duration']['text']) + '</b>',
        'Стоимость <b>' + str(orderModel['amount_client']) + ' ' + str(CURRENCY) + '</b>',
        'Статус <b>' + str(BotDB.statuses[orderModel['status']]) + '</b>',
    ]
    if (orderModel['status'] == 'waiting') & (orderModel['driver_id'] == str(message.from_user.id)):
        caption.insert(1, 'Телефон <b>' + str(clientModel['phone']) + '</b>')
    caption = '\n'.join(caption)
    await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML', reply_markup = markup)




async def setCarPhoto(message, state):
    async with state.proxy() as data:
        data['dir'] = 'cars/'
        data['savedKey'] = 'carPhotoSaved'
    await message.bot.send_message(message.from_user.id, t("Attach a photo of your car"), reply_markup = await markupRemove())
async def setDriverPhoto(message, state):
    async with state.proxy() as data:
        data['dir'] = 'drivers/'
        data['savedKey'] = 'driverPhotoSaved'
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text = 'Пропустить шаг', callback_data='driverPhotoMissed'))
    await message.bot.send_message(message.from_user.id, t("You can attach your photo if you wish"), reply_markup = markup)
@dp.message_handler(content_types='photo')
async def process_car_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        dir = data['dir']
        savedKey = data['savedKey']
    await message.photo[-1].download(destination_file=dir + str(message.from_user.id) + '.jpg')

    if (HAS_CONFIRM_STEPS_DRIVER):
        dMessage = await message.bot.send_message(message.from_user.id, t("Do you confirm?"), reply_markup = await inlineConfirm(savedKey))
        async with state.proxy() as data:
            data['dMessage'] = dMessage
    else:
        if (savedKey == 'carPhotoSaved'):
            await setDriverPhoto(message, state)
        elif (savedKey == 'driverPhotoSaved'):
            await setDriverName(message)




async def carPhotoSaved(message):
    async with state.proxy() as data:
        dMessage = data['dMessage']
        pass
    await deleteMessage(message, dMessage)
    async with state.proxy() as data:
        data['dir'] = 'drivers/'
        data['savedKey'] = 'driverPhotoSaved'




async def getWalletDrivers(message):
    drivers = BotDB.get_drivers_with_wallets()
    markup = InlineKeyboardMarkup(row_width=3)
    for driverModel in drivers:
        item = InlineKeyboardButton(text=str(driverModel['tg_user_id']) + ' - ' + str(driverModel['wallet']) + ' - ' + str(driverModel['tg_first_name']), callback_data='wallet_' + str(driverModel['wallet']))
        markup.add(item)
    await message.bot.send_message(message.from_user.id, 'Выберите водителя', reply_markup = markup)




async def setDriverTopupBalance(message, wallet, state):
    drivers = len(BotDB.get_drivers_by_wallet(wallet))
    if (drivers > 1):
        localMessage = "Нельзя пополнить кошелек поскольку найдено {drivers:d} водителей с таким кошельком"
        localMessage = localMessage.format(drivers = drivers)
        await message.bot.send_message(message.from_user.id, localMessage, reply_markup = await markupRemove())
    else:
        await FormDriver.balance.set()
        async with state.proxy() as data:
            data['wallet'] = wallet
        await message.bot.send_message(message.from_user.id, t("Top up driver balance"), reply_markup = await markupRemove())
@dp.message_handler(state=FormDriver.balance)
async def process_driver_deposit_balance(message: types.Message, state: FSMContext):

    if message.text == t('Confirm'):
        pass
    else:
        match = re.match('^[\-]?[\d]{1,10}$', message.text)
        if match:
            async with state.proxy() as data:
                data['changeBalance'] = message.text
            await message.bot.send_message(message.from_user.id, t('Do you confirm?'), reply_markup = await inlineConfirm('driverTopupBalanceConfirm'))
        else:
            await message.bot.send_message(message.from_user.id, t("Only digits can be entered"))
            await message.bot.send_message(message.from_user.id, t("You can input from 1 to 10 digits"))




async def setDriverPhone(message):
    await FormDriver.phone.set()
    await message.bot.send_message(message.from_user.id, t("Enter phone number") + '\nℹ<i>' + t("Examples of phone number: +905331234567, +79031234567") + '</i>', parse_mode='HTML', reply_markup = await markupRemove())
@dp.message_handler(state=FormDriver.phone)
async def process_driver_phone(message: types.Message, state: FSMContext):
    match = re.match(PHONE_MASK, message.text)
    if match:
        async with state.proxy() as data:
            data['phone'] = message.text
        if (not HAS_CONFIRM_STEPS_DRIVER):
            try:
                await driverRegistered(message, state)
                await menuDriver(message)
            except:
                await menuDriver(message)
                await message.bot.send_message(message.from_user.id, t("We can`t create your form"), reply_markup = await markupRemove())
            pass
        else:
            await message.bot.send_message(message.from_user.id, t('Do you confirm?'), reply_markup = await inlineConfirm('driverPhoneSaved'))
        pass
    else:
        await message.bot.send_message(message.from_user.id, t("Number of digits is incorrect"))




async def setDriverName(message):
    await FormDriver.name.set()
    await message.bot.send_message(message.from_user.id, t("What's your name?"), reply_markup = types.ReplyKeyboardRemove())
@dp.message_handler(state=FormDriver.name)
async def process_driver_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    if (not HAS_CONFIRM_STEPS_DRIVER):
        await setDriverCarNumber(message)
    else:
        await message.bot.send_message(message.from_user.id, t('Do you confirm?'), reply_markup = await inlineConfirm('driverNameSaved'))




async def setDriverCarNumber(message):
    await FormDriver.car_number.set()
    await message.bot.send_message(message.from_user.id, t("What's your car number?"), reply_markup = await markupRemove())
@dp.message_handler(state=FormDriver.car_number)
async def process_driver_car_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['car_number'] = message.text
    if (not HAS_CONFIRM_STEPS_DRIVER):
        await setDriverPhone(message)
    else:
        await message.bot.send_message(message.from_user.id, t('Do you confirm?'), reply_markup = await inlineConfirm('driverCarNumberSaved'))




async def getActiveOrders(message):
    waitingOrders = BotDB.get_orders(message.from_user.id, 'waiting')
    if len(waitingOrders) == 0:
        await message.bot.send_message(message.from_user.id, t('Has not waiting orders'))
    else:
        for row in waitingOrders:
            text = '\n'.join((
                'Статус <b>' + row['status'] + '</b>',
                'Дата <b>' + str(row['dt_order']) + '</b>',
                'Стоимость, ' + str(CURRENCY) + ' <b>' + str(row['amount_client']) + '</b>',
                'Длина маршрута, км. <b>' + str(row['route_length'] / 1000) + '</b>',
                'Время поездки, мин. <b>' + str(row['route_time']) + '</b>'
            ));
            # await message.bot.send_location(message.from_user.id, row['departure_latitude'], row['departure_longitude'])
            await message.bot.send_message(message.from_user.id, text, reply_markup = await bookOrder('bookOrder_' + str(row['id'])))
            pass




async def getDriverDoneOrders(message):
    modelOrders = BotDB.get_orders(message.from_user.id, 'done')
    if len(modelOrders) == 0:
        await message.bot.send_message(message.from_user.id, t('Has not done orders'))
    else:
        await menuDriver(message)
        for row in modelOrders:
            if not row['dt_order']:
                dateFormat = 'Не указана'
            else:
                dateFormat = datetime.strptime(str(row['dt_order']), "%Y-%m-%d %H:%M:%S").strftime("%H:%M %d-%m-%Y")
            text = '\n'.join((
                '<b>Заказ № ' + str(row['id']) + '</b>',
                'Статус <b>' + BotDB.statuses[row['status']] + '</b>',
                'Дата <b>' + str(dateFormat) + '</b>',
                'Стоимость, ' + str(CURRENCY) + ' <b>' + str(row['amount_client']) + '</b>',
                'Длина маршрута, км. <b>' + str(row['route_length'] / 1000) + '</b>',
                'Время поездки, мин. <b>' + str(row['route_time']) + '</b>'
            ));
            await message.bot.send_message(message.from_user.id, text, reply_markup = await markupRemove())
            pass




async def setDriverWallet(message):
    driverModel = BotDB.get_driver(message.from_user.id)
    if (not driverModel):
        await message.bot.send_message(message.from_user.id, t("You need fill the form"))
    else:
        await FormDriver.wallet.set()
        await message.bot.send_message(message.from_user.id, t("Enter the sender's wallet"))
@dp.message_handler(state=FormDriver.wallet)
async def process_driver_wallet(message: types.Message, state: FSMContext):
    if (message.text == t('Confirm')):
        async with state.proxy() as data:
            wallet = data['wallet']
        await state.finish()
        BotDB.update_driver_wallet(message.from_user.id, wallet)
        await message.bot.send_message(message.from_user.id, t('Thank you, we will check the crediting of funds'), reply_markup = await markupRemove())
    else:
        async with state.proxy() as data:
            data['wallet'] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        markup.add(types.KeyboardButton(t('Confirm')))
        await message.bot.send_message(message.from_user.id, t('Confirm entry or correct value'), reply_markup = markup)




async def menuClient(message):
    orderCn = str(len(BotDB.get_client_orders(message.from_user.id)))
    modelClient = BotDB.get_client(message.from_user.id)
    markup = InlineKeyboardMarkup(row_width=1)
    item10 = InlineKeyboardButton(text=t('Profile'), callback_data='client-profile')
    item20 = InlineKeyboardButton(text=t('Make an order') + ' 🚕', callback_data='make-order')
    # item30 = InlineKeyboardButton(text=t('Free drivers'), callback_data='free-drivers')
    item40 = InlineKeyboardButton(text=t('My orders') + ' (' + orderCn + ')', callback_data='client-orders_0_0_0')
    item45 = InlineKeyboardButton(text=t('Rules'), callback_data='client-rules')

    item50 = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='back')
    if modelClient['name'] and modelClient['phone']:
        markup.add(item10)
    markup.add(item20).add(item40).add(item45).add(item50)
    await message.bot.send_message(message.from_user.id, t("You are in the client menu"), reply_markup = markup)





async def setName(message, state):
    await FormClient.name.set()

    clientModel = BotDB.get_client(message.from_user.id)
    markup = InlineKeyboardMarkup(row_width=1)
    if clientModel['name']:
        nameExists = True
    else:
        nameExists = False
    if clientModel['phone']:
        phoneExists = True
    else:
        phoneExists = False
    nameMessage = t("What's your name?")
    if nameExists & phoneExists:
        async with state.proxy() as data:
            data['name'] = clientModel['name']
            data['phone'] = clientModel['phone']
            pass
        markup.add(InlineKeyboardButton(text = t('Leave unchanged'), callback_data='clientPhoneSaved'))
        nameMessage += '. Вы можете оставить без изменений имя и телефон'
    await message.bot.send_message(message.from_user.id, nameMessage, reply_markup = markup)
@dp.message_handler(state=FormClient.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    if HAS_CONFIRM_STEPS_CLIENT:
        await message.bot.send_message(message.from_user.id, data['name'] + t(', do you confirm your name?'), reply_markup = await inlineConfirm('clientNameSaved'))
    else:
        await setPhone(message)




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

    clientModel = BotDB.get_client(message.from_user.id)
    markup = InlineKeyboardMarkup(row_width=6)
    if clientModel['phone']:
        markup.add(InlineKeyboardButton(text = 'Мой номер ' + clientModel['phone'], callback_data='clientPhoneSaved'))

    await message.bot.send_message(message.from_user.id, t("Enter phone number") + '\nℹ<i>' + t("Examples of phone number: +905331234567, +79031234567") + '</i>', parse_mode='HTML', reply_markup = markup)
@dp.message_handler(state=FormClient.phone)
async def process_phone(message: types.Message, state: FSMContext):
    print(re.compile('[^0-9+]').sub('', message.text))
    message.text = re.compile('[^0-9+]').sub('', message.text)
    match = re.match(PHONE_MASK, message.text)
    if match:
        async with state.proxy() as data:
            data['phone'] = message.text
        if HAS_CONFIRM_STEPS_CLIENT:
            await message.bot.send_message(message.from_user.id, t('Do you confirm your phone?'), reply_markup = await inlineConfirm('clientPhoneSaved'))
        else:
            await state.finish()
            await setDeparture(message, state)
        pass
    else:
        await message.bot.send_message(message.from_user.id, t("Number of digits is incorrect"))




async def setDriverLocation(message, state: FSMContext):
    async with state.proxy() as data:
        data['locationType'] = 'driverCurLoc'
    await message.bot.send_message(message.from_user.id, t('Set current location'))
    pass
async def setDeparture(message, state: FSMContext):
    async with state.proxy() as data:
        data['locationType'] = 'clientDptLoc'
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text=t('Catalog'), callback_data='catalog_0'))
    await message.bot.send_message(message.from_user.id, t("Set departure location"), parse_mode='html', reply_markup = markup)
    pass
async def setDestination(message, state: FSMContext):
    async with state.proxy() as data:
        data['locationType'] = 'clientDstLoc'
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text=t('Catalog'), callback_data='catalog_0'))
    await message.bot.send_message(message.from_user.id, t("Set destination location"), parse_mode='html', reply_markup = markup)

    pass
@dp.message_handler(content_types=['location', 'venue'], state='*')
async def process_location(message, state: FSMContext):
    markup = types.InlineKeyboardMarkup(row_width=2)
    async with state.proxy() as data:
        locationType = data['locationType']
    if locationType == 'clientDptLoc':
        async with state.proxy() as data:
            data['departure_latitude'] = message.location.latitude
            data['departure_longitude'] = message.location.longitude
            pass
        if HAS_CONFIRM_STEPS_CLIENT:
            markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data='departureLocationSaved'))
            await message.bot.send_message(message.from_user.id, t("Confirm entry or correct value"), reply_markup = markup)
        else:
            await setDestination(message, state)
    elif locationType == 'clientDstLoc':
        async with state.proxy() as data:
            data['destination_latitude'] = message.location.latitude
            data['destination_longitude'] = message.location.longitude
            pass
        if HAS_CONFIRM_STEPS_CLIENT:
            markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data='destinationLocationSaved'))
            await message.bot.send_message(message.from_user.id, t("Confirm entry or correct value"), reply_markup = markup)
        else:
            await destinationLocationSaved(message, state)
    elif locationType == 'driverCurLoc':
        BotDB.update_driver_location(message.from_user.id, message.location.latitude, message.location.longitude)
        if HAS_CONFIRM_STEPS_DRIVER:
            markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data='driverLocationSaved'))
            await message.bot.send_message(message.from_user.id, t("Confirm entry or correct value"), reply_markup = markup)
        else:
            await switchDriverOnline(message)
    else:
        await message.bot.send_message(message.from_user.id, t("Sorry can`t saved data"))
    pass
#Если пользователь хочет указать локацию "текстом"
@dp.message_handler(content_types='text', state='*')
async def process_location(message: types.Message, state: FSMContext):
    locationModels = BotDB.get_location_by_name(message.text)
    async with state.proxy() as data:
        locationType = data['locationType']

    markup = InlineKeyboardMarkup(row_width=3)

    if locationType == 'clientDptLoc':
        for locationModel in locationModels:
            item = InlineKeyboardButton(text=str(locationModel['name_rus']), callback_data='departureLocationSavedByLocId_' + str(locationModel['id']))
            markup.add(item)
        item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='clientPhoneSaved')
        markup.add(item)
    elif locationType == 'clientDstLoc':
        for locationModel in locationModels:
            item = InlineKeyboardButton(text=str(locationModel['name_rus']), callback_data='destinationLocationSavedByLocId_' + str(locationModel['id']))
            markup.add(item)
        item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='departureLocationSaved')
        markup.add(item)
    elif locationType == 'driverCurLoc':
        for locationModel in locationModels:
            item = InlineKeyboardButton(text=str(locationModel['name_rus']), callback_data='driverLocationSavedByLocId_' + str(locationModel['id']))
            markup.add(item)
    else:
        await message.bot.send_message(message.from_user.id, ("We can`t get type of location"))

    if len(locationModels):
        await message.bot.send_message(message.from_user.id, t("Found the following options"), reply_markup = markup)
    else:
        await message.bot.send_message(message.from_user.id, t("Could not find options"))
    pass




async def destinationLocationSaved(message, state: FSMContext):
    dataClient = {}
    dataOrder = {}
    clientModel = BotDB.get_client(message.from_user.id)

    async with state.proxy() as data:
        if 'name' in data:
            dataClient['name'] = data['name']
        else:
            dataClient['name'] = clientModel['name']
        if 'phone' in data:
            dataClient['phone'] = data['phone']
        else:
            dataClient['phone'] = clientModel['phone']
        dataOrder['departure_latitude'] = data['departure_latitude']
        dataOrder['departure_longitude'] = data['departure_longitude']
        dataOrder['destination_latitude'] = data['destination_latitude']
        dataOrder['destination_longitude'] = data['destination_longitude']
        pass


    lenParams = await setLength(message, dataOrder)
    dataOrder['client_id'] = message.from_user.id
    dataOrder['status'] = 'create'
    dataOrder['dt_order'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dataOrder['amount_client'] = lenParams['amount_client']
    dataOrder['route_length'] = lenParams['route_length']
    dataOrder['route_time'] = lenParams['route_time']

    await state.finish()

    dump(dataOrder)
    orderId = BotDB.create_order(dataOrder)

    BotDB.update_client(message.from_user.id, dataClient)

    modelOrder = BotDB.get_order(orderId)
    await getOrderCardClient(message, modelOrder, True, True)



async def sendClientNotification(message, orderModel):
    # Ваш заказ принят. Водитель выехал к Вам
    await message.bot.send_message(orderModel['client_id'], t("Your order is accepted. The driver drove to you"))
    await driverProfile(message, orderModel['driver_id'], orderModel['client_id'], True)

    markupDoneOrder = types.InlineKeyboardMarkup(row_width=1)
    markupDoneOrder.add(types.InlineKeyboardButton(text=t('Done current order'), callback_data='clientDoneOrder_' + str(orderModel['id'])))
    await message.bot.send_message(orderModel['client_id'], t('When you reach your destination, please click on the button to complete the current order'), reply_markup = markupDoneOrder)
    pass





async def getCategories(message, parentId, state: FSMContext):
    locationModels = BotDB.get_locations_by_category_id(parentId)
    markup = InlineKeyboardMarkup(row_width=2)
    async with state.proxy() as data:
        if not data:
            item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client')
            markup.add(item)
            await message.bot.send_message(message.from_user.id, '🤔 Хм, попробуйте начать заказ с начала', reply_markup = markup)
            return
        locationType = data['locationType']
    if len(locationModels) == 0:
        categoryModels = BotDB.get_categories(parentId)
        catMessage = t("Select category")
        if len(categoryModels) == 0:
            catMessage = t("Could not find options")
            markup.add(types.InlineKeyboardButton(text=t('Catalog'), callback_data='catalog_0'))
        else:
            for categoryModel in categoryModels:
                item = InlineKeyboardButton(text=str(categoryModel['name']), callback_data='catalog_' + str(categoryModel['id']))
                markup.add(item)
                if categoryModel['parent_id']:
                    catMessage = t('Select subcategory')
            if parentId != 0:
                item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='catalog_0')
                markup.add(item)
            else:
                item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client')
                markup.add(item)
    else:
        catMessage = t("Found locations")
        for locationModel in locationModels:
            if locationType == 'clientDptLoc':
                callbackData = 'departureLocationSavedByLocId_' + str(locationModel['id'])
            elif locationType == 'clientDstLoc':
                callbackData = 'destinationLocationSavedByLocId_' + str(locationModel['id'])
            item = InlineKeyboardButton(text=str(locationModel['name_rus']), callback_data=callbackData)
            markup.add(item)
        item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='catalog_0')
        markup.add(item)
    await message.bot.send_message(message.from_user.id, (catMessage), reply_markup = markup)



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
        await message.bot.send_message(message.from_user.id, '🤔 Секундочку... ' + t("We are already looking for drivers for you.."))
    except:
        print('error method clientRegistered(message)')
        await gotoStart(message)
async def driverRegistered(message, state: FSMContext):
    driverData = {}
    async with state.proxy() as data:
        driverData['name'] = data['name']
        driverData['phone'] = data['phone']
        driverData['car_number'] = data['car_number']
        driverData['status'] = 'offline'

    await state.finish()
    BotDB.update_driver(message.from_user.id, driverData)
    # time.sleep(2)
    await message.bot.send_message(message.from_user.id, t("Your profile is saved"))




async def inviteLink(message):
    await message.bot.send_message(message.from_user.id, 'Ниже отправлен текст сообщения. Скопируйте другу, которого хотите пригласить')
    await message.bot.send_message(
        message.from_user.id,
        'Привет. Хочу поделиться новым сервисом по поиску Такси https://t.me/TaxiTRNCBot?start=' + str(message.from_user.id))





async def deleteMessage(aio, dMessage):
    await dMessage.bot.delete_message(dMessage.from_user.id, dMessage.message_id)
    pass





async def addReferer(m):
    user_id = m.from_user.id
    # Проверяем наличие закрепленного реферера за пользователем
    modelClient = BotDB.get_client(user_id)
    modelDriver = BotDB.get_driver(user_id)
    if not modelClient['referer_user_id'] and not modelDriver['referer_user_id']:
        referer_user_id = None
        # Проверяем наличие хоть какой-то дополнительной информации из ссылки
        if " " in m.text:
            referrer_candidate = m.text.split()[1]

            # Пробуем преобразовать строку в число
            try:
                referrer_candidate = int(referrer_candidate)

                # Проверяем на несоответствие TG ID пользователя TG ID реферера
                # Также проверяем, есть ли такой реферер в базе данных
                if user_id != referrer_candidate and (BotDB.client_exists(referrer_candidate) or BotDB.driver_exists(referrer_candidate)):
                    referer_user_id = referrer_candidate

            except ValueError:
                pass

            # Do update referer_user_id
            BotDB.update_driver_referer(m.from_user.id, referer_user_id)
            BotDB.update_client_referer(m.from_user.id, referer_user_id)
    pass





async def getRating(message):
    modelOrdersUserAll = len(BotDB.get_client_orders(message.from_user.id))
    modelOrdersUserDone = len(BotDB.get_done_orders_by_client_id(message.from_user.id))
    if modelOrdersUserAll == 0:
        return 5
    return round(modelOrdersUserDone / modelOrdersUserAll * 5)




async def getWikiBotInfo(message, receiver_id):
    caption = '''
Навигатор по Северному Кипру Wikibot 🏝🇹🇷
Все услуги и места в одном месте 🤖
Каждый из вас может разместить в нем свою услугу или объявление - бесплатно😉'''
    bio = BytesIO()
    image = Image.open('images/wikibot.jpg')
    image.save(bio, 'JPEG')
    bio.seek(0)

    wiki = InlineKeyboardMarkup(row_width=1)
    wiki.add(InlineKeyboardButton(text='Перейти в Wikibot', url = 'https://cazi.me/7R6XM'))
    wiki.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client'))
    await message.bot.send_photo(receiver_id, bio, caption=caption, parse_mode='HTML', reply_markup = wiki)




async def clientRules(message):
    caption = '''<b>Для пассажиров</b>
Бот поможет удобно и недорого заказать такси (частного водителя).

 • Как рассчитывается цена поездки?
Стоимость за 1км = {rate1KM:d} {currency:s}
ℹ️ Стоимость поездки рассчитается автоматически и зависит от длины маршрута в километрах (км).
К примеру стоимость поездки на расстояние {kilometers:d} км составит {amountKM:d} TL ({kilometers:d}км * {rate1KM:d} TL = {amountKM:d} TL)

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




async def driverRules(message):
    caption = '''<b>Для водителей</b>
Бот поможет удобно находить людей желающих добраться из точки А в точку Б.

ℹ️ бот бесплатный для водителей!
Для возможности принимать заказы должна быть заполнена АНКЕТА.
 • анкета
    ⁃ Сделайте фото автомобиля. На фото должно быть хорошо видно ваш автомобиль, чтобы клиент мог найти его среди других автомобилей на улице
    ⁃ Укажите номер автомобиля, достаточно цифр
    ⁃ Укажите номер телефона по которому клиенты смогут связываться с вами

По любым вопросам связывайтесь с администратором {adminTg:s}

 • Комиссия
Комиссия составляет {percent:d}% от суммы заказа. Комиссия списывается с вашего личного баланса
'''
    caption = caption.format(
        minBalanceAmount = MIN_BALANCE_AMOUNT,
        percent = PERCENT,
        adminTg = ADMIN_TG,
    )
    backDriverMenu = InlineKeyboardMarkup(row_width=1)
    backDriverMenu.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='driver'))
    await message.bot.send_message(message.from_user.id, caption, reply_markup = backDriverMenu)
    pass



async def driverProfile(message, driver_id, user_id, showPhone = False, showReturnButton = False):
    driverModel = BotDB.get_driver(driver_id)
    if (not driverModel):
        await message.bot.send_message(user_id, "Can`t do it, begin to /start")
    else:
        Path("merged").mkdir(parents=True, exist_ok=True)
        car = 'cars/' + str(driver_id) + '.jpg';
        driverFileName = 'drivers/' + str(driver_id) + '.jpg';
        fileCarExist = exists(car)
        fileDriverExist = exists(driverFileName)

        # Фото водителя не обязательный параметр
        if not fileDriverExist:
            driverFileName = 'images/anonim-user.jpg';
            fileDriverExist = True

        statusIcon = str(BotDB.statuses[driverModel['status']])
        caption = [
            '<b>Имя</b> ' + str(driverModel['name']),
            '<b>Статус</b> ' + str(statusIcon),
            '<b>Номер машины</b> ' + str(driverModel['car_number']),
        ]
        if showPhone:
            caption.insert(1, '<b>Телефон</b> ' + str(driverModel['phone']))
        caption = '\n'.join(caption)
        versionMerge = 0

        if fileCarExist & fileDriverExist:
            x = 240
            y = 320
            image1 = Image.open(car)
            image2 = Image.open(driverFileName)

            if image1.size[0] < image1.size[1]:
                if image2.size[0] < image2.size[1]:
                    versionMerge=1
                    image1 = image1.resize((x, y))
                    image2 = image2.resize((x, y))
                    merged_image = Image.new(mode='RGB', size=(x*2, y), color=(250,250,250))
                    merged_image.paste(image1,(0,0))
                    merged_image.paste(image2,(x,0))
                elif image2.size[0] > image2.size[1]:
                    versionMerge=4
                    yy = int(y / 0.75)
                    image1 = image1.resize((y, yy))
                    image2 = image2.resize((y, x))
                    merged_image = Image.new(mode='RGB', size=(y, x+yy), color=(250,250,250))
                    merged_image.paste(image1,(0,0))
                    merged_image.paste(image2,(0,yy))
                elif image2.size[0] == image2.size[1]:
                    versionMerge=6
                    image1 = image1.resize((x, y))
                    image2 = image2.resize((y, y))
                    merged_image = Image.new(mode='RGB', size=(x+y, y), color=(250,250,250))
                    merged_image.paste(image1,(0,0))
                    merged_image.paste(image2,(x,0))
            elif image1.size[0] > image1.size[1]:
                if image2.size[0] > image2.size[1]:
                    versionMerge=2
                    image1 = image1.resize((y, x))
                    image2 = image2.resize((y, x))
                    merged_image = Image.new(mode='RGB', size=(y, x*2), color=(250,250,250))
                    merged_image.paste(image1,(0,0))
                    merged_image.paste(image2,(0,x))
                elif image2.size[0] < image2.size[1]:
                    versionMerge=3
                    yy = int(y / 0.75)
                    image1 = image1.resize((y, x))
                    image2 = image2.resize((y, yy))
                    merged_image = Image.new(mode='RGB', size=(y, yy+x), color=(250,250,250))
                    merged_image.paste(image1,(0,0))
                    merged_image.paste(image2,(0,x))
                elif image2.size[0] == image2.size[1]:
                    versionMerge=7
                    image1 = image1.resize((y, x))
                    image2 = image2.resize((y, y))
                    merged_image = Image.new(mode='RGB', size=(y, y+x), color=(250,250,250))
                    merged_image.paste(image1,(0,0))
                    merged_image.paste(image2,(0,x))
            elif image1.size[0] == image1.size[1] & image2.size[0] == image2.size[1]:
                versionMerge=5
                image1 = image1.resize((y, y))
                image2 = image2.resize((y, y))
                merged_image = Image.new(mode='RGB', size=(y+y, y), color=(250,250,250))
                merged_image.paste(image1,(0,0))
                merged_image.paste(image2,(y,0))

        backDriverMenu = InlineKeyboardMarkup(row_width=1)
        if showReturnButton:
            backDriverMenu.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='driver'))

        if versionMerge > 0:

            bio = BytesIO()
            bio.name = 'merged/' + str(driver_id) + '.jpg'
            merged_image.save(bio, 'JPEG')
            bio.seek(0)
            await message.bot.send_photo(user_id, bio, caption=caption, parse_mode='HTML', reply_markup = backDriverMenu)
            print('versionMerge: ' + str(versionMerge))
        else:
            await message.bot.send_message(user_id, caption, parse_mode='HTML', reply_markup = backDriverMenu)
    pass




async def shortStatistic(message):
    driverAllModels = BotDB.get_drivers()
    driverRegisteredModels = BotDB.get_drivers_registered()
    driversOnlineModels = BotDB.get_drivers_by_status('online')
    clientAllModels = BotDB.get_clients()
    orderWaitingModels = BotDB.get_orders(message.from_user.id, 'waiting')
    caption = [
        '<b>Короткая статистика</b>',
        'Всего водителей <b>' + str(len(driverAllModels)) + '</b>',
        'Водителей с анкетой <b>' + str(len(driverRegisteredModels)) + '</b>',
        'Онлайн водителей <b>' + str(len(driversOnlineModels)) + '</b>',
        'Всего клиентов <b>' + str(len(clientAllModels)) + '</b>',
        'Заказов в ожидании <b>' + str(len(orderWaitingModels)) + '</b>',
    ]
    caption = '\n'.join(caption)
    await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML')


async def activeName(userModel):
    return '<a href="tg://openmessage?user_id=' + str(userModel['tg_user_id']) + '">' + str(userModel['tg_first_name']) + '</a>'

async def incentiveDriverFillForm(message):
    unregisteredDriverModels = BotDB.get_drivers_unregistered()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text=('Заполнить анкету'), callback_data='driver-form'))
    caption = 'Мы обнаружили что вы заходили в наш бот но при этом не прошли процесс регистрации водителя. \n\nХотим предложить вам заполнить анкету водителя. \n\nПосле заполнения анкеты Вы сможете пользоваться ботом в качестве водителя, выходить на линию и получать заказы. \n\nЕсли у вас имеются вопросы по заполнению анкеты, напишите нам ' + ADMIN_TG
    sendedCn = 0
    for unregisteredDriverModel in unregisteredDriverModels:
        try:
            await message.bot.send_message(unregisteredDriverModel['tg_user_id'], caption, parse_mode='HTML', reply_markup = markup)
            sendedCn = sendedCn + 1
        except:
            await message.bot.send_message(message.from_user.id, 'Не удалось отправить сообщение контакту @' + str(unregisteredDriverModel['tg_first_name']) + ' ('+str(unregisteredDriverModel['tg_user_id']) + ')')
    await message.bot.send_message(5615867597, 'Предложение о регистрации доставлено ' + str(sendedCn) + ' водителям')



async def gotoStart(message):
    await message.bot.send_message(message.from_user.id, t("can`t do it, start with the /start command"))
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





def dump(v):
#    if type(v) == dict:
        pprint.pprint(v, indent=2)
#    else:
#        print(json.dumps(v, sort_keys=True, indent=4))



async def getGoogleData(locationsData):
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
    result = gmaps.directions(
        (locationsData['departure_latitude'], locationsData['departure_longitude']),
        (locationsData['destination_latitude'], locationsData['destination_longitude']),
        language=LANGUAGE
    )
    resultFormat = {}
    resultFormat['distance'] = result[0]['legs'][0]['distance']
    resultFormat['duration'] = result[0]['legs'][0]['duration']
    resultFormat['start_address'] = result[0]['legs'][0]['start_address']
    resultFormat['end_address'] = result[0]['legs'][0]['end_address']
    resultFormat['summary'] = result[0]['summary']
    return resultFormat




async def testFunction(message):
    x = {}
    print(x)
    pass
