WARNINGS:
realty_displays.DisplayInSearch.realty: (fields.W342) Setting unique=True on a ForeignKey has the same effect as using a OneToOneField.
        HINT: ForeignKey(unique=True) is usually better served by a OneToOneField.
Migrations for 'realty_displays':
  realty_displays/migrations/0002_alter_displayinsearch_realty_and_more.py
    - Alter field realty on displayinsearch
    - Alter unique_together for displayfullinfo (1 constraint(s))
(venv) apple@philippios-imac Realty % python manage.py migrate
MAX_LISTING_DURATION 0:01:00
System check identified some issues:

WARNINGS:
realty_displays.DisplayInSearch.realty: (fields.W342) Setting unique=True on a ForeignKey has the same effect as using a OneToOneField.
        HINT: ForeignKey(unique=True) is usually better served by a OneToOneField.
Operations to perform:
  Apply all migrations: admin, auth, authtoken, chats, complaints, contenttypes, django_q, notifications, questions, realty, realty_addresses, realty_displays, realty_photos, realty_specificities, realty_values, sessions, users
Running migrations:
  Applying realty_displays.0002_alter_displayinsearch_realty_and_more... OK
(venv) apple@philippios-imac Realty % 
