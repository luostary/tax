import json
import re, math, time, datetime

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.exceptions import BotBlocked
from numpy.ma.core import append

from dispatcher import dp, bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime
from bot import db
from language import t
from config import *
from os.path import exists
from PIL import Image
from pathlib import Path
from io import BytesIO
import asyncio
from geopy.distance import geodesic
import pprint
import googlemaps
import qrcode
from . import tClient, payment
from pyrogram import Client

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

payment.register_handlers(dp)

'''
Пользователь от которого производим рассылку
'''
api_user = Client(name='my_session', api_id=API_ID, api_hash=API_HASH)
api_user.start()


@dp.my_chat_member_handler()
async def my_chat_member_handler(message: types.ChatMemberUpdated):
    if message.chat.type == 'private':
        if message.new_chat_member.status == "kicked":
            db.cancel_all_orders_after_kicked_user(message.from_user.id)
            db.user_delete(message.from_user.id)
        elif message.new_chat_member.status == "member":
            if not db.user_exists(message.from_user.id):
                db.user_add(message.from_user.id, message.from_user.first_name, 'driver')
                user = db.user_get_by_id(message.from_user.id)
                await notice_developer(message, user, 1)
                time.sleep(1)


@dp.message_handler(commands=["start", "Back"], state='*')
async def start(message: types.Message, state: FSMContext):
    await invite_users(message)
    await state.finish()

    if not db.user_exists(message.from_user.id):
        db.user_add(message.from_user.id, message.from_user.first_name, 'driver')

    await message.bot.send_message(message.from_user.id, t("Welcome!"), reply_markup=await markup_remove())

    await start_menu(message)
    # Добавление реферальной ссылки
    await add_referer(message)
    # await setDriverPhone(message)
    user = db.user_get_by_id(message.from_user.id)
    await notice_developer(message, user, 2)


# Click handler
@dp.callback_query_handler(lambda message: True, state='*')
async def inline_click(message, state: FSMContext):
    if message.data == "client":
        await menu_client(message)
    elif message.data == 'back':
        await state.finish()
        await start_menu(message)
    elif message.data == 'inviteLink':
        await invite_link(message)
    elif message.data == 'test':
        await test_function(message)
    elif message.data == 'client-rules':
        await client.rules(message)
    elif message.data == 'driver-rules':
        await driver_rules(message)
    elif message.data == 'client-profile':
        await client_profile(message, message.from_user.id)
    elif message.data == 'admin-short-statistic':
        await short_statistic(message)
    elif message.data == 'driver-incentive-fill-form':
        await incentive_driver_fill_form(message)
    elif message.data == 'make-order':
        if not await is_referer_users(message):
            await need_referer_users(message)
            return
        if not ALLOW_MANY_ORDERS:
            model_orders = db.get_waiting_orders_by_client_id(message.from_user.id)
            if model_orders:
                model_order = db.get_waiting_order_by_client_id(message.from_user.id)
                await menu_client(message)
                await message.bot.send_message(message.from_user.id, 'У Вас имеется текущий заказ')
                await get_order_card_client(message, model_order, True)
                return
        print(message.from_user.id)
        db.user_update_tg_username(message.from_user.id, message.from_user.username)
        await set_name(message, state)
    elif message.data == 'clientNameSaved':
        await state.finish()
        await set_phone(message)
    elif message.data == 'clientPhoneSaved':
        await state.finish()
        await set_departure(message, state)
    elif message.data == "driver":
        await menu_driver(message)
        pass
    elif message.data == 'driver-profile':
        if not await is_subscribe_chat(message):
            await suggest_subscribe_chat(message)
            return
        await driver_profile(message, message.from_user.id, message.from_user.id, True, True)
        pass
    elif message.data == "driver-form":
        if not await is_subscribe_chat(message):
            await suggest_subscribe_chat(message)
            return
        await set_car_photo(message, state)
    elif message.data == 'drivers':
        await get_wallet_drivers(message)
    elif message.data == 'carPhotoSaved':
        delete_is_on = False
        async with state.proxy() as data:
            d_message = data['dMessage']
            pass
        if delete_is_on:
            await delete_message(d_message)
        await set_driver_photo(message, state)
    elif message.data == 'driverCarNumberSaved':
        await state.finish()
        await set_driver_phone(message)
    elif message.data == 'driverNameSaved':
        await set_driver_car_number(message)
    elif message.data == 'driverPhoneSaved':
        await menu_driver(message)
        try:
            await driver_registered(message, state)
        except():
            await message.bot.send_message(message.from_user.id, t("We can`t create your form"),
                                           reply_markup=await markup_remove())
        pass
    elif message.data in ['driverPhotoSaved', 'driverPhotoMissed']:
        await set_driver_name(message)
    elif message.data == 'driverDoneOrder':
        await driver_done_order(message)
    elif message.data == 'driverTopUpBalanceConfirm':
        async with state.proxy() as data:
            local_wallet = (data['wallet'])
            local_balance = int(data['changeBalance'])
        driver_model = db.get_driver_by_wallet(local_wallet)
        if not driver_model:
            await message.bot.send_message(message.from_user.id,
                                           t("Wallet not found, you can see right wallet to your profile"),
                                           reply_markup=await markup_remove())
        else:
            if driver_model['balance'] is None:
                driver_model['balance'] = 0
            new_balance = driver_model['balance'] + local_balance
            db.update_driver_balance(driver_model['tg_user_id'], new_balance)
            time.sleep(2)
            await message.bot.send_message(message.from_user.id, t("Balance is filled"))

            caption = ''
            if driver_model['name']:
                caption = driver_model['name'] + ', '
            caption += "Ваш баланс пополнен на " + str(local_balance) + " usdt"
            await message.bot.send_message(driver_model['tg_user_id'], caption)
        await state.finish()
        pass
    elif message.data == 'account':
        driver_balance = (db.user_get(message.from_user.id, 'driver'))
        if None == driver_balance['balance']:
            driver_balance['balance'] = 0
        local_message = t('Your balance is {userBalance:d} usdt') + '. '
        if minBalanceAmount > 0:
            local_message += t('Min balance for use bot is {minBalance:d} usdt')
        else:
            local_message += t('No min balance for use bot')
        local_message = local_message.format(userBalance=driver_balance['balance'], minBalance=minBalanceAmount)
        markup_back = InlineKeyboardMarkup(row_width=1)
        markup_back.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='driver'))
        await message.bot.send_message(message.from_user.id, local_message, reply_markup=markup_back)
    elif message.data == 'client-account':
        client_balance = (db.user_get(message.from_user.id, 'client'))
        if None == client_balance['balance']:
            client_balance['balance'] = 0
        local_message = t('Your balance is {userBalance:d} usdt')
        local_message = local_message.format(userBalance=client_balance['balance'])
        markup_back = InlineKeyboardMarkup(row_width=1)
        markup_back.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client'))
        await message.bot.send_message(message.from_user.id, local_message, reply_markup=markup_back)
    elif message.data == 'how-top-up-account':
        markup_copy = InlineKeyboardMarkup(row_width=1)
        # markupCopy.add(InlineKeyboardButton(text=t('Copy wallet'), callback_data='copy-wallet'))
        markup_copy.add(InlineKeyboardButton(text=t('Confirm the transfer'), callback_data='confirm-transfer'))
        markup_copy.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='driver'))

        local_message = ''
        if MIN_BALANCE_AMOUNT:
            local_message = t('To work in the system, you must have at least {minAmount:d} usdt on your account')
            local_message = local_message.format(minAmount=minBalanceAmount)
        else:
            if SUBSCRIBE_WEEK_AMOUNT:
                local_message = t('To work in the system you need to pay for a subscription')
                local_message += '\n' + t(
                    'Weekly subscription costs <b>{SUBSCRIBE_WEEK_AMOUNT:d} {CURRENCY_WALLET:s}</b>')
                local_message = local_message.format(SUBSCRIBE_WEEK_AMOUNT=SUBSCRIBE_WEEK_AMOUNT,
                                                     CURRENCY_WALLET=CURRENCY_WALLET)

        local_message += '\n\n' + t(
            'To pay for a subscription you need to transfer the currency to the specified crypto wallet. After the payment has been made Confirm the transfer with the button')

        data = WALLET
        qr = qrcode.make(data)
        qr.save('merged/wallet-qr-code.jpg')
        image = Image.open('merged/wallet-qr-code.jpg')
        bio = BytesIO()
        image.save(bio, 'JPEG')
        bio.seek(0)
        qr_msg = 'Если вы пользуетесь услугами обменного пункта - покажите кассиру QR-код кошелька'
        wallet_msg = 'QR-код нашего кошелька 👆\n\nНаш криптокошелек: \n' + '`' + WALLET + '`' + '\n\n' + qr_msg
        caption = local_message
        await bot.send_message(message.from_user.id, caption, parse_mode='HTML')
        await bot.send_photo(message.from_user.id, bio, caption=wallet_msg, parse_mode='MARKDOWN',
                             reply_markup=markup_copy)
    elif message.data == 'copy-wallet':
        pyperclip.copy(WALLET)
        pass
    elif message.data == 'confirm-transfer':
        await set_driver_wallet(message)
        pass
    elif message.data == 'driver-done-orders':
        if not await is_subscribe_chat(message):
            await suggest_subscribe_chat(message)
            return
        driver_model = db.user_get(message.from_user.id, 'driver')
        if not driver_model:
            print('can`t get driver from db')
        else:
            if driver_model['balance'] is None:
                driver_model['balance'] = 0
            if driver_model['phone'] is None:
                await message.bot.send_message(message.from_user.id, t('Phone is required, set it in client form'))
            elif driver_model['status'] == 'offline':
                await get_driver_done_orders(message)
            elif driver_model['status'] == 'route':
                local_message = t("You can`t see orders, your are at route")
                await message.bot.send_message(message.from_user.id, local_message)
            elif driver_model['status'] == 'online':
                local_message = t("You can`t see orders, your are online")
                await message.bot.send_message(message.from_user.id, local_message)
            else:
                await message.bot.send_message(message.from_user.id, t('You have unknown status'))
    elif 'catalog_' in message.data:
        array = message.data.split('_')
        await get_categories(message, int(array[1]), state)
    elif 'client-orders' in message.data:
        array = message.data.split('_')
        await client.get_client_orders(message, int(array[1]), int(array[2]), int(array[3]))
        pass
    elif 'wallet' in message.data:
        array = message.data.split('_')
        await set_driver_top_up_balance(message, array[1], state)
    elif "orderConfirm" in message.data:
        book_order_array = message.data.split('_')
        order_id = book_order_array[1]
        if db.order_waiting_exists(order_id, 'waiting'):
            model_order = db.get_order(order_id)
            if not model_order:
                await message.bot.send_message(message.from_user.id, t("Order not found"))
            else:
                if model_order['amount_client'] is None:
                    model_order['amount_client'] = 0
            driver_model = db.user_get(message.from_user.id, 'driver')
            if not driver_model:
                await message.bot.send_message(message.from_user.id, "Can`t do it, begin to /start")
            else:
                if driver_model['balance'] is None:
                    driver_model['balance'] = 0
                if not model_order['amount_client']:
                    model_order['amount_client'] = 0
                income = int(math.ceil((model_order['amount_client'] / 100 * PERCENT) / RATE_1_USDT))
                progress_order = db.get_order(order_id)
                if not progress_order:
                    await message.bot.send_message(message.from_user.id, "Can`t do it, begin to /start")
                else:
                    try:
                        db.update_driver_status(message.from_user.id, 'route')
                        db.update_order_status(order_id, 'progress')
                        progress_order = db.get_order(order_id)
                        db.update_order_driver_id(order_id, driver_model['tg_user_id'])
                        db.update_driver_balance(message.from_user.id, int(driver_model['balance'] - income))

                        await message.bot.send_message(message.from_user.id, t("You have taken the order"))
                        await get_order_card(message, message.from_user.id, progress_order, False)

                        await message.bot.send_message(message.from_user.id, t("Departure here"))
                        # Give departure-point location
                        await message.bot.send_location(message.from_user.id, progress_order['departure_latitude'],
                                                        progress_order['departure_longitude'])
                        # Give destination-point location
                        await message.bot.send_message(message.from_user.id, t("Destination here"))
                        await message.bot.send_location(message.from_user.id, progress_order['destination_latitude'],
                                                        progress_order['destination_longitude'])
                        markup_done_order = types.InlineKeyboardMarkup(row_width=1)
                        markup_done_order.add(types.InlineKeyboardButton(text=t('Done current order'),
                                                                         callback_data='driverDoneOrder_' + str(
                                                                             order_id)))
                        await message.bot.send_message(message.from_user.id,
                                                       t('When you deliver the passenger, please press the button to done the order'),
                                                       reply_markup=markup_done_order)

                        model_order = db.get_order(order_id)
                        await send_client_notification(message, model_order)
                    except():
                        await message.bot.send_message(message.from_user.id, t("Order can not be taken"))
        else:
            await message.bot.send_message(message.from_user.id, t("This order cannot be taken, it is not active"))
    elif 'orderCancel_' in message.data:
        array = message.data.split('_')
        order_id = array[1]
        if db.order_waiting_exists(order_id, 'waiting'):
            if not db.driver_order_exists(message.from_user.id, order_id):
                db.driver_order_create(message.from_user.id, order_id)
            db.driver_order_increment_cancel_cn(message.from_user.id, order_id)
            await message.bot.send_message(message.from_user.id, t("Order is cancel"))
        else:
            await message.bot.send_message(message.from_user.id, t("This order cannot be canceled, it is not active"))
        pass
    elif 'orderCancelClient_' in message.data:
        # switch order to cancel
        array = message.data.split('_')
        order_id = array[1]
        model_order = db.get_order(order_id)
        if model_order['status'] == 'cancel':
            await message.bot.send_message(message.from_user.id,
                                           ("Заказ №" + str(model_order['id']) + " уже отменен ранее"))
            return
        db.update_order_status(order_id, 'cancel')

        # Cancel fee begin
        if model_order['driver_id']:
            driver_model = db.user_get(model_order['driver_id'], 'driver')
            driver_id = driver_model['tg_user_id']
            income = int(math.ceil((model_order['amount_client'] / 100 * PERCENT) / RATE_1_USDT))
            try:
                db.update_driver_status(driver_id, 'online')
                #            BotDB.update_order_driver_id(order_id, None)
                db.update_driver_balance(driver_id, int(driver_model['balance'] + income))
            except():
                await message.bot.send_message(5615867597, (
                        "Водителю " + driver_model['tg_user_id'] + " (@" + driver_model[
                    'tg_username'] + ") не удалось вернуть комиссию " + str(
                    income) + " USDT в автоматическом режиме, необходимо вернуть вручную"))
                pass
        # Cancel fee end

        # message to client about it
        await message.bot.send_message(message.from_user.id, t("Order is cancel"))
        await menu_client(message)
        pass
    elif 'orderWaitingClient_' in message.data:
        #  What are we doing here?
        array = message.data.split('_')
        order_id = array[1]
        db.update_order_status(order_id, 'waiting')
        await client_registered(message)

        # On timer for client
        message.data = order_id
        await timer_for_client(message)

        await message.bot.send_message(message.from_user.id, "Если не готовы ждать - вы можете отменить поездку")
        model_order = db.get_order(order_id)
        await get_order_card_client(message, model_order, cancel=True, confirm=False)
        pass
    elif message.data == 'switch-online':
        if not await is_referer_users(message):
            await need_referer_users(message)
            return

        if not await is_subscribe_chat(message):
            await suggest_subscribe_chat(message)
            return

        # Check subscribe period
        if not await is_subscribe_driver_week(message):
            await bot.send_message(message.from_user.id, t('You need to pay for a subscription'))
            return

        await menu_driver(message)
        driver_model = db.user_get(message.from_user.id, 'driver')
        model_order = db.get_order_waiting_by_driver_id(message.from_user.id)
        if not driver_model:
            print('can`t get driver from db')
        else:
            if driver_model['balance'] is None:
                driver_model['balance'] = 0
            if driver_model['balance'] < minBalanceAmount:
                local_message = t("You can`t switch to online, your balance is less than {minAmount:d} usdt")
                local_message = local_message.format(minAmount=minBalanceAmount)
                await message.bot.send_message(message.from_user.id, local_message)
            elif driver_model['phone'] is None:
                await message.bot.send_message(message.from_user.id, t('Phone is required, set it in client form'))
            elif model_order:
                # Не даем переключаться в онлайн, если у водителя уже есть waiting-заказ
                await message.bot.send_message(message.from_user.id, t('You have active order'))
                await get_order_card(message, message.from_user.id, model_order, True)
            elif driver_model['status'] == 'route':
                model_order = db.get_order_progress_by_driver_id(message.from_user.id)
                if model_order:
                    local_message = t("You cannot switch to online, you must complete the route")
                    await message.bot.send_message(message.from_user.id, local_message)

                    # Give destination-point location
                    await message.bot.send_message(message.from_user.id, "Доставить клиента сюда")
                    await message.bot.send_location(message.from_user.id, model_order['destination_latitude'],
                                                    model_order['destination_longitude'])

                    markup_done_order = types.InlineKeyboardMarkup(row_width=1)
                    markup_done_order.add(types.InlineKeyboardButton(text=t('Done current order'),
                                                                     callback_data='driverDoneOrder_' + str(
                                                                         model_order['id'])))
                    await message.bot.send_message(message.from_user.id,
                                                   t('When you deliver the passenger, please press the button to done the order'),
                                                   parse_mode='HTML', reply_markup=markup_done_order)

            elif driver_model['status'] == 'online':
                local_message = t("You are online, already")
                await message.bot.send_message(message.from_user.id, local_message)
            elif driver_model['status'] == 'offline':
                db.update_driver_tg_username(message.from_user.id, message.from_user.username)
                await set_driver_location(message, state)
            else:
                await message.bot.send_message(message.from_user.id, t('You have unknown status'))
        pass
    elif message.data == 'switch-offline':
        await switch_driver_offline(message)
        pass
    elif message.data == 'clientType':
        db.update_driver_type(message.from_user.id, 'client')
        await start_menu(message)
    elif message.data == 'driverType':
        db.update_driver_type(message.from_user.id, 'driver')
        await start_menu(message)


    # Client location departure confirm
    elif message.data == 'departureLocationSaved':
        await set_destination(message, state)
        pass
    elif 'departureLocationSavedByLocId_' in message.data:
        array = message.data.split('_')
        location_id = int(array[1])
        # Сохранение координат
        location_model = db.get_location_by_id(location_id)
        async with state.proxy() as data:
            data['departure_latitude'] = float(location_model['lat'])
            data['departure_longitude'] = float(location_model['long'])
            pass
        await set_destination(message, state)
        pass


    # Подтверждение локации назначения клиентом
    elif message.data == 'destinationLocationSaved':
        await destination_location_saved(message, state)
        pass
    elif 'destinationLocationSavedByLocId_' in message.data:
        array = message.data.split('_')
        location_id = int(array[1])
        # Сохранение координат
        location_model = db.get_location_by_id(location_id)
        async with state.proxy() as data:
            data['destination_latitude'] = float(location_model['lat'])
            data['destination_longitude'] = float(location_model['long'])
            pass
        await destination_location_saved(message, state)
        pass


    # Подтверждение локации водителем
    elif message.data == 'driverLocationSaved':
        await switch_driver_online(message)
    elif 'driverLocationSavedByLocId_' in message.data:
        array = message.data.split('_')
        location_id = int(array[1])
        # Сохранение координат
        location_model = db.get_location_by_id(location_id)
        db.update_driver_location(message.from_user.id, location_model['lat'], location_model['long'])
        await switch_driver_online(message)
        pass


    elif 'driverDoneOrder_' in message.data or 'clientDoneOrder_' in message.data:
        array = message.data.split('_')
        order_id = array[1]
        model_order = db.get_order(order_id)
        if not model_order:
            await message.bot.send_message(message.from_user.id, t("Order not found"))
        elif model_order['status'] == 'done':
            await message.bot.send_message(message.from_user.id, t("Order is close already"))
            return
        else:
            try:
                db.update_order_status(order_id, 'done')
                await message.bot.send_message(message.from_user.id, t("Order is done"))

                client_back = InlineKeyboardMarkup(row_width=1)
                client_back.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client'))
                driver_back = InlineKeyboardMarkup(row_width=1)
                driver_back.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='driver'))

                if 'driverDoneOrder_' in message.data:
                    await message.bot.send_message(model_order['client_id'], "Заказ завершен водителем",
                                                   reply_markup=client_back)
                elif 'clientDoneOrder_' in message.data:
                    await message.bot.send_message(model_order['driver_id'], "Заказ завершен клиентом",
                                                   reply_markup=driver_back)

                order_progress_model = db.get_order_progress_by_driver_id(model_order['driver_id'])
                if order_progress_model:
                    db.update_driver_status(message.from_user.id, 'route')
                else:
                    db.update_driver_status(message.from_user.id, 'offline')
            except():
                print("can`t switch order to done")

            # Если инициатор завершения заявки клиент, то ему выводим рекламный блок
            time.sleep(2)
            await get_wiki_bot_info(message, model_order['client_id'])
            pass


@dp.message_handler(content_types='photo')
async def process_car_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if not data:
            await message.bot.send_message(message.from_user.id,
                                           'Прикрепление фото: Пройдите весь процесс создания анкеты сначала')
            return
        directory = data['dir']
        saved_key = data['savedKey']
    await message.photo[-1].download(destination_file=directory + str(message.from_user.id) + '.jpg')

    if HAS_CONFIRM_STEPS_DRIVER:
        d_message = await message.bot.send_message(message.from_user.id, t("Do you confirm?"),
                                                   reply_markup=await inline_confirm(saved_key))
        async with state.proxy() as data:
            data['dMessage'] = d_message
    else:
        if saved_key == 'carPhotoSaved':
            await set_driver_photo(message, state)
        elif saved_key == 'driverPhotoSaved':
            await set_driver_name(message)


@dp.message_handler(state=FormDriver.balance)
async def process_driver_deposit_balance(message: types.Message, state: FSMContext):
    if message.text == t('Confirm'):
        pass
    else:
        match = re.match('^-?\d{1,10}$', message.text)
        if match:
            async with state.proxy() as data:
                data['changeBalance'] = message.text
            await message.bot.send_message(message.from_user.id, t('Do you confirm?'),
                                           reply_markup=await inline_confirm('driverTopUpBalanceConfirm'))
        else:
            await message.bot.send_message(message.from_user.id, t("Only digits can be entered"))
            await message.bot.send_message(message.from_user.id, t("You can input from 1 to 10 digits"))


@dp.message_handler(state=FormDriver.phone)
async def process_driver_phone(message: types.Message, state: FSMContext):
    match = re.match(PHONE_MASK, message.text)
    if match:
        async with state.proxy() as data:
            data['phone'] = message.text
        if not HAS_CONFIRM_STEPS_DRIVER:
            try:
                await driver_registered(message, state)
                await menu_driver(message)
            except():
                await menu_driver(message)
                await message.bot.send_message(message.from_user.id, t("We can`t create your form"),
                                               reply_markup=await markup_remove())
            pass
        else:
            await message.bot.send_message(message.from_user.id, t('Do you confirm?'),
                                           reply_markup=await inline_confirm('driverPhoneSaved'))
        pass
    else:
        await message.bot.send_message(message.from_user.id, t("Number of digits is incorrect"))


@dp.message_handler(state=FormDriver.name)
async def process_driver_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    if not HAS_CONFIRM_STEPS_DRIVER:
        await set_driver_car_number(message)
    else:
        await message.bot.send_message(message.from_user.id, t('Do you confirm?'),
                                       reply_markup=await inline_confirm('driverNameSaved'))


@dp.message_handler(state=FormDriver.car_number)
async def process_driver_car_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['car_number'] = message.text
    if not HAS_CONFIRM_STEPS_DRIVER:
        await set_driver_phone(message)
    else:
        await message.bot.send_message(message.from_user.id, t('Do you confirm?'),
                                       reply_markup=await inline_confirm('driverCarNumberSaved'))


@dp.message_handler(state=FormDriver.wallet)
async def process_driver_wallet(message: types.Message, state: FSMContext):
    if message.text == t('Confirm'):
        async with state.proxy() as data:
            wallet = data['wallet']
        await state.finish()
        db.update_driver_wallet(message.from_user.id, wallet)
        await message.bot.send_message(message.from_user.id, t('Thank you, we will check the crediting of funds'),
                                       reply_markup=await markup_remove())
        await reminder_admin_about_payment(message)
    else:
        async with state.proxy() as data:
            data['wallet'] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton(t('Confirm')))
        await message.bot.send_message(message.from_user.id, t('Confirm entry or correct value'), reply_markup=markup)


@dp.message_handler(state=FormClient.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    if HAS_CONFIRM_STEPS_CLIENT:
        await message.bot.send_message(message.from_user.id, data['name'] + t(', do you confirm your name?'),
                                       reply_markup=await inline_confirm('clientNameSaved'))
    else:
        await set_phone(message)


@dp.message_handler(state=FormClient.phone)
async def process_phone(message: types.Message, state: FSMContext):
    print(re.compile('[^0-9+]').sub('', message.text))
    message.text = re.compile('[^0-9+]').sub('', message.text)
    match = re.match(PHONE_MASK, message.text)
    if match:
        async with state.proxy() as data:
            data['phone'] = message.text
        if HAS_CONFIRM_STEPS_CLIENT:
            await message.bot.send_message(message.from_user.id, t('Do you confirm your phone?'),
                                           reply_markup=await inline_confirm('clientPhoneSaved'))
        else:
            await state.finish()
            await set_departure(message, state)
        pass
    else:
        await message.bot.send_message(message.from_user.id, t("Number of digits is incorrect"))


@dp.message_handler(content_types=['location', 'venue'], state='*')
async def process_location(message, state: FSMContext):
    markup = types.InlineKeyboardMarkup(row_width=2)
    async with state.proxy() as data:
        location_type = data['locationType']
    if location_type == 'clientDptLoc':
        async with state.proxy() as data:
            data['departure_latitude'] = message.location.latitude
            data['departure_longitude'] = message.location.longitude
            pass
        if HAS_CONFIRM_STEPS_CLIENT:
            markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data='departureLocationSaved'))
            await message.bot.send_message(message.from_user.id, t("Confirm entry or correct value"),
                                           reply_markup=markup)
        else:
            await set_destination(message, state)
    elif location_type == 'clientDstLoc':
        async with state.proxy() as data:
            data['destination_latitude'] = message.location.latitude
            data['destination_longitude'] = message.location.longitude
            pass
        if HAS_CONFIRM_STEPS_CLIENT:
            markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data='destinationLocationSaved'))
            await message.bot.send_message(message.from_user.id, t("Confirm entry or correct value"),
                                           reply_markup=markup)
        else:
            await destination_location_saved(message, state)
    elif location_type == 'driverCurLoc':
        db.update_driver_location(message.from_user.id, message.location.latitude, message.location.longitude)
        if HAS_CONFIRM_STEPS_DRIVER:
            markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data='driverLocationSaved'))
            await message.bot.send_message(message.from_user.id, t("Confirm entry or correct value"),
                                           reply_markup=markup)
        else:
            await switch_driver_online(message)
    else:
        await message.bot.send_message(message.from_user.id, t("Sorry can`t saved data"))
    pass


# Если пользователь хочет указать локацию "текстом"
@dp.message_handler(content_types='text', state='*')
async def process_location(message: types.Message, state: FSMContext):
    if not DB_LOCATION_POSTFIX:
        return

    location_models = db.get_location_by_name(message.text)

    try:
        async with state.proxy() as data:
            if not data:
                return
            location_type = data['locationType']
            pass
    except UnboundLocalError:
        return
        pass
    markup = InlineKeyboardMarkup(row_width=3)

    if location_type == 'clientDptLoc':
        for locationModel in location_models:
            item = InlineKeyboardButton(text=str(locationModel['name_rus']),
                                        callback_data='departureLocationSavedByLocId_' + str(locationModel['id']))
            markup.add(item)
        item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='clientPhoneSaved')
        markup.add(item)
    elif location_type == 'clientDstLoc':
        for locationModel in location_models:
            item = InlineKeyboardButton(text=str(locationModel['name_rus']),
                                        callback_data='destinationLocationSavedByLocId_' + str(locationModel['id']))
            markup.add(item)
        item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='departureLocationSaved')
        markup.add(item)
    elif location_type == 'driverCurLoc':
        for locationModel in location_models:
            item = InlineKeyboardButton(text=str(locationModel['name_rus']),
                                        callback_data='driverLocationSavedByLocId_' + str(locationModel['id']))
            markup.add(item)
    else:
        await message.bot.send_message(message.from_user.id, "We can`t get type of location")

    if len(location_models):
        await message.bot.send_message(message.from_user.id, t("Found the following options"), reply_markup=markup)
    else:
        await message.bot.send_message(message.from_user.id, t("Could not find options"))
    pass


# return in kilometers
# deprecated
async def get_length_v2(dept_lt, dept_ln, dest_lt, dest_ln):
    distance = geodesic((dept_lt, dept_ln), (dest_lt, dest_ln)).kilometers
    return f'{distance:.2f}'


# return in meters
# deprecated
async def get_length(dept_lt, dept_ln, dest_lt, dest_ln):
    x1, y1 = dept_lt, dept_ln
    x2, y2 = dest_lt, dest_ln
    y = math.radians(float(y1 + y2) / 2)
    x = math.cos(y)
    n = abs(x1 - x2) * 111000 * x
    n2 = abs(y1 - y2) * 111000
    return float(round(math.sqrt(n * n + n2 * n2)))


async def set_length(order_data):
    order_local = {}
    gdata = await get_google_data(order_data)
    order_local['route_length'] = gdata['distance']['value']
    order_local['route_time'] = float(gdata['duration']['value'] / 60)
    order_local['amount_client'] = math.ceil((order_local['route_length'] / 1000) * RATE_1_KM)
    if order_local['amount_client'] < MIN_AMOUNT:
        order_local['amount_client'] = MIN_AMOUNT
    return order_local
    pass


async def start_menu(message):
    markup = InlineKeyboardMarkup(row_width=3)
    item10 = InlineKeyboardButton(text=t('I looking for a clients'), callback_data='driver')
    item20 = InlineKeyboardButton(t('I looking for a taxi'), callback_data='client')
    item30 = InlineKeyboardButton(t('Tell a friend about us') +' 👍', callback_data='inviteLink')

    driver_model = db.user_get_by_id(message.from_user.id)  # Тут не уточняем тип
    if driver_model['user_type'] == 'driver':
        markup.add(item10)
        item40 = InlineKeyboardButton('Переключиться на пассажира', callback_data='clientType')
    else:
        markup.add(item20)
        item40 = InlineKeyboardButton('Переключиться на водителя', callback_data='driverType')

    markup.add(item40).add(item30)
    if message.from_user.id in [5615867597, 419839605]:
        markup.add(InlineKeyboardButton("Админ - Показать статистику", callback_data='admin-short-statistic'))
        markup.add(InlineKeyboardButton("Админ - Пополнить баланс", callback_data='drivers'))
    if message.from_user.id == 419839605:
        markup.add(InlineKeyboardButton("Админ - Предложить зарегистрироваться В.",
                                        callback_data='driver-incentive-fill-form'))
        markup.add(InlineKeyboardButton(text='Админ - Coding' + ' 💻', callback_data='test'))
    await message.bot.send_message(message.from_user.id, t("Use the menu to get started"), reply_markup=markup)


async def menu_driver(message):
    markup = InlineKeyboardMarkup(row_width=3)

    # Subscribed labels
    item_label_1 = t('Driver form') + ' 📝'
    item_label_3 = t('Done orders')
    item_label_5 = t('My profile') + ' 🔖'
    item_label_6 = t("Go online") + ' 🟢'

    if not await is_subscribe_chat(message):
        item_label_1 += '🔒'
        item_label_3 += '🔒'
        item_label_5 += '🔒'
        item_label_6 += '🔒'

    # Subscribed items
    item1 = InlineKeyboardButton(text=item_label_1, callback_data='driver-form')
    item3 = InlineKeyboardButton(text=item_label_3, callback_data='driver-done-orders')
    item5 = InlineKeyboardButton(text=item_label_5, callback_data='driver-profile')
    item6 = InlineKeyboardButton(text=item_label_6, callback_data='switch-online')

    # Common items
    item2 = InlineKeyboardButton(text=t('Account'), callback_data='account')
    item4 = InlineKeyboardButton(text=t('How to top up') + ' ❓', callback_data='how-top-up-account')
    item7 = InlineKeyboardButton(text=t('Go offline 🔴'), callback_data='switch-offline')
    item71 = InlineKeyboardButton(text=t('Rules'), callback_data='driver-rules')
    item8 = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='back')
    item9 = InlineKeyboardButton(text=t('Drivers chat') + ' 💬', url='https://t.me/' + DRIVER_CHAT_TG)
    driver_model = db.user_get(message.from_user.id, 'driver')
    if not driver_model:
        await message.bot.send_message(message.from_user.id, "Can`t do it, begin to /start")
    else:
        if driver_model['status'] is not None:
            markup.add(item5, item1)
        else:
            markup.add(item1)
        markup.add(item2, item4)
        if driver_model['status'] is not None:
            if driver_model['status'] == 'offline':
                markup.add(item6)
            else:
                markup.add(item7)

        markup.add(item3)
        markup.add(item9)
        markup.add(item71)
        markup.add(item8)
        await message.bot.send_message(message.from_user.id, t("You are in the driver menu"), reply_markup=markup)


async def menu_client(message):
    order_cn = str(len(db.get_client_orders(message.from_user.id)))
    model_client = db.user_get(message.from_user.id, 'client')
    markup = InlineKeyboardMarkup(row_width=1)
    item10 = InlineKeyboardButton(text=t('Profile'), callback_data='client-profile')
    item20 = InlineKeyboardButton(text=t('Make an order') + ' 🚕', callback_data='make-order')
    # item30 = InlineKeyboardButton(text=t('Free drivers'), callback_data='free-drivers')
    item40 = InlineKeyboardButton(text=t('My orders') + ' (' + order_cn + ')', callback_data='client-orders_0_0_0')
    item42 = InlineKeyboardButton(text=t('Account'), callback_data='client-account')
    item45 = InlineKeyboardButton(text=t('Rules'), callback_data='client-rules')

    item50 = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='back')
    if model_client['name'] and model_client['phone']:
        markup.add(item10)
    markup.add(item20).add(item40).add(item42).add(item45).add(item50)
    await message.bot.send_message(message.from_user.id, t("You are in the client menu"), reply_markup=markup)


async def client_profile(message, client_id):
    model_client = db.user_get(client_id, 'client')
    if not model_client:
        await message.bot.send_message(message.from_user.id,
                                       t("Create at least one order and we will create your profile automatically"))
    else:
        caption = '\n'.join((
            '<b>Имя</b> ' + str(model_client['name']),
            '<b>Телефон</b> ' + str(model_client['phone']),
        ))
        markup_back = InlineKeyboardMarkup(row_width=1)
        markup_back.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client'))
        await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML', reply_markup=markup_back)
    pass


async def timer_for_client(message, on_timer=True):
    order_id = message.data
    order_model = db.get_order(order_id)
    if order_model['status'] != 'waiting':
        on_timer = False
    if on_timer:
        # По задумке цикл должен работать раз в минуту
        driver_model = db.get_near_driver(order_model['departure_latitude'], order_model['departure_longitude'],
                                          order_model['id'])
        if not driver_model:
            await message.bot.send_message(message.from_user.id, 'На линии пока нет водителей')
            return
        await get_order_card(message, driver_model['tg_user_id'], order_model, True)

        Timer(ORDER_REPEAT_TIME_SEC, timer_for_client, args=message)
        if not db.driver_order_exists(driver_model['tg_user_id'], order_id):
            db.driver_order_create(driver_model['tg_user_id'], order_id)
        db.driver_order_increment_cancel_cn(driver_model['tg_user_id'], order_id)
        client_model = db.user_get(order_model['client_id'], 'client')

        model_driver_order = db.get_driver_order(driver_model['tg_user_id'], order_id)
        if model_driver_order['driver_cancel_cn'] == 2:
            msg = 'Клиент: ' + await active_name(client_model) + " Заказ №: " + str(
                order_id) + " Предложен водителю: " + await active_name(driver_model)
            try:
                await message.bot.send_message(ADMIN_ID, msg, parse_mode='HTML')
            except BotBlocked:
                db.cancel_all_orders_after_kicked_user(ADMIN_ID)
                db.user_delete(ADMIN_ID)
                message_to_dev = 'Похоже что бот заблокирован пользователем <a href="tg://openmessage?user_id=' + ADMIN_ID + '">ADMIN_ID</a>. Надо назначить ADMIN_ID в конфиге'
                await message.bot.send_message(DEVELOPER_ID, message_to_dev)


# Вроде бы метод вообще не работает
async def driver_done_order(message):
    try:
        driver_id = db.get_driver_id(message.from_user.id)
        if not driver_id:
            await message.bot.send_message(message.from_user.id, t("Driver not found"))
        else:
            model_order = db.get_order_progress_by_driver_id(driver_id)
            if not model_order:
                await message.bot.send_message(message.from_user.id, t("You haven`t current order"))
            else:
                db.update_order_status(model_order['id'], 'done')
                model_order = db.get_order_progress_by_driver_id(driver_id)
                if model_order:
                    db.update_driver_status(message.from_user.id, 'route')
                else:
                    db.update_driver_status(message.from_user.id, 'offline')
                await message.bot.send_message(message.from_user.id,
                                               t('Congratulations! You have completed the order. You can go back to online to make a new order'))
    except():
        await message.bot.send_message(message.from_user.id, t("Can`t set done order status"))


async def switch_driver_online(message):
    # await message.bot.send_message(message.from_user.id, 'You need set a current location')
    db.update_driver_status(message.from_user.id, 'online')
    local_message = 'Вы онлайн. В течении {onlineTime:d} минут Вам будут приходить заказы'.format(
        onlineTime=round(ONLINE_TIME_SEC / 60))
    await message.bot.send_message(message.from_user.id, local_message)
    driver = db.user_get(message.from_user.id, 'driver')
    await notice_developer(message, driver, 3)
    # Запуск таймера Онлайн-статуса
    # выполнить функцию switchDriverOffline() через onlineTime секунд
    Timer(ONLINE_TIME_SEC, switch_driver_offline, args=message)
    pass


# Пока отключена
async def get_near_waiting_order(message, on_timer=True):
    driver_model = db.user_get(message.from_user.id, 'driver')
    if driver_model['status'] != 'online':
        on_timer = False
    model_order = db.order_get_near('waiting', driver_model['latitude'], driver_model['longitude'],
                                    message.from_user.id)
    if model_order:
        if not model_order['order_id']:
            model_order['order_id'] = 0
        if model_order['order_id']:
            model_order = db.get_order(model_order['order_id'])
            # Сюда можем отправлять только стандартную модель order
            await get_order_card(message, message.from_user.id, model_order)
    if on_timer:
        Timer(ORDER_REPEAT_TIME_SEC, get_near_waiting_order, args=message)


async def switch_driver_offline(message):
    driver_model = db.user_get(message.from_user.id, 'driver')
    model_order = db.get_order_progress_by_driver_id(message.from_user.id)
    if not driver_model:
        print('can`t switch to offline')
    elif model_order:
        db.update_driver_status(message.from_user.id, 'route')
        await message.bot.send_message(message.from_user.id, t("You switch route. Orders unavailable"),
                                       reply_markup=await markup_remove())
    else:
        if driver_model['status'] != 'offline':
            db.update_driver_status(message.from_user.id, 'offline')
        await message.bot.send_message(message.from_user.id, t("You switch offline. Orders unavailable"),
                                       reply_markup=await markup_remove())
    pass


async def get_order_card(message, driver_id, model_order, buttons=True):
    driver_model = db.user_get(driver_id, 'driver')
    model_driver_order = db.get_driver_order(driver_id, model_order['id'])
    model_client = db.user_get(model_order['client_id'], 'client')
    data = {
        'departure_latitude': driver_model['latitude'],
        'departure_longitude': driver_model['longitude'],
        'destination_latitude': model_order['departure_latitude'],
        'destination_longitude': model_order['departure_longitude']
    }
    gdata = await get_google_data(data)
    distance_to_client = gdata['distance']['text']
    markup = InlineKeyboardMarkup(row_width=3)
    if buttons:
        item1 = InlineKeyboardButton(text=t('Cancel') + ' ❌', callback_data='orderCancel_' + str(model_order['id']))
        item2 = InlineKeyboardButton(text=t('Confirm') + ' ✅', callback_data='orderConfirm_' + str(model_order['id']))
        markup.add(item1, item2)
    if not model_driver_order:
        driver_cancel_cn = 0
    else:
        driver_cancel_cn = model_driver_order['driver_cancel_cn']
    caption = [
        '<b>Заказ №' + str(model_order['id']) + '</b>',
        'Имя <b>' + str(model_client['name']) + '</b>',
        'Расстояние до клиента <b>' + str(distance_to_client) + '</b>',
        'Длина маршрута <b>' + str(model_order['route_length'] / 1000) + ' км.' + '</b>',
        'Рейтинг <b>' + (await get_rating(message) * '⭐') + '(' + str(await get_rating(message)) + '/5)</b>',
    ]
    if model_order['status'] == 'progress':
        caption.insert(2, 'Телефон <b>' + str(model_client['phone']) + '</b>')
    if MIN_BALANCE_AMOUNT > 0:
        caption.append('Стоимость <b>' + str(model_order['amount_client']) + ' ' + str(CURRENCY) + '</b>')
    if driver_cancel_cn > 0:
        caption.append('Вы отклоняли <b>' + str(driver_cancel_cn) + ' раз</b>', )
    caption = '\n'.join(caption)
    # Check that driver is not kicked
    try:
        await message.bot.send_message(driver_id, caption, parse_mode='HTML', reply_markup=markup)
    except BotBlocked:
        db.cancel_all_orders_after_kicked_user(driver_id)
        db.user_delete(driver_id)
        await message.bot.send_message(DEVELOPER_ID,
                                       'Бот заблокирован пользователем <a href="tg://openmessage?user_id=' + driver_id + '">' +
                                       driver_model['tg_first_name'] + '</a>')


async def get_order_card_client(message, order_model, cancel=False, confirm=False):
    client_model = db.user_get(order_model['client_id'], 'client')
    markup = InlineKeyboardMarkup(row_width=3)
    if cancel & (not order_model['driver_id']) & (order_model['status'] in ['create', 'waiting']):
        item1 = InlineKeyboardButton(text=t('Cancel trip') + ' ❌',
                                     callback_data='orderCancelClient_' + str(order_model['id']))
        markup.add(item1)
    if confirm:
        item2 = InlineKeyboardButton(text=t('Confirm') + ' ✅',
                                     callback_data='orderWaitingClient_' + str(order_model['id']))
        markup.add(item2)
    gdata = await get_google_data(order_model)
    caption = [
        '<b>Заказ №' + str(order_model['id']) + '</b>',
        'Имя <b>' + str(client_model['name']) + '</b>',
        'Длина маршрута <b>' + str(order_model['route_length'] / 1000) + ' км.' + '</b>',
        'Время в пути <b>' + str(gdata['duration']['text']) + '</b>',
        'Статус <b>' + str(db.statuses[order_model['status']]) + '</b>',
    ]
    if (order_model['status'] == 'waiting') & (order_model['driver_id'] == str(message.from_user.id)):
        caption.insert(1, 'Телефон <b>' + str(client_model['phone']) + '</b>')
    if MIN_BALANCE_AMOUNT > 0:
        caption.append('Стоимость <b>' + str(order_model['amount_client']) + ' ' + str(CURRENCY) + '</b>')
    caption = '\n'.join(caption)
    await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML', reply_markup=markup)


async def set_car_photo(message, state):
    async with state.proxy() as data:
        data['dir'] = 'cars/'
        data['savedKey'] = 'carPhotoSaved'
    await message.bot.send_message(message.from_user.id, t("Attach a photo of your car"),
                                   reply_markup=await markup_remove())


async def set_driver_photo(message, state):
    async with state.proxy() as data:
        data['dir'] = 'drivers/'
        data['savedKey'] = 'driverPhotoSaved'
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text='Пропустить шаг', callback_data='driverPhotoMissed'))
    await message.bot.send_message(message.from_user.id, t("You can attach your photo if you wish"),
                                   reply_markup=markup)


async def get_wallet_drivers(message):
    drivers = db.get_drivers_with_wallets()
    markup = InlineKeyboardMarkup(row_width=3)
    for driverModel in drivers:
        item = InlineKeyboardButton(
            text=str(driverModel['tg_user_id']) + ' - ' + str(driverModel['wallet']) + ' - ' + str(
                driverModel['tg_first_name']), callback_data='wallet_' + str(driverModel['wallet']))
        markup.add(item)
    await message.bot.send_message(message.from_user.id, 'Выберите водителя', reply_markup=markup)


async def set_driver_top_up_balance(message, wallet, state):
    drivers = len(db.get_drivers_by_wallet(wallet))
    if drivers > 1:
        local_message = "Нельзя пополнить кошелек поскольку найдено {drivers:d} водителей с таким кошельком"
        local_message = local_message.format(drivers=drivers)
        await message.bot.send_message(message.from_user.id, local_message, reply_markup=await markup_remove())
    else:
        await FormDriver.balance.set()
        async with state.proxy() as data:
            data['wallet'] = wallet
        await message.bot.send_message(message.from_user.id, t("Top up driver balance"),
                                       reply_markup=await markup_remove())


async def set_driver_phone(message):
    await FormDriver.phone.set()
    await message.bot.send_message(message.from_user.id, t("Enter phone number") + '\nℹ<i>' + t(
        "Examples of phone number: +905331234567, +79031234567") + '</i>', parse_mode='HTML',
                                   reply_markup=await markup_remove())


async def set_driver_name(message):
    await FormDriver.name.set()
    await message.bot.send_message(message.from_user.id, t("What's your name?"),
                                   reply_markup=types.ReplyKeyboardRemove())


async def set_driver_car_number(message):
    await FormDriver.car_number.set()
    await message.bot.send_message(message.from_user.id, t("What's your car number?"),
                                   reply_markup=await markup_remove())


async def get_active_orders(message):
    waiting_orders = db.get_orders('waiting')
    if len(waiting_orders) == 0:
        await message.bot.send_message(message.from_user.id, t('Has not waiting orders'))
    else:
        for row in waiting_orders:
            if not row['dt_order']:
                date_format = 'Не указана'
            else:
                date_format = datetime.strptime(str(row['dt_order']), "%Y-%m-%d %H:%M:%S").strftime("%H:%M %d.%m.%Y")
            text = [
                'Статус <b>' + row['status'] + '</b>',
                'Дата <b>' + str(date_format) + '</b>',
                'Длина маршрута, км. <b>' + str(row['route_length'] / 1000) + '</b>',
                'Время поездки, мин. <b>' + str(row['route_time']) + '</b>'
            ]
            if MIN_BALANCE_AMOUNT > 0:
                text.append('Стоимость, ' + str(CURRENCY) + ' <b>' + str(row['amount_client']) + '</b>')
            text = '\n'.join(text)
            # await message.bot.send_location(message.from_user.id, row['departure_latitude'], row['departure_longitude'])
            await message.bot.send_message(message.from_user.id, text,
                                           reply_markup=await book_order('bookOrder_' + str(row['id'])))
            pass


async def get_driver_done_orders(message: Message):
    model_orders = db.get_orders('done')
    if len(model_orders) == 0:
        await message.bot.send_message(message.from_user.id, t('Has not done orders'))
    else:
        await menu_driver(message)
        for row in model_orders:
            if not row['dt_order']:
                date_format = 'Не указана'
            else:
                date_format = datetime.strptime(str(row['dt_order']), "%Y-%m-%d %H:%M:%S").strftime("%H:%M %d.%m.%Y")
            text = [
                '<b>Заказ № ' + str(row['id']) + '</b>',
                'Статус <b>' + db.statuses[row['status']] + '</b>',
                'Дата <b>' + str(date_format) + '</b>',
                'Длина маршрута, км. <b>' + str(row['route_length'] / 1000) + '</b>',
                'Время поездки, мин. <b>' + str(row['route_time']) + '</b>'
            ]
            if MIN_BALANCE_AMOUNT > 0:
                text.append('Стоимость, ' + str(CURRENCY) + ' <b>' + str(row['amount_client']) + '</b>')
            text = '\n'.join(text)
            await message.bot.send_message(message.from_user.id, text, reply_markup=await markup_remove())
            pass


async def set_driver_wallet(message):
    driver_model = db.user_get(message.from_user.id, 'driver')
    if not driver_model:
        await message.bot.send_message(message.from_user.id, t("You need fill the form"))
    else:
        await FormDriver.wallet.set()
        await message.bot.send_message(message.from_user.id, t("Enter the sender's wallet"))


async def set_name(message, state):
    await FormClient.name.set()

    client_model = db.user_get(message.from_user.id, 'client')
    markup = InlineKeyboardMarkup(row_width=1)
    if client_model['name']:
        name_exists = True
    else:
        name_exists = False
    if client_model['phone']:
        phone_exists = True
    else:
        phone_exists = False
    name_message = t("What's your name?")
    if name_exists & phone_exists:
        async with state.proxy() as data:
            data['name'] = client_model['name']
            data['phone'] = client_model['phone']
            pass
        markup.add(InlineKeyboardButton(text=t('Leave unchanged'), callback_data='clientPhoneSaved'))
        name_message += '. Вы можете оставить без изменений имя и телефон'
    await message.bot.send_message(message.from_user.id, name_message, reply_markup=markup)


async def set_phone(message):
    await FormClient.phone.set()

    client_model = db.user_get(message.from_user.id, 'client')
    markup = InlineKeyboardMarkup(row_width=6)
    if client_model['phone']:
        markup.add(InlineKeyboardButton(text='Мой номер ' + client_model['phone'], callback_data='clientPhoneSaved'))

    await message.bot.send_message(message.from_user.id, t("Enter phone number") + '\nℹ<i>' + t(
        "Examples of phone number: +905331234567, +79031234567") + '</i>', parse_mode='HTML', reply_markup=markup)


async def set_driver_location(message, state: FSMContext):
    async with state.proxy() as data:
        data['locationType'] = 'driverCurLoc'
    await message.bot.send_message(message.from_user.id, t('Set current location'))
    pass


async def set_departure(message, state: FSMContext):
    async with state.proxy() as data:
        data['locationType'] = 'clientDptLoc'
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text=t('Catalog'), callback_data='catalog_0'))
    if DB_LOCATION_POSTFIX:
        text = t("Set departure location") + t(
            "Use ONE of 3 methods\n\n1️⃣ method - write the name and send \n2️⃣ method - select the name in the CATALOGUE OF PLACES \n3️⃣ method - indicate the coordinates on the map via PAPERCLIP + LOCATION")
    else:
        text = t("Set departure location") + t(
            "Use the following method.\n\nSpecify coordinates on the map using PAPERCLIP+LOCATION")
        markup = None
    await bot.send_message(message.from_user.id, text=text, parse_mode='html', reply_markup=markup)
    pass


async def set_destination(message, state: FSMContext):
    async with state.proxy() as data:
        data['locationType'] = 'clientDstLoc'
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text=t('Catalog'), callback_data='catalog_0'))
    await message.bot.send_message(message.from_user.id, t("Set destination location"), parse_mode='html',
                                   reply_markup=markup)

    pass


async def destination_location_saved(message, state: FSMContext):
    data_client = {}
    data_order = {}
    client_model = db.user_get(message.from_user.id, 'client')

    async with state.proxy() as data:
        if 'name' in data:
            data_client['name'] = data['name']
        else:
            data_client['name'] = client_model['name']
        if 'phone' in data:
            data_client['phone'] = data['phone']
        else:
            data_client['phone'] = client_model['phone']
        data_order['departure_latitude'] = data['departure_latitude']
        data_order['departure_longitude'] = data['departure_longitude']
        data_order['destination_latitude'] = data['destination_latitude']
        data_order['destination_longitude'] = data['destination_longitude']
        pass

    len_params = await set_length(data_order)
    data_order['client_id'] = message.from_user.id
    data_order['status'] = 'create'
    data_order['dt_order'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_order['amount_client'] = len_params['amount_client']
    data_order['route_length'] = len_params['route_length']
    data_order['route_time'] = len_params['route_time']

    await state.finish()

    dump(data_order)
    order_id = db.create_order(data_order)
    # Оплата агенту за приведенного клиента
    await referer_payed(message, 'client')

    await notice_developer(message, client_model, 4)

    db.update_client(message.from_user.id, data_client)

    model_order = db.get_order(order_id)
    await get_order_card_client(message, model_order, True, True)


async def send_client_notification(message, order_model):
    # Ваш заказ принят. Водитель выехал к Вам
    await message.bot.send_message(order_model['client_id'], t("Your order is accepted. The driver drove to you"))
    await driver_profile(message, order_model['driver_id'], order_model['client_id'], True)

    markup_done_order = types.InlineKeyboardMarkup(row_width=1)
    markup_done_order.add(types.InlineKeyboardButton(text=t('Done current order'),
                                                     callback_data='clientDoneOrder_' + str(order_model['id'])))
    await message.bot.send_message(order_model['client_id'],
                                   t('When you reach your destination, please click on the button to complete the current order'),
                                   reply_markup=markup_done_order)
    pass


async def get_categories(message, parent_id, state: FSMContext):
    location_models = db.get_locations_by_category_id(parent_id)
    markup = InlineKeyboardMarkup(row_width=2)
    async with state.proxy() as data:
        if not data:
            item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client')
            markup.add(item)
            await message.bot.send_message(message.from_user.id, '🤔 Хм, попробуйте начать заказ с начала',
                                           reply_markup=markup)
            return
        location_type = data['locationType']
    if len(location_models) == 0:
        category_models = db.get_categories(parent_id)
        cat_message = t("Select category")
        if len(category_models) == 0:
            cat_message = t("Could not find options")
            markup.add(types.InlineKeyboardButton(text=t('Catalog'), callback_data='catalog_0'))
        else:
            for categoryModel in category_models:
                item = InlineKeyboardButton(text=str(categoryModel['name']),
                                            callback_data='catalog_' + str(categoryModel['id']))
                markup.add(item)
                if categoryModel['parent_id']:
                    cat_message = t('Select subcategory')
            if parent_id != 0:
                item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='catalog_0')
                markup.add(item)
            else:
                item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client')
                markup.add(item)
    else:
        cat_message = t("Found locations")
        for locationModel in location_models:
            if location_type == 'clientDptLoc':
                data = 'departureLocationSavedByLocId_' + str(locationModel['id'])
            elif location_type == 'clientDstLoc':
                data = 'destinationLocationSavedByLocId_' + str(locationModel['id'])
            item = InlineKeyboardButton(text=str(locationModel['name_rus']), callback_data=data)
            markup.add(item)
        item = InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='catalog_0')
        markup.add(item)
    await message.bot.send_message(message.from_user.id, cat_message, reply_markup=markup)


async def reminder_admin_about_payment(message):
    """
    Напоминание админу о поступившей оплате
    :param message:
    """
    model_driver = db.user_get(message.from_user.id, 'driver')
    text = t('It is necessary to check the payment')
    text += "\nПользователь: " + await active_name(model_driver)
    await bot.send_message(DEVELOPER_ID, text, parse_mode='HTML')
    await bot.send_message(DEVELOPER_ID, 'Кошелек: `' + model_driver['wallet'] + '`', parse_mode='MARKDOWN')


# Таймер для асинхронных методов
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


async def client_registered(message):
    try:
        await message.bot.send_message(message.from_user.id,
                                       '🤔 Секундочку... ' + t("We are already looking for drivers for you.."))
        model_client = db.user_get_by_id(message.from_user.id)
        await notice_developer(message, model_client, 5)
    except():
        print('error method clientRegistered(message)')
        await goto_start(message)


async def driver_registered(message, state: FSMContext):
    driver_data = {}
    async with state.proxy() as data:
        driver_data['name'] = data['name']
        driver_data['phone'] = data['phone']
        driver_data['car_number'] = data['car_number']
        driver_data['status'] = 'offline'

    await state.finish()
    db.update_driver(message.from_user.id, driver_data)
    # time.sleep(2)
    await message.bot.send_message(message.from_user.id, t("Your profile is saved"))
    # Оплата агенту за приведенного клиента
    await referer_payed(message, 'driver')


async def invite_link(message):
    await message.bot.send_message(message.from_user.id,
                                   'Ниже отправлен текст сообщения. Скопируйте другу, которого хотите пригласить. Реферальная ссылка позволит Вам получить бонус за приведенного друга')
    await message.bot.send_message(
        message.from_user.id,
        'Привет. Хочу поделиться новым сервисом по поиску Такси https://t.me/' + BOT_ID + '?start=' + str(
            message.from_user.id))


async def delete_message(d_message):
    await d_message.bot.delete_message(d_message.from_user.id, d_message.message_id)
    pass


async def get_rating(message):
    model_orders_user_all = len(db.get_client_orders(message.from_user.id))
    model_orders_user_done = len(db.get_done_orders_by_client_id(message.from_user.id))
    if model_orders_user_all == 0:
        return 5
    return round(model_orders_user_done / model_orders_user_all * 5)


async def get_wiki_bot_info(message, receiver_id):
    if BOT_ID != "TaxiNCBot":
        return
    caption = '''
Навигатор по Северному Кипру WikiBot 🏝🇹🇷
Все услуги и места в одном месте 🤖
Каждый из вас может разместить в нем свою услугу или объявление - бесплатно😉'''
    bio = BytesIO()
    image = Image.open('images/wikiBot.jpg')
    image.save(bio, 'JPEG')
    bio.seek(0)

    wiki = InlineKeyboardMarkup(row_width=1)
    wiki.add(InlineKeyboardButton(text='Перейти в WikiBot', url='https://cazi.me/7R6XM'))
    wiki.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='client'))
    await message.bot.send_photo(receiver_id, bio, caption=caption, parse_mode='HTML', reply_markup=wiki)


async def driver_rules(message):
    caption = '''<b>Для водителей</b>
Бот поможет удобно находить людей желающих добраться из точки А в точку Б.

ℹ️ бот бесплатный для водителей!
Для возможности принимать заказы должна быть заполнена АНКЕТА.
 • анкета
    ⁃ Сделайте фото автомобиля. На фото должно быть хорошо видно ваш автомобиль, чтобы клиент мог найти его среди других автомобилей на улице
    ⁃ Укажите номер автомобиля, достаточно цифр
    ⁃ Укажите номер телефона по которому клиенты смогут связываться с вами

По любым вопросам связывайтесь с администратором {adminTg:s}
'''
    caption_commission = '''
 • Комиссия
Комиссия составляет {percent:d}% от суммы заказа.
    '''
    if PERCENT > 0:
        caption_commission += 'Комиссия списывается с вашего личного баланса'
    caption += caption_commission
    caption = caption.format(
        minBalanceAmount=MIN_BALANCE_AMOUNT,
        percent=PERCENT,
        adminTg=ADMIN_TG,
    )
    back_driver_menu = InlineKeyboardMarkup(row_width=1)
    back_driver_menu.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='driver'))
    await message.bot.send_message(message.from_user.id, caption, reply_markup=back_driver_menu)
    pass


async def driver_profile(message, driver_id, user_id, show_phone=False, show_return_button=False):
    driver_model = db.user_get(driver_id, 'driver')
    if not driver_model:
        await message.bot.send_message(user_id, "Can`t do it, begin to /start")
    else:
        Path("merged").mkdir(parents=True, exist_ok=True)
        car = 'cars/' + str(driver_id) + '.jpg'
        driver_file_name = 'drivers/' + str(driver_id) + '.jpg'
        file_car_exist = exists(car)
        file_driver_exist = exists(driver_file_name)

        # Фото водителя не обязательный параметр
        if not file_driver_exist:
            driver_file_name = 'images/anonim-user.jpg'
            file_driver_exist = True

        status_icon = str(db.statuses[driver_model['status']])
        caption = [
            '<b>Имя</b> ' + str(driver_model['name']),
            '<b>Статус</b> ' + str(status_icon),
            '<b>Номер машины</b> ' + str(driver_model['car_number']),
        ]
        if show_phone:
            caption.insert(1, '<b>Телефон</b> ' + str(driver_model['phone']))
        caption = '\n'.join(caption)
        version_merge = 0
        merged_image = ''

        if file_car_exist & file_driver_exist:
            x = 240
            y = 320
            image1 = Image.open(car)
            image2 = Image.open(driver_file_name)

            if image1.size[0] < image1.size[1]:
                if image2.size[0] < image2.size[1]:
                    version_merge = 1
                    image1 = image1.resize((x, y))
                    image2 = image2.resize((x, y))
                    merged_image = Image.new(mode='RGB', size=(x * 2, y), color=(250, 250, 250))
                    merged_image.paste(image1, (0, 0))
                    merged_image.paste(image2, (x, 0))
                elif image2.size[0] > image2.size[1]:
                    version_merge = 4
                    yy = int(y / 0.75)
                    image1 = image1.resize((y, yy))
                    image2 = image2.resize((y, x))
                    merged_image = Image.new(mode='RGB', size=(y, x + yy), color=(250, 250, 250))
                    merged_image.paste(image1, (0, 0))
                    merged_image.paste(image2, (0, yy))
                elif image2.size[0] == image2.size[1]:
                    version_merge = 6
                    image1 = image1.resize((x, y))
                    image2 = image2.resize((y, y))
                    merged_image = Image.new(mode='RGB', size=(x + y, y), color=(250, 250, 250))
                    merged_image.paste(image1, (0, 0))
                    merged_image.paste(image2, (x, 0))
            elif image1.size[0] > image1.size[1]:
                if image2.size[0] > image2.size[1]:
                    version_merge = 2
                    image1 = image1.resize((y, x))
                    image2 = image2.resize((y, x))
                    merged_image = Image.new(mode='RGB', size=(y, x * 2), color=(250, 250, 250))
                    merged_image.paste(image1, (0, 0))
                    merged_image.paste(image2, (0, x))
                elif image2.size[0] < image2.size[1]:
                    version_merge = 3
                    yy = int(y / 0.75)
                    image1 = image1.resize((y, x))
                    image2 = image2.resize((y, yy))
                    merged_image = Image.new(mode='RGB', size=(y, yy + x), color=(250, 250, 250))
                    merged_image.paste(image1, (0, 0))
                    merged_image.paste(image2, (0, x))
                elif image2.size[0] == image2.size[1]:
                    version_merge = 7
                    image1 = image1.resize((y, x))
                    image2 = image2.resize((y, y))
                    merged_image = Image.new(mode='RGB', size=(y, y + x), color=(250, 250, 250))
                    merged_image.paste(image1, (0, 0))
                    merged_image.paste(image2, (0, x))
            elif image1.size[0] == image1.size[1] & image2.size[0] == image2.size[1]:
                version_merge = 5
                image1 = image1.resize((y, y))
                image2 = image2.resize((y, y))
                merged_image = Image.new(mode='RGB', size=(y + y, y), color=(250, 250, 250))
                merged_image.paste(image1, (0, 0))
                merged_image.paste(image2, (y, 0))

        back_driver_menu = InlineKeyboardMarkup(row_width=1)
        if show_return_button:
            back_driver_menu.add(InlineKeyboardButton(text=t('Back') + ' ↩', callback_data='driver'))

        if version_merge > 0:

            bio = BytesIO()
            bio.name = 'merged/' + str(driver_id) + '.jpg'
            merged_image.save(bio, 'JPEG')
            bio.seek(0)
            await message.bot.send_photo(user_id, bio, caption=caption, parse_mode='HTML',
                                         reply_markup=back_driver_menu)
            print('versionMerge: ' + str(version_merge))
        else:
            await message.bot.send_message(user_id, caption, parse_mode='HTML', reply_markup=back_driver_menu)
    pass


async def short_statistic(message):
    driver_all_models = db.get_drivers()
    driver_registered_models = db.get_drivers_registered()
    drivers_online_models = db.get_drivers_by_status('online')
    client_all_models = db.get_clients()
    order_waiting_models = db.get_orders('waiting')
    caption = [
        '<b>Короткая статистика</b>',
        'Всего водителей <b>' + str(len(driver_all_models)) + '</b>',
        'Водителей с анкетой <b>' + str(len(driver_registered_models)) + '</b>',
        'Онлайн водителей <b>' + str(len(drivers_online_models)) + '</b>',
        'Всего клиентов <b>' + str(len(client_all_models)) + '</b>',
        'Заказов в ожидании <b>' + str(len(order_waiting_models)) + '</b>',
    ]
    caption = '\n'.join(caption)
    await message.bot.send_message(message.from_user.id, caption, parse_mode='HTML')


async def active_name(user_model):
    return '<a href="tg://openmessage?user_id=' + str(user_model['tg_user_id']) + '">' + str(
        user_model['tg_first_name']) + '</a>'


async def incentive_driver_fill_form(message):
    unregistered_driver_models = db.get_drivers_unregistered()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text='Заполнить анкету', callback_data='driver-form'))
    caption = 'Мы обнаружили что вы заходили в наш бот но при этом не прошли процесс регистрации водителя. \n\nХотим предложить вам заполнить анкету водителя. \n\nПосле заполнения анкеты Вы сможете пользоваться ботом в качестве водителя, выходить на линию и получать заказы. \n\nЕсли у вас имеются вопросы по заполнению анкеты, напишите нам ' + ADMIN_TG
    send_cn = 0
    for unregisteredDriverModel in unregistered_driver_models:
        try:
            await message.bot.send_message(unregisteredDriverModel['tg_user_id'], caption, parse_mode='HTML',
                                           reply_markup=markup)
            send_cn = send_cn + 1
        except():
            await message.bot.send_message(message.from_user.id, 'Не удалось отправить сообщение контакту @' + str(
                unregisteredDriverModel['tg_first_name']) + ' (' + str(unregisteredDriverModel['tg_user_id']) + ')')
    await message.bot.send_message(5615867597, 'Предложение о регистрации доставлено ' + str(send_cn) + ' водителям')


async def notice_developer(m, user, notice_type):
    if m.from_user.id == DEVELOPER_ID:
        return
    text = await active_name(user)
    if user['tg_username']:
        text += ' @' + user['tg_username']
    if notice_type == 1:
        text += ' зарегистрировался'
    elif notice_type == 2:
        text += ' зашел посмотреть'
    elif notice_type == 3:
        text += ' вышел на линию как водитель'
    elif notice_type == 4:
        text += ' создал заказ как клиент'
    elif notice_type == 5:
        text += ' подтвердил заказ как клиент'

    try:
        await m.bot.send_message(DEVELOPER_ID, text, parse_mode='HTML')
    except UnboundLocalError:
        print('Except: notice_developer')
        pass


async def goto_start(message):
    await message.bot.send_message(message.from_user.id, t("can`t do it, start with the /start command"))


async def standard_confirm():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(t('Confirm')))
    return markup


async def inline_confirm(callback_data):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text=t('Confirm'), callback_data=callback_data))
    return markup


async def markup_remove():
    return types.ReplyKeyboardRemove()


async def book_order(callback_data):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text=t('Book an order'), callback_data=callback_data))
    return markup


async def get_google_data(locations_data):
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
    result = gmaps.directions(
        (locations_data['departure_latitude'], locations_data['departure_longitude']),
        (locations_data['destination_latitude'], locations_data['destination_longitude']),
        language=LANGUAGE
    )
    result_format = {'distance': result[0]['legs'][0]['distance'], 'duration': result[0]['legs'][0]['duration'],
                     'start_address': result[0]['legs'][0]['start_address'],
                     'end_address': result[0]['legs'][0]['end_address'], 'summary': result[0]['summary']}
    return result_format


"""Подписка и реферальная система"""


# Проверка подписки на чат
async def is_subscribe_chat(m):
    if not ALLOW_SUBSCRIBE:
        return True
    try:
        member = await bot.get_chat_member(chat_id='@' + DRIVER_CHAT_TG, user_id=m.from_user.id)
        if member.status != 'left':
            return True
    except UnboundLocalError:
        pass
    return False


# Подписка на чат
async def suggest_subscribe_chat(message):
    if not ALLOW_SUBSCRIBE:
        return
    chat = await bot.get_chat(chat_id='@' + DRIVER_CHAT_TG)
    item = InlineKeyboardButton(text=chat.title + ' 💬', url='https://t.me/' + DRIVER_CHAT_TG)
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(item)
    await bot.send_message(message.from_user.id, "🔒Чтобы пользоваться ботом, вступите, пожалуйста в чат водителей",
                           reply_markup=markup)


# Проверка платной подписки водителя на неделю
async def is_subscribe_driver_week(message):
    if not SUBSCRIBE_WEEK_AMOUNT:
        return True
    model_driver = db.user_get_by_id(message.from_user.id)
    if not model_driver:
        return False
    if not model_driver['dt_subscribe_until']:
        return False
    if model_driver['dt_subscribe_until'] > datetime.now():
        return True
    return False
    pass


# Платная подписка водителя на неделю
async def suggest_subscribe_driver_week():
    pass


# Оплата агенту за приведенного клиента
async def referer_payed(message, user_type):
    user_model = db.user_get(message.from_user.id, user_type)
    if user_model['referer_user_id'] and user_model['referer_payed'] is None:
        referer_model = db.user_get(user_model['referer_user_id'], user_type)
        referer_balance_updated = False
        if referer_model:
            if referer_model['balance'] is None:
                referer_model['balance'] = 0
            db.update_driver_balance(referer_model['tg_user_id'], referer_model['balance'] + RATE_REFERER)
            referer_balance_updated = True
        if referer_balance_updated:
            db.update_driver_referer_payed(message.from_user.id)
            local_message = "The user you invited has registered. You have received a bonus {rateReferer:d} {currencyWallet:s}"
            local_message = local_message.format(
                rateReferer=RATE_REFERER,
                currencyWallet=CURRENCY_WALLET
            )
            await message.bot.send_message(referer_model['tg_user_id'], local_message)
    print('refererPayed() success done')
    pass


# Добавление реферальной ссылки новому пользователю
async def add_referer(m):
    user_id = m.from_user.id
    # Проверяем наличие закрепленного агента за пользователем
    model_driver = db.user_get_by_id(user_id)  # тут не уточняем тип
    if not model_driver['referer_user_id']:
        referer_user_id = None
        # Проверяем наличие хоть какой-то дополнительной информации из ссылки
        if " " in m.text:
            referrer_candidate = m.text.split()[1]

            # Пробуем преобразовать строку в число
            try:
                referrer_candidate = int(referrer_candidate)

                # Проверяем на несоответствие TG ID пользователя TG ID агента
                # Также проверяем, есть ли такой агент в базе данных
                if user_id != referrer_candidate and db.driver_exists(referrer_candidate):
                    referer_user_id = referrer_candidate

            except ValueError:
                pass

            # Do update referer_user_id
            db.update_driver_referer(m.from_user.id, referer_user_id)
    pass


# Приглашение в бот пользователей
async def invite_users(m):
    if INVITE_INTERVAL == 0:
        return
    # 1 step driver cn
    driver_cn = len(db.get_drivers())

    # 2 stem client cn
    client_cn = len(db.get_clients())

    # 3 step ratio
    ratio = driver_cn / client_cn

    looking_clients = '''Есть свободные водители. Приглашаем заказать такси через наш сервис
- Анонимно
- Безопасно
- Выгодно'''

    looking_drivers = '''Есть несколько человек, желающих заказать такси. Ты можешь получить доп. доход, в качестве водителя
- Даем заказ рядом с тобой
- Бесплатный промо-период'''

    chats = [
        {'alias': 'wifiwife', 'thread': None},
        # {'alias': 'project_Caesar', 'thread': 20},

        # {'alias': 'severniy_kipr_chat', 'thread': 2772},  # Свой чат по СК
    ]

    # if ratio bigger than 1, send message to clients
    if ratio > 1:
        for chat in chats:
            await api_user.send_message(
                chat['alias'],
                looking_clients,
                None,
                None,
                None,
                None,
                chat['thread'])
    # if ratio smaller than 1, send message to drivers
    if ratio < 1:
        for chat in chats:
            await api_user.send_message(
                chat['alias'],
                looking_drivers,
                None,
                None,
                None,
                None,
                chat['thread'])

    # Запуск таймера
    # выполнить функцию invite_users(m) через INVITE_INTERVAL секунд
    Timer(INVITE_INTERVAL, invite_users, args=m)
    pass


# Проверка, что пользователь пригласил минимальное кол-во знакомых
async def is_referer_users(m):
    if INVITE_COUNT == 0:
        return True

    # Запрос кол-ва пользователей с referer_user_id = user_id
    cn_referer_user = db.user_cn_referer(m.from_user.id)

    return cn_referer_user >= INVITE_COUNT
    pass


# Необходимость пригласить минимальное кол-во знакомых
async def need_referer_users(m: Message):
    if INVITE_COUNT == 0:
        return
    caption = [
        'Наш бот бесплатный.',
        'Но для работы в системе мы просим вас пригласить знакомых.',
        'Вернитесь назад в основное меню и нажмите кнопку',
        '«' + t('Tell a friend about us') + '».',
        'Пригласите пожалуйста ' + str(INVITE_COUNT) + ' чел. и вам станет доступна работа системы',
    ]
    caption = ' '.join(caption)
    await m.bot.send_message(m.from_user.id, '' + caption, parse_mode='HTML')
    pass


# Отладка
async def test_function(message):
    dictionary = message.message.__dict__
    dump(dictionary)
    pass


def dump(v):
    if type(v) == dict:
        pprint.pprint(v, indent=2)
    else:
        print(json.dumps(v, sort_keys=True, indent=4))
