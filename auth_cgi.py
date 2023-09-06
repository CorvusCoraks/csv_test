#!E:\miniconda3\envs\csv_test\python
from urllib.parse import parse_qs
import os
from common import RequestStatus, TokenType
import unittest
from db import UsersDBInterface, SQL, SESSION_WAITING_TIME
import db_data


def check_query(query: dict) -> RequestStatus:
    """ Метод проверки качества HTTP-запроса.

    :param query: HTTP-запрос.
    :return: Статус обработки.
    """
    # Возможные возвращаемые значения: RequestStatus.OK, RequestStatus.BAD_REQUEST
    if len(query) == 2:
        return RequestStatus.OK
    else:
        return RequestStatus.BAD_REQUEST


def auth(db: UsersDBInterface, login: str, password: str) -> RequestStatus:
    """ Аутентификация пользователя.

    :param db: Интерфейс доступа к базе данных с пользователями.
    :param login: Логин пользователя.
    :param password: Пароль пользователя.
    :return: Статус обработки.
    """
    # Возможны три возвращаемых значения: RequestStatus.OK, RequestStatus.USER_NOT_FOUND, RequestStatus.WRONG_PASSWORD
    if db.is_real_user(login):
        if not db.login(login, password):
            return RequestStatus.WRONG_PASSWORD
        return RequestStatus.OK
    else:
        return RequestStatus.USER_NON_FOUND


def get_token(db: UsersDBInterface, login: str) -> TokenType:
    """ Получение токена сессии из БД.

    :param db: Интерфейс доступа к базе данных пользователей.
    :param login: Логин пользователя.
    :return: Токен сеанса данного пользователя.
    """
    token = db.get_token(login)
    return token


# @unittest.skip
# class Tests(unittest.TestCase):
#     def test_check_query(self):
#         self.assertEqual(check_query({'login': ['gemma'], 'password': ['foo_pass']}), RequestStatus.OK)
#         self.assertEqual(check_query({'login': ['gemma'], 'any_key': ['foo_pass']}), RequestStatus.BAD_REQUEST)
#         self.assertEqual(check_query({'any_key': ['gemma'], 'password': ['foo_pass']}), RequestStatus.BAD_REQUEST)
#         self.assertEqual(check_query({'foo_key': ['gemma'], 'bar_key': ['foo_pass']}), RequestStatus.BAD_REQUEST)
#         self.assertEqual(check_query({'login': ['gemma'], 'password': ['foo_pass'], 'any_key': ['any_value']}),
#                          RequestStatus.BAD_REQUEST)


if __name__ == "__main__":
    # unittest.main()

    print("Content-Type: text/plain")
    print()

    db: UsersDBInterface = SQL(SESSION_WAITING_TIME, db_data.USER_NAME, db_data.USER_PASSWORD, db_data.DB_NAME,
                                 db_data.TABLE_NAME, db_data.DB_IP)

    # Дефолтные значения.
    status: RequestStatus = RequestStatus.OK
    token: TokenType = 0

    # Выделение запроса
    request = parse_qs(os.environ['QUERY_STRING'], keep_blank_values=True)
    # request = {'login': ['foo_login'], 'password': ['12345']}

    status = check_query(request)

    if status != RequestStatus.BAD_REQUEST:
        # Если запрос не какой-то "кривой"
        # аутентификация
        status = auth(db, request['login'][0], request['password'][0])
        if status == RequestStatus.OK:
            # Если аутентификация прошла успешно.
            token = get_token(db, request['login'][0])

    # Отправляем две строки: статус запроса, и токен
    # Если статус отрицательный, то токен будет пустой строкой.
    print(status.value)
    print(token)
