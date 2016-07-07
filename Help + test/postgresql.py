# Файл для работы с бд

'''
 Для heroku придётся использовать базу данных,
 т.к. данные не сохраняются
'''

import psycopg2
import dj_database_url # Для представления ссылки на базу в её данные (логин, пароль и т.д.) postgres://USER:PASSWORD@HOST:PORT/NAME

db_info = dj_database_url.config(default="postgres://postgree:1234Qwer@localhost:5432/test")

# Создание таблицы
def tb_make():
    print(db_info.get('PASSWORD'))
    # Создаём соединение

    connection = psycopg2.connect("dbname=dcpuk30ncm8l9i user=uxwkaztpfcmjos password=9IzK-mqlx80bZ7WBTJUW3V9qEW host=ec2-204-236-228-133.compute-1.amazonaws.com port=5432")


#    connection = psycopg2.connect(
#        database=url.path[1:],
#        user=url.username,
#        password=url.password,
#        host=url.hostname,
#        port=url.port
#    )
    # Курсор - исполнитель команд на языке SQl для нашей бд
    cursor = connection.cursor()
    # Создаём табоицу, если её нет
    cursor.execute('''CREATE TABLE IF NOT EXISTS USERS
        (CHAT_ID INT PRIMARY KEY NOT NULL,
        TOKEN VARCHAR(250));''')
    # Сохраняем изменения и закрываем базу
    connection.commit()
    return connection


# Запись в базу данных
def writedb(dictionary):
    # Получаем соединение
    connection = tb_make()
    # Курсор
    cursor = connection.cursor()

    for key, val in dictionary.items():
        # Пробуем обновить данные. Если ошибка, то создадим запись
        cursor.execute(
            '''INSERT INTO USERS (CHAT_ID, TOKEN) VALUES (%s, \'%s\') ON CONFLICT (CHAT_ID) DO UPDATE set TOKEN = \'%s\';'''
            %(key, str(val), str(val))
        )
        # Завершаем операцию, сохраняем
        connection.commit()
    # Сохраняем изменения
    connection.commit()
    connection.close()  # Закрываем соединение


# Чтение из базы
def readdb():
    connection = tb_make()  # Получаем соединение
    # Курсор
    cursor = connection.cursor()
    # Читаем базу
    response = cursor.execute('''SELECT CHAT_ID, TOKEN FROM USERS;''')
    users = cursor.fetchall()
    # Закрываем соединение
    connection.close()
    # Возвращаем данные
    return {str(user[0]): user[1] if user[1] != 'False' else False for user in users}