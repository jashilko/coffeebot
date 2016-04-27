# -*- coding: utf-8 -*-
import sqlite3

class SQLighter:

    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def select_all(self):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM music').fetchall()

    def select_single(self, rownum):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('SELECT * FROM music WHERE id = ?', (rownum,)).fetchall()[0]

    def count_rows(self):
        """ Считаем количество строк """
        with self.connection:
            result = self.cursor.execute('SELECT * FROM music').fetchall()
            return len(result)

    def new_client(self, client_id, client_username, client_first_name):
        with self.connection:
            if self.check_exist_client(client_id) == False:
               self.cursor.execute("INSERT INTO clients(Id, username, first_name) VALUES(?, ?, ?)",
                                (client_id, client_username, client_first_name))
    def check_exist_client(self, clientid):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM clients where Id = ?', (clientid,)).fetchall()
        if len(result) > 0:
            return True
        else:
            return  False
    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()


    def set_client_phone(self,contact, username):
        """
        Добавляем телефон клиента
        :param contact: Отправленный клиентом контакт
        :param username: юзернейм клиента
        """
        with self.connection:
            if self.check_exist_client(contact.user_id):
                self.cursor.execute("UPDATE clients SET phone_number = ? WHERE Id = ?",
                                        (contact.phone_number, contact.user_id))
            else:
               self.cursor.execute("INSERT INTO clients(Id, username, first_name, phone_number) VALUES(?, ?, ?, ?)",
                                (contact.user_id, username, contact.first_name, contact.phone_number))
        return None

    def set_order (self, Id, IdClient, Item, Vol, OrderTime):
        """
        Добавляем заказ. Из параметров Item, Vol, OrderTime передаем только один.
        :param Id: Id заказа.
        :param IdClient: Id пользователя.
        :param Item: Что покупаем.
        :param Vol: юзернейм клиента.
        :param OrderTime: юзернейм клиента.
        :return: ИД добавленной записи.
        """
        with self.connection:
            cursor = self.connection.cursor()
            #Добавляем что.
            if (IdClient is not None):
                # Вставляем заказ
                if (Item != "") and (Id is None):
                   cursor.execute("INSERT INTO Orders(IdClient, Item) VALUES(?, ?)",
                                    (IdClient, Item))
                   return cursor.lastrowid
                # Добавляем объем заказа
                if (Vol is not None) and (Id is not None):
                   cursor.execute("UPDATE Orders SET Vol = ? WHERE Id = ?",
                                        (Vol, Id))
                   return Id
                # Добавляем время заказа
                if (OrderTime is not None) and (Id is not None):
                   cursor.execute("UPDATE Orders SET OrderTime = ?, DateCreate = strftime('%s','now') WHERE Id = ?",
                                        (OrderTime, Id))
                   return Id
            else:
                return None

    def get_order_string(self, id, tobar = 0):
        with self.connection:
            # Текст заказа для клиента
            if tobar == 0:
                res = self.cursor.execute('SELECT Item, Vol, OrderTime   FROM orders where Id = ?',
                                       (id,)).fetchall()[0]
                if res is not None:
                    return res[0] + ', ' + res[1] + ', ' + res[2]

            # Текст заказа для баристы
            elif tobar == 1:
                res = self.cursor.execute('SELECT Item, Vol, OrderTime, Clients.first_name, orders.Id FROM '
                                          'Orders LEFT JOIN Clients ON orders.IdClient = Clients.Id where Orders.Id  = ?',
                                       (id,)).fetchall()[0]
                if res is not None:
                    return '# ' + str(res[4]) + ' Name: ' + res[3]+ ', ' + res[0] + ', ' + res[1] + ', ' + res[2]
            else:
                return None

