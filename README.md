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
Cоздать и активировать виртуальное окружение:
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

Прим.: среди данных созданы 2 обычных пользователя: Иван и Петр, пароль 123; и один админ.
Пользователи под id 2, 3, 4, т.е. чтобы загрузка данных прошла успешно, в БД не должно быть пользователей с таким id.

## Ссылки на доки/описания

- [Работа с пользователем](docs/user_doc.md)


## ВАЖНО!
## каждый создает свою ветку по образцу "ваш никнейм или имя / краткое название ветки, отображающее сущность работ. Работаем в своих ветках, в свои же ветки свой код пушим. Делать слияние будем после кросс-ревью."
Пример: "kons/messaging_models" или "anna_k/realty_serializer". 


