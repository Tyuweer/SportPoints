import re

def parse_time_to_seconds(time_str: str) -> float | None:
    if not time_str:
        return None
    s = time_str.replace(":", ".").replace(",", ".")
    try:
        if re.fullmatch(r'\d+\.\d{2}', s):
            return float(s)
        elif len(s.split(".")) == 3:  # 3.31.25
            m, sec, cent = map(int, s.split("."))
            return m * 60 + sec + cent / 100
        elif ":" in time_str:
            parts = time_str.replace(",", ".").split(":")
            mins = int(parts[0])
            rest = float(parts[1])
            return mins * 60 + rest
        else:
            return float(s)
    except:
        return None

def get_best_time(result, final_result):
    """Возвращает лучшее (минимальное) время из двух"""
    sec1 = parse_time_to_seconds(result)
    sec2 = parse_time_to_seconds(final_result)
    
    if sec1 is None and sec2 is None:
        return None
    if sec1 is None:
        return final_result
    if sec2 is None:
        return result
    
    return result if sec1 <= sec2 else final_result

def format_time(seconds: float) -> str:
    """Преобразует секунды в формат MM:SS,cc"""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02}:{secs:05.2f}".replace(".", ",")

def get_points_by_place(place: int) -> int:
    points = [50, 46, 42, 39, 36, 33, 30, 27, 24, 22, 20, 18, 16, 14, 12, 10, 8, 7, 6, 5, 4, 3, 2, 1]
    if 1 <= place <= 24:
        return points[place - 1]
    else:
        return 1  # Все места после 24 — по 1 очку

def normalize_event_name(title: str) -> str:
    title = title.lower()
    if "ныряние" in title:
        base = "ныряние"
    elif "классическ" in title:
        base = "плавание_классические_ласты"
    elif "подводное" in title:
        base = "подводное_плавание"
    elif "плавание" in title or "ластах" in title:
        base = "плавание_ласты"
    else:
        base = "other"
    dist_match = re.search(r'(\d+)\s*(?:м|метров)', title)
    distance = dist_match.group(1) if dist_match else "0"

    # Определяем пол
    if any(x in title for x in ["женщины", "девушки", "юниорки"]):
        gender = "female"
    elif any(x in title for x in ["мужчины", "юниоры", "юноши"]):
        gender = "male"
    else:
        gender = "male"  # По умолчанию мужчины

    return f"{base}_{distance}м_{gender}"

def is_event_header(line):
        """Определяет заголовок дисциплины."""
        line_lower = line.lower()
        document_headers = [
        'всероссийские соревнования',
        'группы спортивных дисциплин',
        'снежные ласты',
        'первенство россии',
        'кубок россии',
        'чемпионат россии'
    ]
        if any(header in line_lower for header in document_headers):
            return False
        
        # Ищем строки, содержащие тип дистанции и возрастную категорию
        keywords = ['плавание', 'ныряние', 'подводное', 'классическ', 'ласт']
        age_groups = ['юниоры', 'юниорки', 'юноши', 'девушки', 'мужчины', 'женщины', 'мальчики', 'девочки']

        has_keyword = any(k in line_lower for k in keywords)
        has_age = any(ag in line_lower for ag in age_groups)

        distances = ['50', '100', '200', '400', '800', '1500', '4х50', '4х100', '4х200']
        has_distance = any(d in line_lower for d in distances)

        return has_keyword and has_age and (has_distance or 'эстафета' in line_lower)
    
def is_athlete_row(parts):
        NON_ATHLETE_KEYWORDS = [
    'протокол', 'технических', 'результатов', 'место', 'разряд',
    'фамилия', 'имя', 'год', 'рожд', 'команда', 'результат',
    'норматив', 'очки', 'предв', 'финал', 'главный', 'судья',
    'секретарь', 'соревнований', 'федерация', 'министерство',
    'первенство', 'чемпионат', 'соревнования', 'протокол',
    'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
    'августа', 'сентября', 'октября', 'ноября', 'декабря',
    'января', 'дистанция', 'дисциплина', 'день'
]
        """Проверяет, является ли строка данными спортсмена"""
        if not parts:
            return False
        
        # Объединяем первые несколько частей для проверки
        text_check = ' '.join(parts[:min(5, len(parts))]).lower()
        
        # Проверка на наличие ключевых слов не-спортсмена
        for keyword in NON_ATHLETE_KEYWORDS:
            if keyword in text_check:
                return False
        
        # Проверка на дату в формате "26 февраля-01 марта 2025 г."
        date_pattern = r'\d{1,2}\s*(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)'
        import re
        if re.search(date_pattern, text_check, re.IGNORECASE):
            return False
        
        return True
    