import config
from config import *


language = {
    'RU':{
        "Account":"Баланс",
        "Attach a photo of your car": "Прикрепите фото Вашего автомобиля",
        "Back":"Назад",
        "Balance is filled":"Баланс заполнен",
        "can`t do it, start with the /start command":"Не могу это сделать, начни с команды /start",
        "Can`t set done order status":"Не могу установить статус Выполнен",
        "can`t switch order to done":"Не удалось переключить заказ в Выполнено",
        "Confirm entry or correct value": "Подтвердите ввод или исправьте значение",
        "Confirm": "Подтвердить",
        "Confirm the transfer":"Подтвердить перевод",
        "Congratulations! You have completed the order. You can go back to online to make a new order":"Поздравляем! Вы выполнили заказ. Вы можете вернуться в онлайн, чтобы сделать новый заказ",
        "Client form": "Анкета",
        "Client not found":"Клиент не найден",
        "Client profile not found":"Профиль клиента не найден",
        "Create at least one order and we will create your profile automatically":"Создайте хотя бы один заказ и мы создадим ваш профиль автоматически",
        "Departure here": "Забрать здесь",
        "Destination here":"Отвезти сюда",
        "Driver form":"Анкета",
        "Driver not found":"Водитель не найден",
        "Done current order":"Завершить текущий заказ",
        "Done orders":"Выполненные заказы",
        "Do you confirm your phone?": "Подтвердите телефон",
        "Do you confirm your amount?": "Подтвердите сумму",
        "Do you confirm?": "Подтвердите",
        "Driver":"Водитель",
        "Enter phone number?": "Укажите номер телефона?",
        "Enter the sender's wallet":"Укажите кошелек отправителя",
        "Examples of phone number: +905331234567, +79031234567":"Примеры номеров: +905331234567, +79031234567",
        "Free drivers": "Свободные водители",
        "Go online 🟢":"Выйти на линию 🟢",
        "Go offline 🔴":"Отключиться 🔴",
        "Has not done orders":"Нету завершенных заказов",
        "Has not waiting orders":"Нету активных заказов",
        "How much do you want to pay?": "Сколько Вы готовы заплатить?",
        "I looking for a clients": "Я Водитель",
        "I looking for a taxi": "Я Пассажир",
        "I dont understand this message. Use the menu to get started": "Я не понимаю это сообщение. Используйте меню чтобы начать",
        "Look for a driver": "Иcкать водителя",
        "May be entered number only": "Укажите число",
        "Make an order":"Сделать заказ",
        "My current location": "Мое текущее местоположение",
        "My destination location": "Мой пункт назначения",
        "My orders": "Мои заказы",
        "Number of digits is incorrect": "Кол-во цифр от 11 до 12",
        "You can input from 1 to 10 digits": "Можно ввести от 1 до 10 цифр",
        "Only digits can be entered": "Могут быть указаны только цифры",
        "Only digits can be entered as a phone number": "В качестве номера телефона могут быть указаны только цифры",
        "Only digits can be entered as a amount": "В качестве суммы могут быть указаны только цифры",
        "Order can not be taken":"Этот заказ нельзя взять",
        "Order is cancel":"Заказ отменен",
        "Order is done": "Заказ выполнен",
        "Order is close already":"Заказ уже завершен",
        "Order not found":"Заказ не найден",
        ", do you confirm your name?": ", подтвердите имя?",
        "Order":"Заказ",
        "Orders":"Заказы",
        "Phone is required, set it in client form":"Телефон обязателен для заполнения, укажите пожалуйста его в анкете",
        "Profile":"Профиль",
        "Rules":"Правила",
        "Cancel": "Отклонить",
        "Cancel trip": "Отменить поездку",
        "Set current location":"Укажите свою локацию",
        "Set departure location": "Укажите координаты отправления (Нажмите 📎 и выберите \"Локация\")",
        "Set destination location": "Укажите координаты назначения (Нажмите 📎 и выберите \"Локация\")",
        "Show destination location":"Показать локацию назначения",
        "Sorry can`t saved data":"Извините, не смогли сохранить данные",
        "Thank you for an order":"Спасибо за заказ",
        "Thank you, we will check the crediting of funds":"Спасибо, мы проверим зачисление средств",
        "Thanks for the information": "Спасибо за указанную информацию",
        "This order cannot be canceled, it is already taken":"Этот заказ нельзя отменить, он уже принят другим водителем",
        "This order cannot be taken, it is already taken":"Этот заказ нельзя взять, он уже занят другим водителем",
        "Top up driver balance":"Пополнить баланс водителя",
        "To use the service you need to enter some data":"Чтобы пользоваться сервисом необходимо ввести некоторые данные",
        "To work in the system, you must have at least {minAmount:d} usdt on your account. To replenish the account, you need to transfer the currency to the specified crypto wallet. After the payment has been made Confirm the transfer with the button": "Для работы в системе необходимо иметь на балансе не меньше {minAmount:d} usdt. Чтобы пополнить счёт необходимо перевести валюту на указанный криптокошелёк. После произведённой оплаты подтвердите перевод кнопкой",
        "Unable to find customer":"Не удалось найти клиента",
        "Under construction..": "В разработке..",
        "Use the menu to get started": "Используйте меню чтобы начать",
        "Waiting driver":"Ждать водителя",
        "Wallet not found, you can see right wallet to your profile":"Кошелек не найден, вы можете увидеть нужный кошелек в своем профиле",
        "What time do you need a taxi?": "В какое время вам нужна машина?",
        "What's your name?": "Как вас зовут?",
        "What's your car number?":"Укажите номер машины?",
        "We are already looking for drivers for you..": "Мы уже ищем водителей для Вас..",
        "When you deliver the passenger, please press the button to done the order":"Когда доставите пассажира, нажмите, пожалуйста, кнопку \n&#171;завершить текущий заказ&#187;",
        "When you reach your destination, please click on the button to complete the current order":"Когда вы доберётесь до места назначения, нажмите, пожалуйста кнопку \n&#171;завершить текущий заказ&#187;",
        "We can`t create your form":"Не удалось создать форму",
        "We couldn't find your profile":"Мы не смогли найти ваш профиль",
        "We saved your name":"Мы сохранили Ваше имя",
        "We saved your phone":"Мы сохранили Ваш телефон",
        "We saved your amount":"Мы сохранили Вашу сумму",
        "Welcome!": "Добро пожаловать!",
        "We are looking for clients for you already":"Мы уже ищем клиентов для Вас",
        "You are in the client menu": "Вы находитесь в меню клиента",
        "You are in the driver menu": "Вы находитесь в меню водителя",
        "You are online, already":"Вы уже онлайн",
        "You are offline, already":"Вы уже оффлайн",
        "You can attach your photo if you wish": "Прикрепите Ваше фото",
        "You can`t see orders, your are at route":"Вы не можете смотреть заказы, вы в пути",
        "You can`t see orders, your are online":"Вы не можете смотреть заказы, вы онлайн",
        "You can`t see orders, your balance is less than {minAmount:d} usdt":"Вы не можете видеть заказы, Ваш баланс менее {minAmount:d} usdt",
        "You can`t switch to online, your balance is less than {minAmount:d} usdt":"Вы не можете выйти на линию, ваш баланс меньше {minAmount:d} usdt",
        "You cannot switch to online, you must complete the route":"Вы не можете переключиться в онлайн, необходимо завершить заказ",
        "You have active order":"У Вас имеется текущий заказ",
        "You have taken the order": "Вы приняли заказ",
        "You have taken the order go to the passenger":"Вы приняли заказ, направляйтесь к пассажиру",
        "You have unknown status":"Неизвестный статус",
        "You haven`t orders":"У вас нет заказов",
        "You haven`t current order":"У вас нет текущего заказа",
        "Your balance is {driverBalance:d} usdt, min balance for use bot is {minBalance:d} usdt": "Ваш баланс {driverBalance:d} usdt, минимальный баланс для работы в системе {minBalance:d} usdt",
        "Your order is accepted. The driver drove to you":"Ваш заказ принят. Вы можете связаться с водителем и договориться о встрече",
        "Your profile is saved": "Ваш профиль сохранен",
        "You switch offline. Orders unavailable":"Вы отключены. Заказы недоступны",
        "You switch route. Orders unavailable":"Вы на маршруте. Заказы недоступны",
        "How to top up":"Как пополнять",
        "My profile":"Мой профиль",
        "Now":"Прямо сейчас",
        "After 10 minutes":"Через 10 минут",
        "After 15 minutes":"Через 15 минут",
        "In 30 minutes":"Через 30 минут",
        "In one hour":"Через час",
        "In 2 hours":"Через 2 часа",
        "Book an order":"Взять заказ",
        "Copy wallet":"Скопировать кошелек",

        "yes":"да",
        "no":"нет",


    },
    'EN':{},
}


def t (alias):
    return language[LANGUAGE][alias]
