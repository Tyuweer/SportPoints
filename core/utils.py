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
    return f"{base}_{distance}м"