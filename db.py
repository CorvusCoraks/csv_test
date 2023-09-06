""" Модуль работы с базами данных. """
import abc
from common import RequestStatus, TokenType
import mysql.connector
from datetime import datetime, timedelta
import random
import db_data


# Время бездействия сессии, сек
SESSION_WAITING_TIME = 60


class UsersDBInterface(abc.ABC):
    """ Интерфейс связи с базой данной с пользователями. """

    @abc.abstractmethod
    def is_real_user(self, login: str, ) -> bool:
        """ Пользователь есть в базе? """
        ...

    @abc.abstractmethod
    def login(self, login: str, password: str) -> bool:
        """ Логин пользователя в систему (обновление токена сеанса)"""
        ...

    @abc.abstractmethod
    def get_token(self, login: str) -> TokenType:
        """ Получение токена текущего сеанса пользователя. """
        ...

    @abc.abstractmethod
    def renew_timestamp(self, token: TokenType) -> None:
        """ Обновление времени обращения. """
        ...

    @abc.abstractmethod
    def check_token(self, token: TokenType) -> RequestStatus:
        """ Проверка токена на актуальность. Вдруг его время уже истекло, или такого токена не существует? """
        ...


class SQL(UsersDBInterface):
    """ Возможная реализация. """
    def __init__(self, waiting_time: int, script_user: str, script_pass: str, db: str, table: str, ip: str):
        """

        :param waiting_time: Время допустимого простоя.
        :param script_user: Имя пользователя (для скрипта)
        :param script_pass: Пароль пользователя (для скрипта)
        :param db: Имя базы данных
        :param table: Таблица базы данных с пользователями.
        :param ip: ip-адрес SQL-сервера.
        """
        super().__init__()
        # Время допустимого простоя в ожидании очередного обращения одного пользователя.
        # Если время истекло, сеанс считается завершённым и токен сессии становится неактуальным.
        # Будет нужна новая авторизация.
        self.__waiting_time = waiting_time
        self.__db_user: str = script_user
        self.__db_password: str = script_pass
        self.__db: str = db
        self.__table: str = table
        self.__host: str = ip

    def __token_generate(self) -> TokenType:
        """ Генерация токена сеанса. """
        return random.randint(10000, 99999)

    def is_real_user(self, login: str) -> bool:
        # Начальное значение: ответ из БД пустой
        result: bool = False

        cnx = mysql.connector.connect(user=self.__db_user, password=self.__db_password,
                                      host=self.__host,
                                      database=self.__db)
        # Обязательно buffered=True
        # https://stackoverflow.com/questions/29772337/python-mysql-connector-unread-result-found-when-using-fetchone
        # Ответ БД в виде словаря
        cursor = cnx.cursor(buffered=True, dictionary=True)
        query = ("SELECT login, password FROM {} "
                 "WHERE login = '{}'".format(self.__table, login))

        cursor.execute(query)

        # Если ответа из БД нет (значение не найдено), то в цикл for вообще не заходит
        for answer in cursor:
            if 'login' in answer.keys():
                result = True

        cursor.close()
        cnx.close()
        return result

    def login(self, login: str, password: str) -> bool:
        cnx = mysql.connector.connect(user=self.__db_user, password=self.__db_password,
                                      host=self.__host,
                                      database=self.__db)
        # Ответ БД в виде словаря
        cursor = cnx.cursor(buffered=True, dictionary=True)
        query = ("UPDATE {} SET timestamp='{}', token={} "
                 "WHERE login='{}'".format(self.__table, datetime.today(), self.__token_generate(), login))
        cursor.execute(query)

        cnx.commit()

        return True

    def get_token(self, login: str) -> TokenType:
        result = 0
        cnx = mysql.connector.connect(user=self.__db_user, password=self.__db_password,
                                      host=self.__host,
                                      database=self.__db)
        cursor = cnx.cursor(buffered=True, dictionary=True)
        query = ("SELECT token FROM {} "
                 "WHERE login = '{}'".format(self.__table, login))
        cursor.execute(query)

        # Если ответа из БД нет (значение не найдено), то в цикл for вообще не заходит
        for answer in cursor:
            result = answer['token']

        cursor.close()
        cnx.close()
        return result

    def renew_timestamp(self, token: TokenType) -> None:
        cnx = mysql.connector.connect(user=self.__db_user, password=self.__db_password,
                                      host=self.__host,
                                      database=self.__db)
        # Ответ БД в виде словаря
        cursor = cnx.cursor(buffered=True, dictionary=True)
        query = ("UPDATE {} SET timestamp='{}' "
                 "WHERE token={}".format(self.__table, datetime.today(), token))
        cursor.execute(query)

        cnx.commit()

        cursor.close()
        cnx.close()

    def check_token(self, token: TokenType) -> RequestStatus:
        # Значение по умолчанию
        default: datetime = datetime(1970, 1, 1, 00, 00, 00)
        timestamp: datetime = default

        cnx = mysql.connector.connect(user=self.__db_user, password=self.__db_password,
                                      host=self.__host,
                                      database=self.__db)
        cursor = cnx.cursor(buffered=True, dictionary=True)
        query = ("SELECT timestamp FROM {} "
                 "WHERE token = {}".format(self.__table, token))
        cursor.execute(query)

        # Если ответа из БД нет (значение не найдено), то в цикл for вообще не заходит
        for answer in cursor:
            timestamp = answer['timestamp']

        cursor.close()
        cnx.close()

        if timestamp is default:
            # Таймстэмп не найден в базе данных
            return RequestStatus.UNAUTHORIZED

        if datetime.today() - timestamp > timedelta(seconds=self.__waiting_time):
            # Время паузы для этого сеанса истекло.
            return RequestStatus.REQUEST_TIMEOUT

        return RequestStatus.OK
