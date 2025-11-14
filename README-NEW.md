
Первичная популяция данными

###  1) ADD FIRST USER - ADMIN (with default pass)

```
python manage.py loaddata Z_DATA/db_dump_before_deploy_refactor_2025_11/01_BATCH/users.user.json
```

What the heck - What is user_type in user app?
How can user be only Собственник/Арендатор/Агент?
В разных сделках он разный!

### 2) ADD MODERATOR AND Moderator Group with permissions

```
python manage.py fix_moderator_permissions
```

Начало базы работает!


### 3) Загружаем большинство следующих справочников

```
find Z_DATA/db_dump_before_deploy_refactor_2025_11/02_BATCH_MAIN/ -name "*.json" -print0 | xargs -0 python manage.py loaddata
```

### 4) Оставляем незагруженными в папке 99_REMOVED:
auth.group.json
auth.permission.json
realty_addresses.district.json
realty_addresses.zone.json

----------

Добавление базовых данных завершено.


