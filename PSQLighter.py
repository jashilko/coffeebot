# -*- coding: utf-8 -*-
# Файл для работы с бд

'''
 Для heroku придётся использовать базу данных,
 т.к. данные не сохраняются
'''

import psycopg2
import dj_database_url 
from datetime import datetime

# Для представления ссылки на базу в её данные (логин, пароль и т.д.) postgres://USER:PASSWORD@HOST:PORT/NAME

class PSQLighter:
    
    def __init__(self):
        try:
            #Строка для Cloud9
            #database = "dbname=test_database user=test_user password=qwerty host=localhost port=5432"
            
            # Строка для heroku
            database = "dbname=dcpuk30ncm8l9i user=uxwkaztpfcmjos password=9IzK-mqlx80bZ7WBTJUW3V9qEW host=ec2-204-236-228-133.compute-1.amazonaws.com port=5432"
            
            self.connection = psycopg2.connect(database)
            self.cursor = self.connection.cursor()
            self.connection.set_client_encoding('UTF8')
        except Exception as e:
            print("Ошибка __init__: %s" %str(e))  

    # Проверка клиента на существование.
    def check_exist_client(self, clientid):
        cursor = self.connection.cursor()
        cursor.execute('''SELECT count(*) FROM clients where Id = %s;'''%(clientid))
        result = cursor.fetchone()      
        count = result[0]
        print ("res - " + str(result[0]))
        if count > 0:
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
                self.cursor.execute('''UPDATE clients SET phone_number = \'%s\' WHERE Id = %s;'''%(contact.phone_number, contact.user_id))
            else:
               self.cursor.execute('''INSERT INTO clients(Id, username, first_name, phone_number) VALUES(%s, \'%s\', \'%s\', \'%s\');'''%(contact.user_id, username, contact.first_name, contact.phone_number))
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
        try:
            with self.connection:
                cursor = self.connection.cursor()
                #Добавляем что.
                if (IdClient is not None):
                    # Вставляем заказ
                    if (Item != "") and (Id is None):
                       cursor.execute('''INSERT INTO Orders(IdClient, Item) VALUES (%s, \'%s\') RETURNING id;'''%(IdClient, Item))
                       id_of_new_row = cursor.fetchone()[0]
                       self.connection.commit
                       return id_of_new_row
                    # Добавляем объем заказа
                    if (Vol is not None) and (Id is not None):
                       cursor.execute('''UPDATE Orders SET Vol = \'%s\' WHERE Id = %s ;'''%(Vol, Id))
                       self.connection.commit
                       return Id
                    # Добавляем время заказа
                    if (OrderTime is not None) and (Id is not None):
                       dt = datetime.now()
                       cursor.execute('''UPDATE Orders SET OrderTime = \'%s\', DateCreate = \'%s\' WHERE Id = %s;'''%(OrderTime, dt,  Id))
                       self.connection.commit                     
                       return Id
                else:
                    return None
        except Exception as e:
            print("Ошибка set_order: %s" %str(e))                      
        

    def get_order_string(self, id, tobar = 0):
        try:
            with self.connection:
                cursor = self.connection.cursor()
                # Текст заказа для клиrента
                if tobar == 0:
                    cursor.execute('''SELECT Item, Vol, OrderTime   FROM orders where Id = %s;'''%(id))
                    res = cursor.fetchone()
                    if res[1] is None:
                        r1 = ''
                    else:
                        r1 = res[1]
                    return res[0] + ', ' + r1 + ', ' + res[2]
    
                # Текст заказа для баристы
                elif tobar == 1:
                    res = cursor.execute('''SELECT Item, Vol, OrderTime, Clients.first_name, orders.Id FROM Orders LEFT JOIN Clients ON orders.IdClient = Clients.Id where Orders.Id  = %s;'''%(id))
                    res = cursor.fetchone()
                    if res[1] is None:
                        r1 = ''
                    else:
                        r1 = res[1]
    
                    if res is not None:
                        return '# ' + str(res[4]) + ' Name: ' + res[3]+ ', ' + res[0] + ', ' + r1 + ', ' + res[2]
                else:
                    return None
        except Exception as e:
            print("Ошибка get_order_string : %s" %str(e))  
        
    def del_order(self, id):
        """
        Удаляем заказ.
        :param id: Id заказа.
        """
        try:
            with self.connection:
                if (id is not None):
                   self.cursor.execute('''DELETE FROM Orders where Id = %s;'''%(id))
            return None     
        except Exception as e:
            print("Ошибка del_order : %s" %str(e))          