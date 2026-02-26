from core.utils import is_event_header, is_relay_event, normalize_event_name

test_lines = [
    "Плавание в классических ластах - эстафета 4х100 метров Девушки",
    "Плавание в ластах - 100 м Мужчины",
    "Место Разряд Фамилия Имя Г.р. Команда Результат",
    "1) 2 ЖАРКОВ Артём 2014 00:55,26 2"
]

for line in test_lines:
    print(f"\nСтрока: {line}")
    print(f"  is_event_header: {is_event_header(line)}")
    print(f"  is_relay_event: {is_relay_event(line)}")
    print(f"  normalize_event_name: {normalize_event_name(line)}")