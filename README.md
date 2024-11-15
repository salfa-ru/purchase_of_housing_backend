# purchase_of_housing_backend

## Описание:
MVP Backend-проекта сервиса по продаже и аренде жилья в г. Москва

## Как работать с проектом:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:salfa-ru/purchase_of_housing_backend.git
```
```
cd purchase_of_housing_backend
```
Создать и активировать виртуальное окружение:
```
py -3.11 -m venv venv
```
```
source venv/Scripts/activate
```
Установить зависимости из файла requirements.txt:
```
python -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
В корне проекта создать файл .env
```
touch .env
```
и заполнить его по следующему образцу:
```
# Переменные для PostgreSQL
POSTGRES_DB=realty_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Переменные для Django_settings
SECRET_KEY=your_secret_key
HOST_IP=127.0.0.1
DEBUG=True
```
Выполнить миграции
```
python manage.py makemigrations
python manage.py migrate
```


## Загрузка тестовых значений в БД
### Вариант 1
Грузим все данные вместе
```
python manage.py loaddata data.json
```
### Вариант 2
Грузим данные со значениями (values, questions, шаблоны в notifications) 
```
python manage.py loaddata data_values.json
```
Грузим все остальные данные 
```
python manage.py loaddata data_other.json
```

Прим.: среди данных созданы 2 обычных пользователя: Иван и Петр (пароль 123) и один админ.
Их id – 2, 3 и 4, и чтобы т.е. чтобы загрузка данных прошла успешно, в БД не должно быть пользователей с таким id.
### Добавляем группу ALFA Moderators, задаем ей права и вводим первого Модератора
```
python manage.py fix_moderator_permissions
```
Модератор по умолчанию ищется по адресу электронной почты `moderator@moderator.ru`, <br> 
и, независимо от того, создается новый пользователь или обновляется старый, ему задаются <br>
username: `moderator` <br>
password: `moderator` <br>

**На момент публикации ему даны** 
- права на просмотр всех таблиц (кроме сервисных таблиц `Django-Q`), 
- таблица **Сообщения** - все права *(но закрыта "отправка" сообщений от чужого имени и изменение отправителя у существующих сообщений)*
- таблица **Realty** - права редактирования

При перенастройке прав группы ALFA Moderators, достаточно перезапустить скрипт `fix_moderator_permissions`<br>
и все пользователи, являющиеся членами этой группы, получат новые права.


## Ссылки на доки/описания

- [Работа с пользователем](docs/user_doc.md)
- [Деактивация старых объявлений](docs/deactivation.md) <sup>NEW</sup>

## Запуск приложения 

Для включения функций деактивации объявлений:
```bash
# Запуск management command (хотя бы один раз за срок жизни базы): 
# - деактивирует expired объявления при своем запуске 
# - создаст или перезапишет задачу на такую деактивацию 
# (будет выполняться ежечасно)
python manage.py cleanapp

# Запуск Django 
python manage.py runserver

# Запуск Q-CLUSTER - pool of workers that will handle your tasks
python manage.py qcluster
 ```


## ВАЖНО!
### Каждый создает свою ветку по образцу "ваш никнейм или имя / краткое название ветки, отображающее сущность работ. Работаем в своих ветках, в свои же ветки свой код пушим. Делать слияние будем после кросс-ревью."
Пример: "kons/messaging_models" или "anna_k/realty_serializer". 


