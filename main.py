import os
import sys
import typing
from typing import Dict, List, Optional, Tuple
import requests
import pickle
import common
import csv
from common import TokenType

# Формат расшифрованного ответа на запрос.
Parsed = Dict[str, Optional[typing.Union[str, list]]]
# Адрес ответного скрипта на сервере.
url: str = "http://csvtest/cgi-bin/get_cgi.py"
# Относительный путь (относительно скрипта) к папке с сохраняемыми файлами.
saved_dir: str = '../files'
# Файл с токеном сеанса
token_file: str = "./token"


def parse_input(com_line: List[str]) -> Parsed:
    """ Парсинг параметров командной строки.

    :param com_line: список параметров командной строки.
    :return: словарь параметров командной строки.
    """
    # Если параметр командной строки не вида key=value, то его value равен None
    result: Parsed = {}
    for com in com_line:
        try:
            key, value = com.split(sep='=')
        except ValueError:
            result[com] = None
            continue
        result[key] = value
    return result


def print_help() -> None:
    print("\n"
          "Варианты использования:\n"
          "\n"
          "Получить список файлов: main.py -list [-info]\n"
          "Загрузить один файл: main.py -file=... [-cols=...,...,...] [sort=...,...,...] [-delete]\n"
          "\n"
          "Подробно о параметрах.\n"
          "-list        - загрузка списка csv файлов\n"
          "-info        - показать информацию о содержимом файла\n"
          "-file        - имя файла, вида 'foo.csv'\n"
          "-cols        - список необходимых колонок, вида 'foo,bar,baz' (без пробелов)\n"
          "-sort        - сортировка запрошенных колонок, вида 'foo,bar' (без пробелов)\n"
          "-delete      - удалить ранее загруженные файлы\n"
          "-help        - помощь.\n")


def send_request(url: str, params: Dict[str, str], headers: Dict[str, str]) -> Tuple[common.RequestStatus, dict]:
    """ Отправка HTTP-запроса.

    :param url: адрес запроса. Может указывать на директорию или на отдельный .csv-файл.
    :param params: параметры запроса
    :param headers: заголовок запроса. Обязательно с 'Content-Type': 'application/octet-stream'
    :return: расшифрованный ответ HTTP-сервера в виде словаря с двумя полями: 'status' и 'content'
    """
    try:
        # Чтение токена сессии
        with open(token_file, 'r') as tf:
            token: str = tf.readline()
            # Попытка привезти прочитанную строку к типу токена, если не токен, то вылетит ошибка.
            TokenType(token)
            params['token'] = token
    except FileNotFoundError:
        raise FileNotFoundError("Отсутствует файл с токеном.")
    except TypeError:
        raise TypeError("В файле, где должен быть токен, находится не токен.")

    response = requests.get(url, params=params, headers=headers)

    # декодируем байтовый поток в строку вида "b'...'" и превращаем эту строку в bytes-объект
    bytes_obj = eval(response.content.decode())
    # десериализация byte-объекта в словарь с данными
    dict_response: dict = pickle.loads(bytes_obj)

    return dict_response['status'], dict_response['content']


def unic_filename(filename: str) -> str:
    """ Если в папке сохранений уже есть файл с таким именем, функция создаёт новое уникальное имя
    для этого файла по принципу: foo.csv -> foo0.csv -> foo1.csv и т. д. """

    result_filename: str = filename

    i = -1
    while os.path.isfile(result_filename):
        # Пока находится файл с таким же именем в папке для сохранений.
        #
        # Добавление в конец имени файла числа, начиная с нуля.
        # Если и такой файл существует, инкрементируем добавляемое число.
        i += 1
        # И так до тех пор, пока полученное имя файла не будет уникальным.
        result_filename = filename[:-4] + repr(i) + '.csv'

    return result_filename


if __name__ == '__main__':
    # Удаление имени приложения из аргументов командной строки.
    sys.argv.pop(0)

    # Распознанный ввод командной строки.
    parsed_commands: Parsed = parse_input(sys.argv)

    # Параметры запроса.
    params: dict = {}

    if '-help' in parsed_commands.keys():
        print_help()
    elif '-file' in parsed_commands.keys():
        # Указание на конкретный файл csv.

        if "-delete" in parsed_commands.keys():
            # Удаление файлов, полученных ранее (очистка директории с загруженными файлами на локальной машине).
            for filename in os.listdir(saved_dir):
                os.remove(saved_dir + '/' + filename)

        params['file'] = parsed_commands['-file']
        if "-cols" in parsed_commands.keys():
            # Получение только указанных колонок.
            params['cols'] = parsed_commands['-cols']

        if "-sort" in parsed_commands.keys():
            # Сортировка файла по указанным в списке столбцам
            params['sort'] = parsed_commands['-sort']

        status, content = send_request(url, params, {'Content-Type': 'application/octet-stream'})

        if status == common.RequestStatus.OK:
            filename = saved_dir + '/' + parsed_commands['-file']

            filename = unic_filename(filename)

            try:
                with open(filename, 'w') as csvfile:
                    # Запись в файл
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerows(content)
            except:
                print("Не удалось сохранить файл.")
        else:
            # Ошибка
            print("Error. {} - {}".format(status.value, status.name))
    else:
        if "-list" in parsed_commands.keys():
            # Получение списка файлов csv из директории.
            params['list'] = ''
            if "-info" in parsed_commands.keys():
                # Список файлов с информацией о столбцах в каждом.
                params['info'] = ''

            status, content = send_request(url, params, {'Content-Type': 'application/octet-stream'})

            if status == common.RequestStatus.OK:
                for filename, fields in content.items():
                    print(filename, ': ', fields)
            else:
                # Ошибка
                print("Error. {} - {}".format(status.value, status.name))

        else:
            # Не хватает команд для работы с директорией, указанной в URL
            print("Ошибка. Команды не опознаны. Для справки используйте параметр -help.")
