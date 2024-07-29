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
## ВАЖНО!
## каждый создает свою ветку по образцу "ваш никнейм или имя / краткое название ветки, отображающее сущность работ. Работаем в своих ветках, в свои же ветки свой код пушим. Делать слияние будем после кросс-ревью."
Пример: "kons/messaging_models" или "anna_k/realty_serializer". 
