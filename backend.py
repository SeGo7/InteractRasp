import re
import requests
import socket

import pandas as pd

from copy import deepcopy
from collections import defaultdict

pattern_day = r'^(Понедельник|Вторник|Среда|Четверг|Пятница|Суббота)$'


def lessons_equal(l1, l2):
    return (
            l1['предмет'].strip() == l2['предмет'].strip() and
            l1['кабинет'].strip() == l2['кабинет'].strip() and
            l1['учитель'].strip() == l2['учитель'].strip()
    )


def group_by_urok(lessons):
    grouped = {}
    for lesson in lessons:
        num = lesson['урок']
        grouped.setdefault(num, []).append(lesson)
    return grouped


def compare_raspisanie(base_rasp, new_rasp):
    result = deepcopy(new_rasp)

    for day, classes in result.items():
        for class_name, lessons in classes.items():
            base_lessons = base_rasp.get(day, {}).get(class_name, [])
            base_by_urok = group_by_urok(base_lessons)
            res_by_urok = group_by_urok(lessons)

            for urok_num in range(1, 8):
                new_entries = res_by_urok.get(urok_num, {})
                base_entries = base_by_urok.get(urok_num, [])

                if len(new_entries) == 0 and len(base_entries) > 0:
                    lessons.append({'урок': urok_num, 'отличается' : True})
                    continue
                elif len(new_entries) > 0 and len(base_entries) == 0:
                    for entry in new_entries.values():
                        entry['отличается'] = True
                    continue

                for entry in new_entries:
                    if not any(lessons_equal(entry, b) for b in base_entries):
                        entry['отличается'] = True
                    else:
                        entry['отличается'] = False

    return result



def get_raspisanie(file_name="day.csv"):
    file_path = 'tmp/' + file_name

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    class_line = lines[1].strip().split(",")

    classes = {}

    # Определяем индексы классов
    class_indices = []
    for idx, name in enumerate(class_line):
        name = name.strip()
        if re.match(r'\d{1,2} [а-я]', name.lower()):
            class_indices.append((name, idx))

    # Добавим последний индекс для корректного расчета диапазонов
    class_indices.append(("END", len(class_line)))

    # Заполняем classes
    for i in range(len(class_indices) - 1):
        name, start_idx = class_indices[i]
        next_idx = class_indices[i + 1][1]
        num_cells = next_idx - start_idx

        if num_cells >= 4:
            # две подгруппы
            classes[name] = [start_idx, start_idx + 2]
        else:
            # одна подгруппа
            classes[name] = [start_idx]

    # Парсинг расписания
    all = {}
    schedule = defaultdict(list)
    i = 3
    lesson_number = 1

    while i < len(lines) - 1:
        subject_line = lines[i].strip().split(",")
        teacher_line = lines[i + 1].strip().split(",")

        if re.match(pattern_day, subject_line[0], re.IGNORECASE):
            all[subject_line[0]] = defaultdict(list)
            schedule = all[subject_line[0]]
            lesson_number = 1

        i += 2

        for class_name, indices in classes.items():
            for group_idx, col in enumerate(indices, start=1):
                try:
                    subject = subject_line[col].strip()
                    teacher = teacher_line[col].strip()
                    # Поиск кабинета:
                    # если следующая ячейка (col+1) не содержит предмета или учителя — вероятно, это кабинет
                    room = ""
                    if col + 1 < len(subject_line) and subject_line[col + 1] != "":
                        room = subject_line[col + 1]
                    elif col + 3 < len(subject_line):
                        room = subject_line[col + 3]

                    if subject:
                        lesson = {
                            "урок": lesson_number,
                            "предмет": subject,
                            "кабинет": str(int(float(room))) if bool(re.fullmatch(r'[-+]?\d+(\.\d+)?', room)) else room,
                            "учитель": teacher
                        }
                        schedule[class_name].append(lesson)

                except IndexError:
                    continue
        lesson_number += 1

    return all


def get_rasp():
    rasp_changes = get_raspisanie(file_name="day.csv")
    rasp_const = get_raspisanie(file_name="all.csv")

    return compare_raspisanie(rasp_const, rasp_changes), rasp_const


def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError:
        return False


def download_and_convert_yandex_xlsx(url_file, xlsx_path, csv_path):
    if not check_internet():
        print("Ошибка: Отсутствует подключение к интернету.")
        return

    try:
        # Шаг 1: Получаем прямую ссылку на файл
        api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
        params = {"public_key": url_file}
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()

        download_url = response.json().get("href")
        if not download_url:
            print("Ошибка: Не удалось получить ссылку для загрузки.")
            return

        # Шаг 2: Скачиваем файл
        with requests.get(download_url, stream=True, timeout=10) as r:
            r.raise_for_status()
            with open(xlsx_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Скачано: {xlsx_path}")

        # Шаг 3: Конвертируем в CSV
        try:
            df = pd.read_excel(xlsx_path)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"Преобразовано в CSV: {csv_path}")
        except Exception as e:
            print(f"Ошибка при чтении/конвертации Excel-файла: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")


def update_data():
    with open("tmp/day_url") as f:
        download_and_convert_yandex_xlsx(
            url_file=f.read(),
            xlsx_path='tmp/' + "day.xlsx",
            csv_path='tmp/' + "day.csv"
        )
    with open("tmp/all_url") as f:
        download_and_convert_yandex_xlsx(
            url_file=f.read(),
            xlsx_path='tmp/' + "all.xlsx",
            csv_path='tmp/' + "all.csv"
        )


if __name__ == "__main__":
    update_data()
