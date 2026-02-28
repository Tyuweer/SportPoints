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
    """Главная функция нормализации."""
    # 1. Очистка от мусора
    clean_title = clean_raw_text(title)
    
    # 2. Извлечение компонентов
    sport = normalize_sport_type(clean_title)
    distance = normalize_distance(clean_title)
    category = normalize_category(clean_title)
    
    # 3. Сборка итоговой строки
    # Формат: Вид спорта - Дистанция Категория
    return f"{sport} - {distance} {category}"

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
        keywords = ['плавание', 'ныряние', 'подводное', 'классическ', 'ласт',]
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
    'января', 'дистанция', 'дисциплина', 'день', 'переныр', '15м',
    'медотвод', 'отвод', 'н/я', 'ф/с', 'н/кас повор', 'касание'

]
        if not parts:
            return False
        
        # Объединяем первые несколько частей для проверки
        text_check_start = ' '.join(parts[:min(5, len(parts))]).lower()
        # Объединяем последние несколько частей для проверки
        text_check_end = ' '.join(parts[-5:]).lower()

        
        # Проверка на наличие ключевых слов не-спортсмена
        for keyword in NON_ATHLETE_KEYWORDS:
            if keyword in text_check_start or keyword in text_check_end:
                return False
        
        # Проверка на дату в формате "26 февраля-01 марта 2025 г."
        date_pattern = r'\d{1,2}\s*(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)'
        import re
        if re.search(date_pattern, text_check_start, re.IGNORECASE):
            return False
                
        return True

def normalize_line(line):
            # 1. Добавляем пробелы между временем и разрядом: "59,03III" -> "59,03 III"
            line = re.sub(r'(\d{1,2}[,.:]\d{2}(?:[,.:]\d{2})?)([IКМСб\\/юн])', r'\1 \2', line)
            
            # 2. Добавляем пробелы между разрядом и "юн": "IIIюн" -> "III юн"
            line = re.sub(r'([I]{1,3}|[1-3])(юн)', r'\1 \2', line)
            
            # 3. Обрабатываем сложные случаи: "59,03IIIюн" -> "59,03 III юн"
            line = re.sub(r'(\d{1,2}[,.:]\d{2}(?:[,.:]\d{2})?)([I]{1,3}|[1-3])(юн)', r'\1 \2 \3', line)
            return line

def get_best_time(*results):
    valid_pairs = []
    for r in results:
        if r is None:
            continue
        sec = parse_time_to_seconds(r)
        if sec is not None:
            valid_pairs.append((sec, r))
    
    if not valid_pairs:
        return None
    
    # Находим минимальное по секундам и возвращаем исходную строку
    best_sec, best_str = valid_pairs[0]
    for sec, s in valid_pairs[1:]:
        if sec < best_sec:
            best_sec = sec
            best_str = s
    return best_str


def clean_raw_text(text: str) -> str:
    """Удаляет коды дисциплин, лишние пробелы и знаки препинания."""
    # Удаляем всё в скобках (коды дисциплин)
    text = re.sub(r'\([^)]*\)', '', text)
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    # Убираем точки в конце, если есть
    text = text.rstrip('.')
    return text

def normalize_sport_type(title: str) -> str:
    """Определяет и нормализует название вида спорта."""
    title_lower = title.lower()
    
    if "ныряние" in title_lower:
        return "Ныряние"
    elif "классическ" in title_lower:
        return "Плавание в классических ластах"
    elif "подводное" in title_lower:
        return "Подводное плавание"
    elif "плавание" in title_lower and "ласт" in title_lower:
        return "Плавание в ластах"
    elif "плавание" in title_lower:
        # Если просто плавание без упоминания ласт, но в контексте подводного спорта
        return "Плавание в ластах" 
    else:
        return "Дисциплина"
    
def normalize_category(title: str) -> str:
    """ Приводит 6 возрастных категорий к единому стандарту."""
    title_lower = title.lower()
    
    # Женские категории
    if "юниорк" in title_lower: # юниорки
        return "Женщины"
    if "девуш" in title_lower or "девоч" in title_lower: # девушки, девочки
        return "Женщины"
    if "Женщины" in title_lower or "жен " in title_lower or title_lower.endswith("жен"):
        return "Женщины"
        
    # Мужские категории
    if "юниор" in title_lower: # юниоры (проверяем после юниорок)
        return "Мужчины"
    if "юнош" in title_lower or "мальчик" in title_lower: # , мальчики
        return "Мужчины"
    if "мужчин" in title_lower or "муж " in title_lower or title_lower.endswith("муж"):
        return "Мужчины"
    
    return "Женщины" # Если категория не найдена

def normalize_distance(title: str) -> str:
    """Нормализует дистанцию (100м, 100 метров, 4х100)."""
    # Ищем эстафеты 4х100
    relay_match = re.search(r'4\s*[хx]\s*(\d+)', title)
    if relay_match:
        return f"4х{relay_match.group(1)} м"
    
    # Ищем обычные дистанции 50, 100, 200...
    dist_match = re.search(r'(\d+)\s*(?:м|метров|м\.)', title)
    if dist_match:
        return f"{dist_match.group(1)} м"
        
    return "0 м"

def is_relay_event(event_name: str) -> bool:
    """
    Проверяет, является ли дисциплина эстафетой.
    """
    if not event_name:
        return False
    
    event_lower = event_name.lower()
    
    # Признаки эстафеты
    relay_indicators = [
        'эстафет',
        '4x',           # 4x100
        '4х',           # 4х100 (кириллическая x)
        '4 x',          # 4 x 100
        '4 х',          # 4 х 100
    ]
    
    return any(indicator in event_lower for indicator in relay_indicators)

# def get_relay_leg_distance(event_name: str) -> int | None:
#     """
#     Извлекает дистанцию одного этапа эстафеты.
#     Например: "4x100" -> 100
#     """
#     if not event_name:
#         return None
    
#     # Ищем паттерн 4x100 или 4х100
#     match = re.search(r'4\s*[xх]\s*(\d+)', event_name)
#     if match:
#         return int(match.group(1))
    
#     return None