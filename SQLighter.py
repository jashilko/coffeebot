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
    def check_exist_client(self, client):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM clients where Id = ?', (client,)).fetchall()
        if len(result) > 0:
            return True
        else:
            return  False
    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()