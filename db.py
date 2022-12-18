import sqlite3
from sqlite3 import Error
import config
import os.path

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class BotDB:

    statuses = {
        'online': 'Доступен 🟢',
        'offline': 'Не доступен 🔴',
        'route': 'Везет клиента 🟠',
        'waiting': 'Ожидает машину 🟢',
        'progress': 'В пути 🟠',
        'done': 'Выполнен 🔵',
        'cancel': 'Отменен ⚫',
        'unknown': 'Неизвестен ⚪'
    }

    def __init__(self, db_file):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, db_file)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = dict_factory
        self.cursor = self.conn.cursor()





    def client_exists(self, user_id):
        """Проверяем, есть ли client в базе"""
        sql = ""
        result = self.cursor.execute("SELECT `tg_user_id` FROM `client` WHERE `tg_user_id` = ?", (user_id,))
        return bool(self.cursor.fetchall())

    def get_client_id(self, user_id):
        """Достаем id client в базе по его user_id"""
        result = self.cursor.execute("SELECT `id` FROM `client` WHERE `tg_user_id` = ?", (user_id,))
        return self.cursor.fetchone()['id']

    def get_client(self, user_id):
        """Достаем client в базе по его user_id"""
        result = self.cursor.execute("SELECT * FROM `client` WHERE `tg_user_id` = ?", (user_id,))
        return self.cursor.fetchone()

    def add_client(self, user_id):
        """Добавляем client в базу"""
        try:
            self.cursor.execute("INSERT INTO `client` (`tg_user_id`) VALUES (?)", (user_id,))
        except Error as e:
            print(e)
        return self.conn.commit()
    def update_client(self, user_id, data):
        """update client"""
        try:
            self.cursor.execute("UPDATE `client` SET name = ?, phone = ? WHERE tg_user_id = ?", (data['name'], data['phone'], user_id))
        except Error as e:
            print(e)
        return self.conn.commit()
    def create_order(self, data):
        try:
            sql = '''INSERT INTO `order`
            (client_id, status, dt_order, amount_client, departure_latitude, departure_longitude, destination_latitude, destination_longitude, route_length, route_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, list(data.values()))
        except Error as e:
            print(e)
        return self.conn.commit()
    def get_orders(self, user_id, status):
        result = self.cursor.execute("SELECT * FROM `order` WHERE `status` = ? ORDER BY `dt_order`", (status,))
        return result.fetchall()
    def get_client_orders(self, client_id):
        result = self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = ? ORDER BY `dt_order` DESC", (client_id,))
        return result.fetchall()
    def order_waiting_exists(self, id, status):
        result = self.cursor.execute("SELECT `id` FROM `order` WHERE id = ? AND status = ?", (id, status))
        return bool(len(result.fetchall()))
    def update_order_status(self, id, status):
        self.cursor.execute("UPDATE `order` SET status = ? WHERE id = ?", (status, id,))
        return self.conn.commit()
    def get_order(self, id):
        result = self.cursor.execute("SELECT * FROM `order` WHERE `id` = ?", (id,))
        return result.fetchone()


    def driver_exists(self, user_id):
        """Проверяем, есть ли driver в базе"""
        result = self.cursor.execute("SELECT `id` FROM `driver` WHERE `tg_user_id` = ?", (user_id,))
        return bool(len(result.fetchall()))

    def get_driver_id(self, user_id):
        """Достаем id driver в базе по его user_id"""
        result = self.cursor.execute("SELECT `id` FROM `driver` WHERE `tg_user_id` = ?", (user_id,))
        return result.fetchone()['id']

    def get_driver(self, user_id):
        """Достаем driver по его user_id"""
        result = self.cursor.execute("SELECT * FROM `driver` WHERE `tg_user_id` = ?", (user_id,))
        return result.fetchone()

    def add_driver(self, user_id):
        """Добавляем driver в базу"""
        self.cursor.execute("INSERT INTO `driver` (`tg_user_id`) VALUES (?)", (user_id,))
        return self.conn.commit()

    def get_driver_balance(self, user_id):
        result = self.cursor.execute("SELECT `balance` FROM `driver` WHERE `tg_user_id` = ?", (user_id,))
        return result.fetchone()['balance']
    def get_driver_by_wallet(self, wallet):
        result = self.cursor.execute("SELECT * FROM `driver` WHERE `wallet` = ?", (wallet,))
        return result.fetchone()
    def update_driver_balance(self, user_id, data):
        """update driver balance"""
        try:
            self.cursor.execute("UPDATE `driver` SET balance = ? WHERE tg_user_id = ?", (data, user_id))
        except Error as e:
            print(e)
        return self.conn.commit()
    def update_driver_wallet(self, user_id, data):
        """update driver wallet"""
        try:
            self.cursor.execute("UPDATE `driver` SET wallet = ? WHERE tg_user_id = ?", (data, user_id))
        except Error as e:
            print(e)
        return self.conn.commit()
    def update_driver(self, user_id, data):
        """update driver"""
        try:
            self.cursor.execute("UPDATE `driver` SET name = ?, phone = ?, car_number = ?, status = ? WHERE tg_user_id = ?", (data['name'], data['phone'], data['car_number'], data['status'], user_id))
        except Error as e:
            print(e)
        return self.conn.commit()
    def update_driver_status(self, user_id, status):
        """update driver status"""
        try:
            self.cursor.execute("UPDATE `driver` SET status = ? WHERE tg_user_id = ?", (status, user_id))
        except Error as e:
            print(e)
        return self.conn.commit()





    def add_record(self, user_id, operation, value):
        """Создаем запись о доходах/расходах"""
        self.cursor.execute("INSERT INTO `records` (`users_id`, `operation`, `value`) VALUES (?, ?, ?)",
            (self.get_user_id(user_id),
            operation == "+",
            value))
        return self.conn.commit()

    def get_records(self, user_id, within = "all"):
        """Получаем историю о доходах/расходах"""

        if(within == "day"):
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = ? AND `date` BETWEEN datetime('now', 'start of day') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        elif(within == "week"):
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = ? AND `date` BETWEEN datetime('now', '-6 days') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        elif(within == "month"):
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = ? AND `date` BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        else:
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = ? ORDER BY `date`",
                (self.get_user_id(user_id),))

        return result.fetchall()

    def close(self):
        """Закрываем соединение с БД"""
        self.conn.close()
