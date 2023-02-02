import sqlite3
from sqlite3 import Error
import config
import os.path
import mysql.connector

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class BotDB:

    statuses = {
        # Водитель
        'online': 'Доступен 🟢',
        'offline': 'Не доступен 🔴',
        'route': 'Везет клиента 🟠',

        # Заказ
        'create': 'Создан 🟡',
        'waiting': 'Ожидает машину 🟢',
        'progress': 'В пути 🟠',
        'done': 'Выполнен 🔵',
        'cancel': 'Отменен ⚫',

        'unknown': 'Неизвестен ⚪'
    }

    dbType = 'sqlite'

    replacer = '?';

    def __init__(self, db_file):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, db_file)

        if self.dbType == 'sqlite':
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = dict_factory
            self.cursor = self.conn.cursor()
        else:
            self.conn = mysql.connector.connect(user='root', password='rootPass', host='127.0.0.1', database='taxi')
            self.replacer = '%s';
            self.cursor = self.conn.cursor(buffered=True, dictionary=True)






    def client_exists(self, user_id):
        """Проверяем, есть ли client в базе"""
        sql = ""
        result = self.cursor.execute("SELECT `tg_user_id` FROM `client` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        return bool(self.cursor.fetchall())

    def get_client_id(self, user_id):
        """Достаем id client в базе по его user_id"""
        result = self.cursor.execute("SELECT `id` FROM `client` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        return self.cursor.fetchone()['id']

    def get_client(self, user_id):
        """Достаем client в базе по его user_id"""
        result = self.cursor.execute("SELECT * FROM `client` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        return self.cursor.fetchone()

    def add_client(self, user_id, first_name):
        """Добавляем client в базу"""
        try:
            self.cursor.execute("INSERT INTO `client` (`tg_user_id`, `tg_first_name`) VALUES (" + self.replacer + ", " + self.replacer + ")", (user_id, first_name,))
        except Error as e:
            print(e)
        return self.conn.commit()
    def update_client(self, user_id, data):
        """update client"""
        try:
            self.cursor.execute("UPDATE `client` SET name = " + self.replacer + ", phone = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (data['name'], data['phone'], user_id))
        except Error as e:
            print(e)
        return self.conn.commit()
    def create_order(self, data):
        try:
            sql = '''INSERT INTO `order`
            (client_id, status, dt_order, amount_client, departure_latitude, departure_longitude, destination_latitude, destination_longitude, route_length, route_time)
            VALUES (''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''')'''
            self.cursor.execute(sql, list(data.values()))
        except Error as e:
            print(e)
        return self.conn.commit()
    def get_last_order(self):
        result = self.cursor.execute("SELECT *, o.id order_id FROM `order` o LEFT JOIN client c ON c.tg_user_id = o.client_id ORDER BY id DESC LIMIT 1")
        return self.cursor.fetchone()
    def get_order_waiting_by_driver_id(self, driver_id):
        result = self.cursor.execute("SELECT * FROM `order` WHERE driver_id = " + self.replacer + " AND status = 'waiting'", (driver_id))
        return self.cursor.fetchone()
    def get_orders(self, user_id, status):
        result = self.cursor.execute("SELECT * FROM `order` WHERE `status` = " + self.replacer + " ORDER BY `dt_order`", (status,))
        return result.fetchall()
    def get_client_orders(self, client_id):
        result = self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = " + self.replacer + " ORDER BY `dt_order` DESC", (client_id,))
        return self.cursor.fetchall()
    def order_waiting_exists(self, id, status):
        result = self.cursor.execute("SELECT `id` FROM `order` WHERE id = " + self.replacer + " AND status = " + self.replacer, (id, status))
        return bool(len(result.fetchall()))
    def update_order_status(self, id, status):
        try:
            self.cursor.execute("UPDATE `order` SET status = " + self.replacer + " WHERE id = " + self.replacer, (status, id,))
        except Error as e:
            print(e)
        return self.conn.commit()
    def update_order_driver_id(self, id, driver_id):
        try:
            self.cursor.execute("UPDATE `order` SET driver_id = " + self.replacer + " WHERE id = " + self.replacer, (driver_id, id,))
        except Error as e:
            print(e)
        return self.conn.commit()
    def get_order(self, id):
        result = self.cursor.execute("SELECT * FROM `order` WHERE `id` = " + self.replacer, (id,))
        return self.cursor.fetchone()
    def get_order_progress_by_driver_id(self, id):
        result = self.cursor.execute("SELECT * FROM `order` WHERE `driver_id` = " + self.replacer + " AND status = 'progress'", (id,))
        return self.cursor.fetchone()
    def get_waiting_orders_by_client_id(self, id):
        result = self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = " + self.replacer + " AND status = 'waiting'", (id,))
        return result.fetchall()
    def get_waiting_order_by_client_id(self, id):
        result = self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = " + self.replacer + " AND status = 'waiting'", (id,))
        return self.cursor.fetchone()
    def get_create_order_by_client_id(self, id):
        result = self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = " + self.replacer + " AND status = 'create'", (id,))
        return self.cursor.fetchone()
    def get_done_orders_by_client_id(self, id):
        result = self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = " + self.replacer + " AND status = 'done'", (id,))
        return result.fetchall()




    def driver_exists(self, user_id):
        """Проверяем, есть ли driver в базе"""
        result = self.cursor.execute("SELECT `id` FROM `driver` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        return bool(len(self.cursor.fetchall()))
    def get_drivers(self):
        result = self.cursor.execute("SELECT * FROM `driver`")
        return result.fetchall()
    def get_drivers_with_wallets(self):
        result = self.cursor.execute("SELECT * FROM `driver` WHERE wallet not NULL")
        return result.fetchall()
    def get_driver_id(self, user_id):
        """Достаем id driver в базе по его user_id"""
        result = self.cursor.execute("SELECT `id` FROM `driver` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        return self.cursor.fetchone()['id']

    def get_driver(self, user_id):
        """Достаем driver по его user_id"""
        result = self.cursor.execute("SELECT * FROM `driver` WHERE tg_user_id = " + self.replacer, (user_id,))
        return self.cursor.fetchone()

    def add_driver(self, user_id, first_name):
        """Добавляем driver в базу"""
        try:
            self.cursor.execute("INSERT INTO `driver` (`tg_user_id`, `tg_first_name`) VALUES (" + self.replacer + ", " + self.replacer + ")", (user_id, first_name,))
        except Error as e:
            print(e)
        return self.conn.commit()

    def get_driver_balance(self, user_id):
        result = self.cursor.execute("SELECT `balance` FROM `driver` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        return self.cursor.fetchone()['balance']
    def get_driver_by_wallet(self, wallet):
        result = self.cursor.execute("SELECT * FROM `driver` WHERE `wallet` = " + self.replacer, (wallet,))
        return self.cursor.fetchone()
    def get_drivers_by_wallet(self, wallet):
        result = self.cursor.execute("SELECT * FROM `driver` WHERE `wallet` = " + self.replacer, (wallet,))
        return result.fetchall()
    def update_driver_balance(self, user_id, data):
        """update driver balance"""
        try:
            self.cursor.execute("UPDATE `driver` SET balance = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (data, user_id))
        except Error as e:
            print(e)
        return self.conn.commit()
    def update_driver_wallet(self, user_id, data):
        """update driver wallet"""
        try:
            self.cursor.execute("UPDATE `driver` SET wallet = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (data, user_id))
        except Error as e:
            print(e)
        return self.conn.commit()
    def update_driver(self, user_id, data):
        """update driver"""
        try:
            self.cursor.execute("UPDATE `driver` SET name = " + self.replacer + ", phone = " + self.replacer + ", car_number = " + self.replacer + ", status = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (data['name'], data['phone'], data['car_number'], data['status'], user_id))
        except Error as e:
            print(e)
        return self.conn.commit()
    def update_driver_status(self, user_id, status):
        """update driver status"""
        try:
            self.cursor.execute("UPDATE `driver` SET status = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (status, user_id))
        except Error as e:
            print(e)
        return self.conn.commit()
    def update_driver_location(self, user_id, latitude, longitude):
        try:
            self.cursor.execute("UPDATE `driver` SET latitude = " + self.replacer + ", longitude = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (latitude, longitude, user_id))
        except Error as e:
            print(e)
        return self.conn.commit()
    def get_near_order(self, status, latitude, longitude, driver_id):
        sql = '''
            select
                MIN(ABS(o.departure_latitude - ''' + self.replacer + ''')) as l1
                , MIN(ABS(o.departure_longitude - ''' + self.replacer + ''')) as l2
                , *
                , o.id order_id
            from `order` o
            left join client c ON c.tg_user_id = o.client_id
            left join driver_order do ON do.order_id = o.id
            where o.status = ''' + self.replacer + ''' AND o.departure_latitude > 0 AND o.departure_longitude > 0
            and (do.driver_id IS NULL OR (do.driver_id = ''' + self.replacer + ''' and do.driver_cancel_cn < 2))
        '''
        result = self.cursor.execute(sql, (latitude, longitude, status, driver_id))
        return self.cursor.fetchone()





    def driver_order_exists(self, driver_id, order_id):
        result = self.cursor.execute("SELECT `driver_id` FROM `driver_order` WHERE `driver_id` = " + self.replacer + " AND order_id = " + self.replacer, (driver_id, order_id))
        return bool(self.cursor.fetchall())
    def driver_order_create(self, driver_id, order_id):
        try:
            self.cursor.execute("INSERT INTO `driver_order` (`driver_id`, `order_id`) VALUES (" + self.replacer + ", " + self.replacer + ")", (driver_id, order_id,))
        except Error as e:
            print(e)
        return self.conn.commit()
    def driver_order_increment_cancel_cn(self, driver_id, order_id):
        try:
            if (not self.driver_order_exists(driver_id, order_id)):
                self.driver_order_create(driver_id, order_id)
            self.cursor.execute("UPDATE `driver_order` SET driver_cancel_cn = IFNULL(driver_cancel_cn, 0) + 1 WHERE driver_id = " + self.replacer + " AND order_id = " + self.replacer, (driver_id, order_id))
        except Error as e:
            print(e)
        return self.conn.commit()
    def add_record(self, user_id, operation, value):
        """Создаем запись о доходах/расходах"""
        try:
            self.cursor.execute("INSERT INTO `records` (`users_id`, `operation`, `value`) VALUES (" + self.replacer + ", " + self.replacer + ", " + self.replacer + ")",
                (self.get_user_id(user_id),
                operation == "+",
                value))
        except Error as e:
            print(e)
        return self.conn.commit()

    def get_driver_order(self, driver_id, order_id):
        result = self.cursor.execute("SELECT * FROM `driver_order` WHERE `driver_id` = " + self.replacer + " AND order_id = " + self.replacer, (driver_id, order_id))
        return self.cursor.fetchone()

    def get_records(self, user_id, within = "all"):
        """Получаем историю о доходах/расходах"""

        if(within == "day"):
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = " + self.replacer + " AND `date` BETWEEN datetime('now', 'start of day') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        elif(within == "week"):
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = " + self.replacer + " AND `date` BETWEEN datetime('now', '-6 days') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        elif(within == "month"):
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = " + self.replacer + " AND `date` BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        else:
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = " + self.replacer + " ORDER BY `date`",
                (self.get_user_id(user_id),))

        return result.fetchall()

    def close(self):
        """Закрываем соединение с БД"""
        self.conn.close()

    def fetchOne(self, result):
        if result is None:
            return False
        else:
            if self.dbType == 'sqlite':
                return result.fetchone()
            elif self.dbType == 'mysql':
                return result.fetch_one()


    def fetchAll(self, result):
        if len(result) == 0:
            return result
        else:
            if self.dbType == 'sqlite':
                return result.fetchall()
            elif self.dbType == 'mysql':
                return result.fetchall()
