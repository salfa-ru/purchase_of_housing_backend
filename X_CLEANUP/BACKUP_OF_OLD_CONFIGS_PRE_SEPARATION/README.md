# purchase_of_housing_backend

## Описание:
Здесь хранятся файлы старой конфигурации Backend-сервера.
```
docker-compose-yml
Dockerfile
nginx.conf
Папка .github
```
В этой конфигурации (а также с неправильно настроенными .env файлами и settings.py на сервере запускалось три контейнера
```
purchase_of_housing_backend-nginx-1
purchase_of_housing_backend-backend-1
purchase_of_housing_backend-db-1
```
При этом
- prod и test запускается из одного контейнера
- с одним и тем же .env файлом
- база данных для обеих веток используется SQLite - одна и та же,
- соответственно данные, добавляемые на test показываеются на prod и наоборот
