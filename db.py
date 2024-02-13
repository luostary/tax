import sqlite3
from sqlite3 import Error
import config
import os.path
import mysql.connector
from config import *

# show processlist;
# Select concat('kill ',id,';') from information_schema.processlist where user='root';


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

    dbType = config.DB_TYPE

    replacer = '?';
    dbFile = ''

    def __init__(self, db_file = 'taxi.db'):
        self.dbFile = db_file
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, db_file)

        if self.dbType == 'sqlite':
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = dict_factory
            self.cursor = self.conn.cursor()
        else:
            self.conn = mysql.connector.connect(
                user = config.DB_USER,
                password = config.DB_PASSWORD,
                host = config.DB_HOST,
                database = config.DB_NAME,
                connection_timeout = config.DB_CONNECTION_TIMEOUT
            )
            self.replacer = '%s';
            self.cursor = self.conn.cursor(buffered=True, dictionary=True)
            self.cursor.execute("SET GLOBAL wait_timeout = 120")

    def connect(self):
        if not self.conn.is_connected():
            self.conn.reconnect()
        pass


    # ЗАПРОСЫ ДЛЯ КЛИЕНТА
    def client_exists(self, user_id):
        """Проверяем, есть ли client в базе"""
        self.connect()
        sql = ""
        self.cursor.execute("SELECT `tg_user_id` FROM `client` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        result = bool(self.cursor.fetchall())
        self.close()
        return result

    def get_client_id(self, user_id):
        """Достаем id client в базе по его user_id"""
        self.connect()
        self.cursor.execute("SELECT `id` FROM `client` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        result = self.cursor.fetchone()['id']
        self.close()
        return result

    def get_client(self, user_id):
        """Достаем client в базе по его user_id"""
        self.connect()
        self.cursor.execute("SELECT * FROM `client` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        result = self.cursor.fetchone()
        self.close()
        return result

    def add_client(self, user_id, first_name):
        """Добавляем client в базу"""
        self.connect()
        try:
            self.cursor.execute("INSERT INTO `client` (`tg_user_id`, `tg_first_name`) VALUES (" + self.replacer + ", " + self.replacer + ")", (user_id, first_name,))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def update_client(self, user_id, data):
        """Обновление клиента"""
        self.connect()
        try:
            self.cursor.execute("UPDATE `client` SET name = " + self.replacer + ", phone = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (data['name'], data['phone'], user_id))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def update_client_referer(self, user_id, referer_user_id):
        """Обновление referer_user_id"""
        self.connect()
        try:
            self.cursor.execute("UPDATE `client` SET referer_user_id = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (referer_user_id, user_id))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def update_client_tg_username(self, user_id, username):
        self.connect()
        try:
            self.cursor.execute("UPDATE `client` SET tg_username = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (username, user_id))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result





    # Заявки
    def create_order(self, data):
        self.connect()
        try:
            sql = '''INSERT INTO `order`
            (client_id, status, dt_order, amount_client, departure_latitude, departure_longitude, destination_latitude, destination_longitude, route_length, route_time)
            VALUES (''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''', ''' + self.replacer + ''')'''
            self.cursor.execute(sql, (
                data['client_id'],
                data['status'],
                data['dt_order'],
                data['amount_client'],
                data['departure_latitude'],
                data['departure_longitude'],
                data['destination_latitude'],
                data['destination_longitude'],
                data['route_length'],
                data['route_time'],
            ))
            id = self.cursor.lastrowid
            self.conn.commit()
        except Error as e:
            print(e)
        result = id
        self.close()
        return result


    def get_last_order(self):
        self.connect()
        self.cursor.execute("SELECT *, o.id order_id FROM `order` o LEFT JOIN client c ON c.tg_user_id = o.client_id ORDER BY id DESC LIMIT 1")
        result = self.cursor.fetchone()
        self.close()
        return result


    def get_order_waiting_by_driver_id(self, driver_id):
        self.connect()
        self.cursor.execute("SELECT * FROM `order` WHERE driver_id = " + self.replacer + " AND status = 'waiting'", (driver_id,))
        result = self.cursor.fetchone()
        self.close()
        return result


    def get_orders(self, user_id, status):
        self.connect()
        self.cursor.execute("SELECT * FROM `order` WHERE `status` = " + self.replacer + " ORDER BY `dt_order`", (status,))
        result = self.cursor.fetchall()
        self.close()
        return result


    def get_client_orders(self, client_id):
        self.connect()
        self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = " + self.replacer + " ORDER BY `dt_order` DESC", (client_id,))
        result = self.cursor.fetchall()
        self.close()
        return result


    def get_clients(self):
        self.connect()
        self.cursor.execute("SELECT * FROM `client`")
        result = self.cursor.fetchall()
        self.close()
        return result

    def get_client_orders_by_one(self, client_id, offset):
        self.connect()
        self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = " + self.replacer + " ORDER BY `dt_order` DESC LIMIT " + self.replacer + ", 1", (client_id, int(offset)))
        result = self.cursor.fetchall()
        self.close()
        return result


    def order_waiting_exists(self, id, status):
        self.connect()
        self.cursor.execute("SELECT `id` FROM `order` WHERE id = " + self.replacer + " AND status = " + self.replacer, (id, status))
        result = bool(len(self.cursor.fetchall()))
        self.close()
        return result


    def update_order_status(self, id, status):
        self.connect()
        try:
            self.cursor.execute("UPDATE `order` SET status = " + self.replacer + " WHERE id = " + self.replacer, (status, id,))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def update_order_driver_id(self, id, driver_id):
        self.connect()
        try:
            self.cursor.execute("UPDATE `order` SET driver_id = " + self.replacer + " WHERE id = " + self.replacer, (driver_id, id,))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def get_order(self, id):
        self.connect()
        self.cursor.execute("SELECT * FROM `order` WHERE `id` = " + self.replacer, (id,))
        result = self.cursor.fetchone()
        self.close()
        return result


    def get_order_progress_by_driver_id(self, id):
        self.connect()
        self.cursor.execute("SELECT * FROM `order` WHERE `driver_id` = " + self.replacer + " AND status = 'progress'", (id,))
        result = self.cursor.fetchone()
        self.close()
        return result


    def get_waiting_orders_by_client_id(self, id):
        self.connect()
        self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = " + self.replacer + " AND status = 'waiting'", (id,))
        result =  self.cursor.fetchall()
        self.close()
        return result


    def get_waiting_order_by_client_id(self, id):
        self.connect()
        self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = " + self.replacer + " AND status = 'waiting'", (id,))
        result = self.cursor.fetchone()
        self.close()
        return result


    def get_create_order_by_client_id(self, id):
        self.connect()
        self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = " + self.replacer + " AND status = 'create'", (id,))
        result = self.cursor.fetchone()
        self.close()
        return result


    def get_done_orders_by_client_id(self, id):
        self.connect()
        self.cursor.execute("SELECT * FROM `order` WHERE `client_id` = " + self.replacer + " AND status = 'done'", (id,))
        result = self.cursor.fetchall()
        self.close()
        return result






    # Водитель
    def driver_exists(self, user_id):
        self.connect()
        """Проверяем, есть ли driver в базе"""
        self.cursor.execute("SELECT `id` FROM `driver` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        result = bool(len(self.cursor.fetchall()))
        self.close()
        return result


    def get_drivers(self):
        self.connect()
        self.cursor.execute("SELECT * FROM `driver`")
        result = self.cursor.fetchall()
        self.close()
        return result


    def get_drivers_with_wallets(self):
        self.connect()
        self.cursor.execute("SELECT * FROM `driver` WHERE wallet IS NOT NULL")
        result = self.cursor.fetchall()
        self.close()
        return result


    def get_driver_id(self, user_id):
        """Достаем id driver в базе по его user_id"""
        self.connect()
        self.cursor.execute("SELECT `id` FROM `driver` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        result = self.cursor.fetchone()['id']
        self.close()
        return result


    def get_driver(self, user_id):
        """Достаем driver по его user_id"""
        self.connect()
        self.cursor.execute("SELECT * FROM `driver` WHERE tg_user_id = " + self.replacer, (user_id,))
        result = self.cursor.fetchone()
        self.close()
        return result


    def add_driver(self, user_id, first_name):
        """Добавляем driver в базу"""
        self.connect()
        try:
            self.cursor.execute("INSERT INTO `driver` (`tg_user_id`, `tg_first_name`, `wallet`) VALUES (" + self.replacer + ", " + self.replacer + ", " + self.replacer + ")", (user_id, first_name, user_id,))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def get_driver_balance(self, user_id):
        self.connect()
        self.cursor.execute("SELECT `balance` FROM `driver` WHERE `tg_user_id` = " + self.replacer, (user_id,))
        result = self.cursor.fetchone()['balance']
        self.close()
        return result


    def get_driver_by_wallet(self, wallet):
        self.connect()
        self.cursor.execute("SELECT * FROM `driver` WHERE `wallet` = " + self.replacer, (wallet,))
        result = self.cursor.fetchone()
        self.close()
        return result


    def get_drivers_by_wallet(self, wallet):
        self.connect()
        self.cursor.execute("SELECT * FROM `driver` WHERE `wallet` = " + self.replacer, (wallet,))
        result = self.cursor.fetchall()
        self.close()
        return result


    def get_drivers_by_status(self, status):
        self.connect()
        self.cursor.execute("SELECT * FROM `driver` WHERE `status` = " + self.replacer, (status,))
        result = self.cursor.fetchall()
        self.close()
        return result


    def get_drivers_registered(self):
        self.connect()
        self.cursor.execute("SELECT * FROM `driver` WHERE `name` IS NOT NULL AND phone IS NOT NULL")
        result = self.cursor.fetchall()
        self.close()
        return result


    def get_drivers_unregistered(self):
        self.connect()
        sql = "SELECT * FROM `driver` WHERE `phone` IS NULL"
        if (LIMIT_THESE_USERS):
            idsString = ", ".join(str(element) for element in LIMIT_THESE_USERS)
            sql += " AND tg_user_id IN (" + idsString + ")"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.close()
        return result


    def update_driver_balance(self, user_id, data):
        """Обновление баланса водителя"""
        self.connect()
        try:
            self.cursor.execute("UPDATE `driver` SET balance = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (data, user_id))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def update_driver_wallet(self, user_id, data):
        """Обновление значения кошелька водителя"""
        self.connect()
        try:
            self.cursor.execute("UPDATE `driver` SET wallet = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (data, user_id))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def update_driver(self, user_id, data):
        """Обновление записи водителя"""
        self.connect()
        try:
            self.cursor.execute("UPDATE `driver` SET name = " + self.replacer + ", phone = " + self.replacer + ", car_number = " + self.replacer + ", status = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (data['name'], data['phone'], data['car_number'], data['status'], user_id))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def update_driver_referer(self, user_id, referer_user_id):
        """Обновление referer_user_id"""
        self.connect()
        try:
            self.cursor.execute("UPDATE `driver` SET referer_user_id = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (referer_user_id, user_id))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def update_driver_tg_username(self, user_id, username):
        self.connect()
        try:
            self.cursor.execute("UPDATE `driver` SET tg_username = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (username, user_id))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def update_driver_status(self, user_id, status):
        """Обновление статуса водителя"""
        self.connect()
        try:
            self.cursor.execute("UPDATE `driver` SET status = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (status, user_id))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def update_driver_location(self, user_id, latitude, longitude):
        self.connect()
        try:
            self.cursor.execute("UPDATE `driver` SET latitude = " + self.replacer + ", longitude = " + self.replacer + " WHERE tg_user_id = " + self.replacer, (latitude, longitude, user_id))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def update_status_for_all_drivers(self, status):
        self.connect()
        result = False
        try:
            self.cursor.execute("UPDATE `driver` SET status = " + self.replacer, (status))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def get_near_driver(self, lt, ln, order_id):
        self.connect()
        sql = '''SELECT
               ABS(d.latitude - {latitude:f}) dif_lat, ABS(d.longitude - {longitude:f}) dif_lon
               , d.*
            FROM driver d
            LEFT JOIN driver_order dror ON dror.driver_id = d.tg_user_id AND dror.order_id = {order_id:d}
            where `status` IN ('online', 'offline')
            AND IFNULL(dror.driver_cancel_cn, 0) < 2'''

        if LIMIT_THESE_USERS:
            idsString = ", ".join(str(element) for element in LIMIT_THESE_USERS)
            sql+= '''
            AND tg_user_id IN (''' + idsString + ''')'''

        sql+='''
            having dif_lat IS NOT NULL AND dif_lon IS NOT NULL
            order by dif_lat, dif_lon ASC
            LIMIT 1;'''
        sql = sql.format(
            latitude = lt,
            longitude = ln,
            order_id = order_id
        )
        self.cursor.execute(sql)
        result = self.cursor.fetchone()
        self.close()
        return result






    # Связи таблиц
    def get_near_order(self, status, latitude, longitude, driver_id):
        self.connect()
        sql = '''
            select
                MIN(ABS(o.departure_latitude - ''' + self.replacer + ''')) as l1
                , MIN(ABS(o.departure_longitude - ''' + self.replacer + ''')) as l2
                , o.*
                , c.*
                , o.id order_id
            from `order` o
            left join client c ON c.tg_user_id = o.client_id
            left join driver_order do ON do.order_id = o.id
            where o.status = ''' + self.replacer + ''' AND o.departure_latitude > 0 AND o.departure_longitude > 0
            and (do.driver_id IS NULL OR (do.driver_id = ''' + self.replacer + ''' and do.driver_cancel_cn < 2))
            GROUP BY o.id, c.id
            ORDER BY l1, l2 ASC
        '''
        self.cursor.execute(sql, (latitude, longitude, status, driver_id))
        result = self.cursor.fetchone()
        self.close()
        return result





    def driver_order_exists(self, driver_id, order_id):
        self.connect()
        self.cursor.execute("SELECT `driver_id` FROM `driver_order` WHERE `driver_id` = " + self.replacer + " AND order_id = " + self.replacer, (driver_id, order_id))
        result = bool(self.cursor.fetchall())
        self.close()
        return result


    def driver_order_create(self, driver_id, order_id):
        self.connect()
        try:
            self.cursor.execute("INSERT INTO `driver_order` (`driver_id`, `order_id`, `driver_cancel_cn`) VALUES (" + self.replacer + ", " + self.replacer + ", 0)", (driver_id, order_id,))
        except Error as e:
            print(e)
        result = self.conn.commit()
        self.close()
        return result


    def driver_order_increment_cancel_cn(self, driver_id, order_id):
        self.connect()
        result = False
        try:
            self.cursor.execute("UPDATE `driver_order` SET driver_cancel_cn = IFNULL(driver_cancel_cn, 0) + 1 WHERE driver_id = " + self.replacer + " AND order_id = " + self.replacer, (driver_id, order_id))
            result = self.conn.commit()
        except Error as e:
            print(e)
        self.close()
        return result


    def get_driver_order(self, driver_id, order_id):
        self.connect()
        self.cursor.execute("SELECT * FROM `driver_order` WHERE `driver_id` = " + self.replacer + " AND order_id = " + self.replacer, (driver_id, order_id))
        result = self.cursor.fetchone()
        self.close()
        return result


    def get_location_by_name(self, text):
        self.connect()
        sql = ("SELECT * FROM `location` WHERE `name_rus` LIKE '%{text:s}%' OR name_eng LIKE '%{text:s}%' OR search_rus LIKE '%{text:s}%'")
        sql = sql.format(
            text = text
        )
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.close()
        return result


    def get_locations_by_category_id(self, category_id):
        self.connect()
        sql = ("SELECT * FROM `location` WHERE `category_id` = {category_id:d} ORDER BY name_rus")
        sql = sql.format(
            category_id = category_id
        )
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.close()
        return result


    def get_location_by_id(self, id):
        self.connect()
        self.cursor.execute("SELECT * FROM `location` WHERE `id` = " + self.replacer, (id,))
        result = self.cursor.fetchone()
        self.close()
        return result



    # Каталог локаций
    def get_categories(self, parent_id):
            if (parent_id > 0):
                condition = '= ' + str(parent_id)
            else:
                condition = 'IS NULL';
            self.connect()
            sql = "SELECT * FROM `category` WHERE `parent_id` {condition:s} ORDER BY sort".format(
                condition = condition
            )
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            self.close()
            return result



    def close(self):
        """Закрываем соединение с БД"""
        if config.DB_RECONNECT_CONNECTION_AFTER_QUERY:
            self.conn.reconnect()
        pass