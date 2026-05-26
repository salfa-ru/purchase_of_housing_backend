# python manage.py shell < Z_DATA/dp_dump.py

from django.apps import apps as django_apps
from django.core.management import call_command

# Folder to store dumps
# os.makedirs("Z_DATA/db_dump_before_deply_refactor", exist_ok=True)

# Applications to exclude from dumping
exclude_apps = [
    'admin',
    'authtoken',
    'chats',
    'complaints',
    'contenttypes',
    'corsheaders',
    'django_q',
    'django_filters',
    'drf_spectacular',
    'messages',
    'realty_photos',
    'rest_framework',
    'staticfiles',
    'sessions',
    # definitely Realty Ads
    'realty',
    'realty_displays',
]

# Models to exclude within specific applications
exclude_models = {
    'notifications': ['notification'],
    'questions': ['documenttemplate'],
    'users': ['customgroup'],
    'realty_addresses': ['address', 'street'],
    'realty_specificities': [
        'aboutapartment',
        'aboutbuilding',
        'commoncharacteristics',
        'leasepayments',
        'rentalfeatures',
        'salesparameters',
    ],
    # "other_app": ["model1", "model2"],
}

for app_config in django_apps.get_app_configs():
    app_label = app_config.label

    if app_label in exclude_apps:
        print(f'Skipping app {app_label}...')
        continue

    for model in app_config.get_models():
        model_name = model._meta.model_name

        # Check for model exclusions
        if app_label in exclude_models and model_name in exclude_models[app_label]:
            print(f'Skipping model {app_label}.{model_name}...')
            continue

        output_file = (
            f'Z_DATA/db_dump_before_deply_refactor/{app_label}.{model_name}.json'
        )
        print(f'Dumping {app_label}.{model_name} -> {output_file}...')
        call_command(
            'dumpdata', f'{app_label}.{model_name}', indent=4, output=output_file
        )
