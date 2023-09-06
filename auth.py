import re
import unittest
import requests
import os
import sys
from common import RequestStatus
from typing import Tuple

# Файл с токеном сессии.
token_file_name: str = "./token"
# Адрес ответного скрипта на сервере.
url: str = "http://csvtest/cgi-bin/auth_cgi.py"


def parse_input(inp: list) -> Tuple[str, str]:
    """ Разбор входных параметров с их контролем.

    :param inp: список пар 'ключ-значение'
    :return: Значение ('', '') означает ошибку парсинга.
    """

    # Значения по умолчанию
    login: str = ''
    password: str = ''

    if len(inp) == 1:
        if inp[0] == '-help':
            print_help()
            exit()
        else:
            return '', ''

    if len(inp) > 2 or len(inp) == 0:
        # Если число параметров не два, метод возвращает ошибку
        return '', ''

    for param in inp:
        kv: list = param.split(sep='=')
        if len(kv) == 1:
            # Если в строке есть параметр без знака =, метод возвращает ошибку
            return '', ''
        else:
            if kv[0] == '-login':
                if len(kv[1]) == 0:
                    # Если длина логина нулевая, метод возвращает ошибку
                    return '', ''
                login = kv[1]
            elif kv[0] == '-password':
                if len(kv[1]) == 0:
                    # Если длина пароля нулевая, метод возвращает ошибку.
                    return '', ''
                password = kv[1]
            else:
                # Если из двух параметров строки хотя бы один не является логином или паролем, метод возвращает ошибку
                return '', ''

    return login, password


def print_help() -> None:
    print("\n"
          "Использование:\n"
          "auth.py -login=... -password=...\n"
          "auth.py -help\n"
          "\n"
          "Подробно о параметрах:\n"
          "-login       - логин пользователя\n"
          "-password    - пароль пользователя\n"
          "-help        - помощь\n")


# class Test(unittest.TestCase):
#     def test_check(self):
#         self.assertEqual(parse_input(['-login=is_login', '-password=is_password']), tuple(['is_login', 'is_password']))
#         self.assertEqual(parse_input(['-login=is_login', '-passwordis_password']), tuple(['', '']))
#         self.assertEqual(parse_input(['-loginis_login', '-password=is_password']), tuple(['', '']))
#         self.assertEqual(parse_input(['-login=is_login', '-passwor=dis_password', '-anystr']), tuple(['', '']))
#         self.assertEqual(parse_input(['-login=is_login', '-passwordis_password', '-anystr=anyfoo']), tuple(['', '']))
#         self.assertEqual(parse_input(['-login=is_login']), tuple(['', '']))
#         self.assertEqual(parse_input(['-password=is_password']), tuple(['', '']))


if __name__ == '__main__':
    # unittest.main()

    # Удаление имени приложения из аргументов командной строки.
    sys.argv.pop(0)

    # Парсинг командной строки.
    login, password = parse_input(sys.argv)

    if len(login) == 0:
        # разбор команд не удался
        exit()

    # Получение токена
    response: requests.Response = requests.\
        get(url + '?login={0}&password={1}'.format(login, password))
    # Деление ответа на две строки (в первой статус, во второй - токен)
    response: list = response.text.split(sep='\r\n')

    if int(response[0]) == RequestStatus.OK.value:
        # Токен получен
        with open(token_file_name, "w") as fn:
            # сохраняем токен
            fn.write(response[1])
        print("Token ({}) succesfull received and saved.".format(response[1]))
    else:
        # Токен не получен, ошибка.
        try:
            # Удаление, возможного, предыдущего файла с токеном.
            os.remove(token_file_name)
        except FileNotFoundError:
            pass
        print("Login not success, status: {}".format(RequestStatus(response[0]).name))
