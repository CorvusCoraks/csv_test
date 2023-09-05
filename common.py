from enum import Enum


# Тип токена, идентифицирующего сеанс
TokenType = int


class RequestStatus(Enum):
    """ Результаты обработки запросов. """
    # Результат обработки - успешно
    OK = 200
    # Сервер не понял запроса
    BAD_REQUEST = 400
    # Требуется авторизация
    UNAUTHORIZED = 401
    # Запрошенный файл не найден
    NON_FOUND = 404
    # Сессия истекла
    REQUEST_TIMEOUT = 408
    # Дополнительно
    # Пользователь не обнаружен
    USER_NON_FOUND = 4010
    # Неверный пароль
    WRONG_PASSWORD = 4011
