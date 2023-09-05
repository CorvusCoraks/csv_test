#!E:\miniconda3\envs\csv_test\python
from urllib.parse import parse_qs
import os
from common import RequestStatus, TokenType
import unittest
from typing import Optional, Any, List, Dict, Tuple, Set
import csv
from operator import itemgetter
import pickle
from db import UsersDBInterface, SQL, SESSION_WAITING_TIME


# Представление файла .csv внутри скрипта: список кортежей, где каждый кортеж - одна строка файла.
ContentView = List[tuple]
# Относительный путь к директории с файлами.
files_dir: str = "../files"
# Разделитель множественных значений в запросе
in_value_separator: str = ','


def check_query(query: dict) -> RequestStatus:
    """ Метод проверки качества HTTP-запроса.

    :param query: запрос, поступивший в скрипт.
    """
    status = RequestStatus.OK

    if 'token' not in query.keys():
        status = RequestStatus.BAD_REQUEST

    return status


def get_list(files_dir: str, with_info: bool = False) -> Dict[str, tuple]:
    """ Получить список файлов.

    :param files_dir: папка с файлами.
    :param with_info: получить список файлов с информацией о столбцах.
    :return: Словарь вида {'имя файла': (кортеж имён столбцов)}
    """
    file_dict = {filename: tuple('') for filename in os.listdir(files_dir)}

    if with_info:
        result: dict = {}
        for filename in file_dict:
            with open(files_dir + '/' + filename) as csvfile:
                csvreader = csv.reader(csvfile)
                for row in csvreader:
                    result[filename] = tuple(row)
                    break
        return result
    else:
        return file_dict


def get_file(filepath: str, cols: Optional[List[str]] = None) -> \
        Tuple[RequestStatus, Optional[tuple], Optional[ContentView]]:
    """ Чтение файла.

    :param filepath: имя файла с путём
    :param cols: список желаемых колонок
    :return: Статус запроса, Кортеж заголовков столбцов, Список кортежей (каждый кортеж - одна строка файла)
    """
    # Если файл не найден, то возвращается: (RequestStatus.NON_FOUND, None, None)

    # Индекс желаемых столбцов в файле csv
    index: Set[int] = set()

    # Заголовок исходного csv-файла
    header: tuple = tuple()
    # Заголовок прочитан из файла
    is_header_ready: bool = False
    # Содержимое файла (только затребованные столбцы)
    content: List[tuple] = []
    try:
        # Цикл чтения файла
        with open(filepath) as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                if not is_header_ready:
                    header = tuple(row)

                    if cols:
                        # Если нужны не все столбцы
                        for colname in cols:
                            # Заполнение списка индексов желаемых столбцов
                            try:
                                index.add(header.index(colname))
                            except ValueError:
                                # Если колонка с таким именем в файле отсутствует
                                return RequestStatus.BAD_REQUEST, None, None

                    is_header_ready = True
                    continue

                if cols:
                    # Добавление запрошенных столбцов
                    filtered: tuple = tuple(value for idx, value in enumerate(row) if idx in index)
                    content.append(filtered)
                else:
                    # Добавление всех столбцов
                    content.append(tuple(row))
    except FileNotFoundError:
        # Файл не найден
        return RequestStatus.NON_FOUND, None, None

    # Создание заголовка csv-файла
    header = header if not cols else tuple(value for idx, value in enumerate(header) if idx in index)

    return RequestStatus.OK, header, content


def sort(header: Tuple[str], content: ContentView, cols: List[str]) -> Tuple[RequestStatus, ContentView]:
    """ Сортировка.

    :param header: Кортеж из названий столбцов файла.
    :param content: Неотсортированное содержимое файла.
    :param cols: Список колонок, по которым необходима сортировка.
    :return: Статус запроса, отсортированное содержимое файла.
    """
    # Список индексов колонок
    index: List[int] = []

    for colname in cols:
        # Заполнение списка индексов желаемых столбцов
        try:
            index.append(header.index(colname))
        except ValueError:
            # Если колонка с таким именем в файле отсутствует
            return RequestStatus.BAD_REQUEST, [()]

    # Сортировка по запрошенным полям.
    content = sorted(content, key= itemgetter(*index))

    return RequestStatus.OK, content


def send_answer(status: RequestStatus, data: Any) -> None:
    """ Отправка ответа на запрос в виде потока байт.

    :param status: Статус запроса.
    :param data: Данные, которые будут отправлены.
    """
    # Данные будут отправлены в виде словаря.
    answer: dict = {'status': status, 'content': data}
    # Сериализация
    serialized = pickle.dumps(answer)
    # Отправка.
    print("Content-Type: application/octet-stream")
    print("")
    print(serialized)


def is_session_active(db: UsersDBInterface, token: TokenType) -> bool:
    """ Проверка на то, что время сессии не истекло.

    :param db: Интерфейс доступа к базе данных с пользователями.
    :param token: Токен сеанса для данного пользователя.
    """
    if db.check_token(token) == RequestStatus.OK:
        # Если токен существует в базе данных и он актуален.
        db.renew_timestamp(token)
        # Освежаем время последнего обращения.
        return True
    else:
        # Токен устарел или его просто нет в базе данных. Нужна повторная авторизация.
        return False


if __name__ == "__main__":
    # unittest.main()

    # Выделение запроса
    request = parse_qs(os.environ['QUERY_STRING'], keep_blank_values=True)
    # request = {'file':['bar.csv'], 'cols': ['foo,bar'], 'sort':['foo,bar']}
    # request = {'list':'', 'info': ''}
    # request = {'list':'', 'token': '12345'}

    status = check_query(request)

    if status == RequestStatus.BAD_REQUEST:
        # Запрос "кривой", ошибка.
        send_answer(status, None)
        exit()

    if not is_session_active(SQL(SESSION_WAITING_TIME), TokenType(request['token'][0])):
        # Токен устарел, сессия закрыта.
        send_answer(RequestStatus.REQUEST_TIMEOUT, None)
        exit()

    if 'file' in request.keys():
        # Работа с отдельным файлом.
        filepath = files_dir + '/' + request['file'][0]
        if os.path.isfile(filepath):
            # проверка файла на существование.
            if 'cols' in request.keys():
                # Получение только указанных колонок.
                status, header, content = get_file(filepath, request['cols'][0].split(sep=in_value_separator))
            else:
                # Получение Всех колонок.
                status, header, content = get_file(filepath)

            if status == RequestStatus.BAD_REQUEST or status == RequestStatus.NON_FOUND:
                # Не удалось прочитать содержимое файла.
                send_answer(status, None)
                exit()

            if 'sort' in request.keys():
                # Сортировка файла по указанным в списке столбцам
                status, content = sort(header, content, request['sort'][0].split(sep=in_value_separator))

            content.insert(0, header)
            send_answer(status, content)
        else:
            send_answer(RequestStatus.NON_FOUND, None)
    else:
        # Работа с папкой по умолчанию.
        if 'list' in request.keys():
            # Получение списка файлов csv из директории.
            if 'info' in request.keys():
                # Список файлов с информацией о столбцах в каждом.
                files_list = get_list(files_dir, with_info=True)
            else:
                # Список файлов без информации
                files_list = get_list(files_dir)

            send_answer(RequestStatus.OK, files_list)

        else:
            # Запрос не опознан.
            send_answer(RequestStatus.BAD_REQUEST, None)
