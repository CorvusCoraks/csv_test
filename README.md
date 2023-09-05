HTTP-сервис по загрузке .csv-файлов с сервера на локальный компьютер.

Функционал:
1. Получение списка файлов (как с информацией о столбцах, так и без).
2. Получение конкретного файла (как всех столбцов, так и выбранных).
3. Предварительная сортировка (на сервере) указанных столбцов файла.
4. Авторизация пользователя.

Структура каталогов.

Сервер:
/user/cgi-bin/ - директория с скриптами (get_cgi.py, auth_cgi.py, common.py, db.py)
/user/files/ - директория с .csv-файлами

Клиент:
csv_test/script/ - директория со скриптами (main.py, auth.py, common.py, db.py, token)
csv_test/files/ - директория с загруженными файлами csv.

Описание модулей.
- get_cgi.py - модуль работы с файлами csv.
- auth_cgi.py - модуль авторизации пользователя.
- common.py - модуль общих классов и методов.
- db.py - модуль работы с базой данных пользователей.
- token - файл содержащий токен сеанса
- main.py - модуль получения файлов .csv
- auth.py - модуль аутентификации пользователя.

Параметры базы данных пользователей "вшиты" в класс SQL.
Запись базы данных состоит из полей: login, password, timestamp, token.
В поле timestamp фиксируется момент последнего обращения пользователя к серверу.
Если с последнего обращения пользователя прошло больше SESSION_WAITING_TIME секунд, то сессия считается закрытой 
и необходима повторная аутентификация пользователя.
Поле token содержит, собственно, токен для идентификации пользователя в процессе одной сессии 
(чтобы не передавать повторно и многократно пароль пользователя.)

Аутентификация с клиента.
    auth.py -login=... -password=...
    auth.py -help
    
    Подробно о параметрах:
    -login       - логин пользователя
    -password    - пароль пользователя
    -help        - помощь

Получить список файлов:
    main.py -list [-info]
Загрузить один файл:
    main.py -file=... [-cols=...,...,...] [sort=...,...,...] [-delete]

Подробно о параметрах.
    -list        - загрузка списка csv файлов
    -info        - показать информацию о содержимом файла
    -file        - имя файла, вида 'foo.csv'
    -cols        - список необходимых колонок, вида 'foo,bar,baz' (без пробелов)
    -sort        - сортировка запрошенных колонок, вида 'foo,bar' (без пробелов)
    -delete      - удалить ранее загруженные файлы
    -help        - помощь.