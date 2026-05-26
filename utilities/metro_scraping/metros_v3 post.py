import json
import os
import re
import time

import requests  # Добавляем requests
from dotenv import load_dotenv

# --- НАЧАЛО ПЕРВОЙ ЧАСТИ ПРОГРАММЫ: СБОР ДАННЫХ С API ---

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен из переменных окружения
DADATA_API_TOKEN = os.getenv('DADATA_API_KEY')  # Переименовал для ясности

if not DADATA_API_TOKEN:
    print('Ошибка: Токен DADATA_API_KEY не найден в .env файле.')
    exit()

# Русский алфавит
russian_alphabet = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
DADATA_SUGGEST_LIMIT = (
    20  # Максимальное количество подсказок для бесплатного тарифа Dadata
)
DADATA_SUGGEST_URL = 'http://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/metro'

all_moscow_stations_raw_list = []
processed_query_prefixes = set()  # Для отслеживания уже обработанных префиксов

print('Начинаю сбор станций метро Москвы с использованием прямых POST-запросов...')


def fetch_stations_recursive(query_prefix, current_depth=0, max_depth=1):
    """
    Рекурсивно собирает станции метро через POST-запросы.
    Если на запрос приходит DADATA_SUGGEST_LIMIT результатов,
    пытается уточнить запрос, добавляя следующую букву алфавита.
    """
    global all_moscow_stations_raw_list
    global processed_query_prefixes
    global DADATA_API_TOKEN  # Доступ к токену

    if query_prefix in processed_query_prefixes:
        return

    print(f"Запрос станций с префиксом: '{query_prefix}' (глубина: {current_depth})")
    processed_query_prefixes.add(query_prefix)

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Token {DADATA_API_TOKEN}',
        'Content-Type': 'application/json',
    }
    payload = {
        'query': query_prefix,
        'count': DADATA_SUGGEST_LIMIT,
        # Используем 'filters' согласно вашему примеру.
        # DaData также поддерживает 'locations': [{'city': 'Москва'}] для этого.
        'filters': [{'city': 'Москва'}],
        # Если хотите использовать более стандартный для dadata-api способ:
        # "locations": [{"city": "Москва"}]
    }

    try:
        response = requests.post(
            DADATA_SUGGEST_URL, headers=headers, json=payload, timeout=10
        )
        response.raise_for_status()  # Вызовет исключение для HTTP-ошибок 4xx/5xx

        result_json = response.json()
        suggestions = result_json.get('suggestions', [])

        moscow_stations_in_this_batch = []
        if suggestions:
            for station_suggestion in suggestions:
                # DaData должна уже отфильтровать по городу на своей стороне,
                # но дополнительная проверка не помешает, если вдруг фильтр в payload не сработает как ожидается
                if station_suggestion.get('data', {}).get('city') == 'Москва':
                    moscow_stations_in_this_batch.append(station_suggestion)
                # Если в payload используется "locations", то этот if можно сделать менее строгим
                # или даже убрать, полагаясь на фильтрацию API.
                # Но с "filters" лучше оставить проверку.

            all_moscow_stations_raw_list.extend(moscow_stations_in_this_batch)
            actual_moscow_count = len(moscow_stations_in_this_batch)
            print(
                f"  Получено {actual_moscow_count} московских станций для префикса '{query_prefix}'."
            )

            if (
                actual_moscow_count == DADATA_SUGGEST_LIMIT
                and current_depth < max_depth
            ):
                print(f"  Достигнут лимит для '{query_prefix}'. Углубляемся...")
                for next_letter in russian_alphabet:
                    time.sleep(0.3)
                    fetch_stations_recursive(
                        query_prefix + next_letter, current_depth + 1, max_depth
                    )
            elif actual_moscow_count < DADATA_SUGGEST_LIMIT:
                print(
                    f"  Для префикса '{query_prefix}' получено {actual_moscow_count} станций (меньше лимита), углубление не требуется."
                )
            elif current_depth >= max_depth:
                print(
                    f"  Достигнута максимальная глубина рекурсии для префикса '{query_prefix}'."
                )
        else:
            print(
                f"  Станций на префикс '{query_prefix}' не найдено (ответ API пуст или нет поля 'suggestions')."
            )

    except requests.exceptions.HTTPError as http_err:
        print(
            f"  HTTP ошибка при запросе для префикса '{query_prefix}': {http_err} - {response.text}"
        )
    except requests.exceptions.ConnectionError as conn_err:
        print(
            f"  Ошибка соединения при запросе для префикса '{query_prefix}': {conn_err}"
        )
    except requests.exceptions.Timeout as timeout_err:
        print(f"  Таймаут при запросе для префикса '{query_prefix}': {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"  Ошибка запроса для префикса '{query_prefix}': {req_err}")
    except json.JSONDecodeError:
        print(
            f"  Ошибка декодирования JSON ответа для префикса '{query_prefix}'. Ответ: {response.text if 'response' in locals() else 'N/A'}"
        )
    except Exception as e:
        print(f"  Непредвиденная ошибка при запросе для префикса '{query_prefix}': {e}")

    time.sleep(1)


# Основной цикл сбора данных
for letter in russian_alphabet:
    fetch_stations_recursive(letter, current_depth=0, max_depth=1)

print(
    f'\nВсего собрано {len(all_moscow_stations_raw_list)} сырых записей (включая возможные дубликаты).'
)

# Сохранение "сырых" данных в JSON файл
raw_output_filename = 'all_moscow_stations_raw.json'
try:
    with open(raw_output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_moscow_stations_raw_list, f, ensure_ascii=False, indent=2)
    print(f'Сырые данные успешно сохранены в файл: {raw_output_filename}')
except OSError as e:
    print(f"Ошибка при сохранении сырых данных в '{raw_output_filename}': {e}")

print('--- КОНЕЦ ПЕРВОЙ ЧАСТИ ПРОГРАММЫ: СБОР ДАННЫХ ЗАВЕРШЕН ---')

# --- НАЧАЛО ВТОРОЙ ЧАСТИ ПРОГРАММЫ: ОБРАБОТКА ДАННЫХ С ДИСКА И НОРМАЛИЗАЦИЯ ---
print('\n--- НАЧАЛО ВТОРОЙ ЧАСТИ ПРОГРАММЫ: ОБРАБОТКА ДАННЫХ С ДИСКА ---')

# Загрузка "сырых" данных из файла
loaded_raw_stations_from_file = []
raw_input_filename = 'all_moscow_stations_raw.json'
try:
    with open(raw_input_filename, encoding='utf-8') as f:
        loaded_raw_stations_from_file = json.load(f)
    print(f'Сырые данные успешно загружены из файла: {raw_input_filename}')
    print(
        f'Загружено {len(loaded_raw_stations_from_file)} сырых записей для обработки.'
    )
except FileNotFoundError:
    print(
        f"Ошибка: Файл с сырыми данными '{raw_input_filename}' не найден. "
        'Убедитесь, что первая часть скрипта успешно отработала.'
    )
    exit()
except json.JSONDecodeError:
    print(
        f"Ошибка: Не удалось декодировать JSON из файла '{raw_input_filename}'. Файл может быть поврежден."
    )
    exit()
except OSError as e:
    print(f"Ошибка при чтении файла '{raw_input_filename}': {e}")
    exit()

if not loaded_raw_stations_from_file:
    print(
        'Файл с сырыми данными пуст или не удалось загрузить данные. Обработка прекращена.'
    )
    exit()

# Удаление ПОЛНЫХ дубликатов из загруженных данных
unique_stations_list = []
seen_station_signatures = set()

print('\nНачинаю удаление дубликатов...')
for station_entry in loaded_raw_stations_from_file:
    station_for_signature_creation = station_entry.copy()
    if 'data' in station_for_signature_creation and isinstance(
        station_for_signature_creation['data'], dict
    ):
        data_copy = station_for_signature_creation['data'].copy()
        data_copy.pop('city_kladr_id', None)
        data_copy.pop('city_fias_id', None)
        # Можно добавить другие поля, которые могут меняться, но не влияют на уникальность станции
        # data_copy.pop('qc', None) # Код качества подсказки
        # data_copy.pop('source', None) # Источник данных
        # data_copy.pop('unparsed_parts', None) # Неразобранные части запроса
        station_for_signature_creation['data'] = data_copy

    station_signature = json.dumps(
        station_for_signature_creation, sort_keys=True, ensure_ascii=False
    )

    if station_signature not in seen_station_signatures:
        seen_station_signatures.add(station_signature)
        unique_stations_list.append(
            station_for_signature_creation
        )  # Добавляем уже "очищенную" версию

print(
    f'После удаления дубликатов осталось {len(unique_stations_list)} уникальных станций.'
)

# Формирование итогового JSON с уникальными станциями
output_data_unique_stations = {'moscow_metro_stations': unique_stations_list}
unique_stations_output_filename = 'moscow_metro_stations_unique.json'
try:
    with open(unique_stations_output_filename, 'w', encoding='utf-8') as f:
        json.dump(output_data_unique_stations, f, ensure_ascii=False, indent=2)
    print(
        f'Уникальные данные станций успешно сохранены в файл: {unique_stations_output_filename}'
    )
except OSError as e:
    print(f"Ошибка при сохранении файла '{unique_stations_output_filename}': {e}")


def generate_normalized_db_files(stations_input_list):
    """
    Создает lines.json и stations.json для базы данных
    из списка уникальных данных о станциях.
    """
    print(
        '\nНачинаю создание нормализованных JSON файлов (lines.json, stations.json)...'
    )

    if not stations_input_list:
        print('Список станций пуст. Нормализованные файлы не будут созданы.')
        return

    unique_lines_info = {}
    for station_entry in stations_input_list:
        station_data = station_entry.get('data', {})
        original_line_id = station_data.get('line_id')

        if original_line_id is None:
            print(
                f"Предупреждение: Станция '{station_entry.get('value')}' (unrestricted_value: '{station_entry.get('unrestricted_value')}') не имеет 'line_id'."
            )
            continue

        if original_line_id not in unique_lines_info:
            unique_lines_info[original_line_id] = {
                'line_id': original_line_id,
                'line_name': station_data.get('line_name'),
                'city': station_data.get('city'),
                'color': station_data.get('color'),
            }

    def line_id_sort_key(line_dict_entry):
        line_id_str = line_dict_entry.get('line_id', '')
        match_num_alpha = re.match(r'(\d+)([А-Яа-яЁёA-Za-z]*)', line_id_str)
        if match_num_alpha and match_num_alpha.group(0) == line_id_str:
            num_part = int(match_num_alpha.group(1))
            alpha_part = match_num_alpha.group(2).upper()
            return (0, num_part, alpha_part)
        match_d_num = re.match(r'D(\d+)', line_id_str, re.IGNORECASE)
        if match_d_num and match_d_num.group(0) == line_id_str:
            num_part = int(match_d_num.group(1))
            return (1, num_part)
        return (2, line_id_str.lower())

    sorted_lines = sorted(unique_lines_info.values(), key=line_id_sort_key)

    lines_for_json_db = []
    line_original_id_to_new_pk_map = {}
    for i, line_item in enumerate(sorted_lines):
        new_line_pk = i + 1
        lines_for_json_db.append(
            {
                'id': new_line_pk,
                'line_id': line_item['line_id'],
                'line_name': line_item['line_name'],
                'city': line_item['city'],
                'color': line_item['color'],
            }
        )
        line_original_id_to_new_pk_map[line_item['line_id']] = new_line_pk

    lines_output_filename = 'lines.json'
    try:
        with open(lines_output_filename, 'w', encoding='utf-8') as f:
            json.dump(lines_for_json_db, f, ensure_ascii=False, indent=2)
        print(f'Данные о ветках для БД сохранены в: {lines_output_filename}')
    except OSError as e:
        print(f'Ошибка сохранения {lines_output_filename}: {e}')

    alphabetically_sorted_stations = sorted(
        stations_input_list, key=lambda s: s.get('value', '').lower()
    )

    stations_for_json_db = []
    for i, station_entry in enumerate(alphabetically_sorted_stations):
        new_station_pk = i + 1
        station_data = station_entry.get('data', {})
        original_station_line_id = station_data.get('line_id')
        line_fk = None
        if original_station_line_id is not None:
            line_fk = line_original_id_to_new_pk_map.get(original_station_line_id)

        if line_fk is None and original_station_line_id is not None:
            print(
                f"Предупреждение: Не найден PK для line_id '{original_station_line_id}' "
                f'(станция: {station_entry.get("value")}). Станция будет без FK на линию.'
            )

        stations_for_json_db.append(
            {
                'id': new_station_pk,
                'line': line_fk,
                'name': station_data.get('name'),
                'name_full': station_entry.get('unrestricted_value'),
                'geo_lat': station_data.get('geo_lat'),
                'geo_lon': station_data.get('geo_lon'),
                'is_closed': station_data.get('is_closed', False),
            }
        )

    stations_output_filename = 'stations.json'
    try:
        with open(stations_output_filename, 'w', encoding='utf-8') as f:
            json.dump(stations_for_json_db, f, ensure_ascii=False, indent=2)
        print(f'Данные о станциях для БД сохранены в: {stations_output_filename}')
    except OSError as e:
        print(f'Ошибка сохранения {stations_output_filename}: {e}')


if (
    'unique_stations_list' in locals()
    and isinstance(unique_stations_list, list)
    and unique_stations_list
):
    generate_normalized_db_files(unique_stations_list)
else:
    print(
        "\nПеременная 'unique_stations_list' не найдена, пуста или не является списком. "
        'Создание lines.json и stations.json пропущено.'
    )

print('\n--- РАБОТА СКРИПТА ЗАВЕРШЕНА ---')
