import logging
from aiogram import types, Dispatcher
from aiogram.types.message import ContentType

from config import PAYMENT_TOKEN
from dispatcher import bot

# log
logging.basicConfig(level=logging.INFO)

def register_handlers(dp: Dispatcher):
    # buy
    @dp.message_handler(commands=["buy"])
    async def buy(message: types.Message):
        price = types.LabeledPrice(label='Подписка на 1 месяц за 100 рублей.', amount=100 * 100)  # В копейках (руб)

        if PAYMENT_TOKEN.split(':')[1] == 'TEST':
            await bot.send_message(message.chat.id, "Тестовый платеж!!!")
        await bot.send_invoice(message.from_user.id,
                               title="Подписка на бота",
                               description="Активация подписки на бота на 1 месяц",
                               provider_token=PAYMENT_TOKEN,
                               currency="rub",
                               photo_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRi1Jotlc8TCjejrCrXFrYufxd2lkQe4eK0nw&s",
                               photo_width="274",
                               photo_height="171",
                               photo_size="171",
                               is_flexible=False,
                               prices=[price],
                               payload="test-invoice-payload",
                               start_parameter="one-month-subscript")



    # pre checkout (must be answered in 10 seconds)
    @dp.pre_checkout_query_handler(lambda query: True)
    async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
        await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)



    # successful payment
    @dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
    async def successful_payment(message: types.Message):
        print("SUCCESSFUL PAYMENT:")
        payment_info = message.successful_payment.to_python()
        for k, v in payment_info.items():
            print(f"{k} = {v}")
        await bot.send_message(message.chat.id,
                               f"Платеж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!")