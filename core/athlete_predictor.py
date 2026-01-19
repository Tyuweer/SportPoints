from core.utils import parse_time_to_seconds, get_points_by_place, normalize_event_name

def load_target_events(target_json_data):
    events = {}
    for event in target_json_data:
        # Используем новую функцию normalize_event_name
        full_key = normalize_event_name(event["event_name"])

        overall_times = []
        final_times = []
        for r in event["results"]:
            if "is_relay" in r and r["is_relay"]:
                continue
            result_str = r.get("result")
            if result_str:
                sec = parse_time_to_seconds(result_str)
                if sec is not None:
                    overall_times.append(sec)
            final_str = r.get("final")
            if final_str:
                sec = parse_time_to_seconds(final_str)
                if sec is not None:
                    final_times.append(sec)

        events[full_key] = {
            "overall": sorted(overall_times),
            "final": sorted(final_times) if final_times else None,
            "participants": len(overall_times)
        }
    return events

def find_best_results_per_event(athlete_name: str, history_data_list):
    # Разбиваем имя на фамилию и имя
    parts = athlete_name.split()
    if len(parts) >= 2:
        search_surname = parts[0].lower()
        search_name = parts[1].lower()
    else:
        search_surname = athlete_name.lower()
        search_name = ""

    all_results = {}

    for data in history_data_list:
        for event in data:
            # Используем новую функцию normalize_event_name
            full_key = normalize_event_name(event["event_name"])

            for r in event["results"]:
                if "full_name" not in r:
                    continue

                full_name = r["full_name"]
                full_name_lower = full_name.lower()

                if search_surname in full_name_lower and (search_name == "" or search_name in full_name_lower):
                    if "result" not in r or not r["result"]:
                        continue
                    time_sec = parse_time_to_seconds(r["result"])
                    if time_sec is None:
                        continue

                    if r.get("is_manual_timing", False):
                        time_sec += 0.20

                    # Определяем пол спортсмена
                    athlete_gender = detect_gender_by_name(full_name)

                    # Если дисциплина не соответствует полу — пропускаем
                    if "_female" in full_key and athlete_gender != "female":
                        continue
                    if "_male" in full_key and athlete_gender != "male":
                        continue

                    if full_key not in all_results:
                        all_results[full_key] = []
                    all_results[full_key].append({"time": time_sec, "source": r})

    best = {}
    for key, results in all_results.items():
        best_result = min(results, key=lambda x: x["time"])
        best[key] = best_result

    return best

def calculate_predicted_scores(athlete_name: str, target_json_data, history_json_list):
    target_events = load_target_events(target_json_data)
    best_results = find_best_results_per_event(athlete_name, history_json_list)

    results = []
    for key, entry in best_results.items():
        our_time = entry["time"]

        if key in target_events:
            event_data = target_events[key]

            if event_data["final"]:
                overall_place = 1
                for t in event_data["overall"]:
                    if t < our_time:
                        overall_place += 1

                if overall_place <= 8:
                    final_place = 1
                    for t in event_data["final"]:
                        if t < our_time:
                            final_place += 1
                    place = final_place
                else:
                    place = overall_place
            else:
                place = 1
                for t in event_data["overall"]:
                    if t < our_time:
                        place += 1

            points = get_points_by_place(place)
        else:
            place = 0
            points = 0

        results.append({
            "event_key": key,
            "time": our_time,
            "place": place,
            "points": points
        })

    results.sort(key=lambda x: x["points"], reverse=True)
    top3 = results[:3]

    return top3, results

def detect_gender_by_name(full_name: str) -> str:
    # Расширенный список мужских имён
    male_names = [
        "Матвей", "Дмитрий", "Алексей", "Арсений", "Марк", "Тимофей", "Роман", "Максим", "Олег", "Ярослав",
        "Андрей", "Иван", "Александр", "Михаил", "Сергей", "Даниил", "Артем", "Кирилл", "Макс", "Егор",
        "Илья", "Тимур", "Руслан", "Амир", "Артур", "Владислав", "Денис", "Никита", "Антон", "Виктор",
        "Арсен", "Мирон", "Адам", "Мирослав", "Георгий", "Валерий", "Владимир", "Петр", "Федор", "Богдан",
        "Миша", "Степан", "Архип", "Евгений", "Вячеслав", "Борис", "Григорий", "Константин", "Анатолий", "Олег",
        "Павел", "Роман", "Аркадий", "Леонид", "Семен", "Марат", "Айдар", "Ринат", "Азат", "Дамир",
        "Рустам", "Ильнур", "Ильдар", "Фарид", "Марат", "Альберт", "Роберт", "Айрат", "Айрат", "Радик",
        "Равиль", "Рафик", "Рашид", "Родион", "Ростислав", "Руслан", "Савелий", "Семён", "Сергей", "Станислав",
        "Тимур", "Тихон", "Умар", "Фарух", "Феликс", "Филипп", "Харитон", "Эдуард", "Эрик", "Юрий",
        "Ян", "Яромир", "Ярослав", "Алекс", "Арсений", "Бронислав", "Валентин", "Вениамин", "Виктор", "Виталий",
        "Влад", "Геннадий", "Глеб", "Гордей", "Давид", "Данил", "Демьян", "Ефим", "Захар", "Игорь",
        "Клемент", "Кузьма", "Лаврентий", "Лев", "Макар", "Мирослав", "Назар", "Нестор", "Остап", "Платон",
        "Родион", "Ростислав", "Савва", "Святослав", "Севастьян", "Тимофей", "Фёдор", "Фома", "Эраст", "Юлиан",
        "Агафон", "Аким", "Анисим", "Антип", "Афанасий", "Богдан", "Болеслав", "Василий", "Венедикт", "Викентий",
        "Влас", "Гавриил", "Гордей", "Демид", "Добрыня", "Евсей", "Ефим", "Зиновий", "Измаил", "Капитон",
        "Кирей", "Клемент", "Корней", "Ксенофонт", "Лавр", "Мефодий", "Назарий", "Никифор", "Онуфрий", "Пимен",
        "Прокопий", "Савва", "Сила", "Созон", "Тарас", "Устин", "Фока", "Харитон", "Чеслав", "Эльдар", "Юлий"
    ]

    # Расширенный список женских имён
    female_names = [
        "Анастасия", "Мария", "Ольга", "Варвара", "Полина", "Юлия", "Елизавета", "Алина", "Амина", "Злата",
        "Анна", "Екатерина", "Дарья", "Алиса", "Виктория", "София", "Милана", "Ксения", "Вера", "Алёна",
        "Ангелина", "Валерия", "Василиса", "Вероника", "Диана", "Ева", "Зоя", "Ирина", "Кира", "Лада",
        "Лариса", "Лидия", "Любовь", "Майя", "Надежда", "Наталья", "Нина", "Олеся", "Пелагея", "Раиса",
        "Светлана", "Тамара", "Татьяна", "Ульяна", "Фаина", "Эвелина", "Эльвира", "Яна", "Ярослава", "Агния",
        "Агата", "Аглая", "Аграфена", "Анисья", "Антонина", "Анфиса", "Арина", "Ася", "Божена", "Бронислава",
        "Валентина", "Васса", "Вера", "Вероника", "Весна", "Виктория", "Виолетта", "Владислава", "Галина", "Дария",
        "Диана", "Дина", "Евгения", "Екатерина", "Елена", "Елизавета", "Жанна", "Зинаида", "Злата", "Инна",
        "Ирина", "Карина", "Кира", "Клавдия", "Кристина", "Ксения", "Лариса", "Лидия", "Любовь", "Майя",
        "Маргарита", "Марина", "Милана", "Надежда", "Наталья", "Нина", "Оксана", "Ольга", "Пелагея", "Раиса",
        "Светлана", "Софья", "Тамара", "Татьяна", "Ульяна", "Фаина", "Эвелина", "Эльвира", "Яна", "Ярослава",
        "Ада", "Аида", "Айгуль", "Айнур", "Айсылу", "Алсу", "Альбина", "Альфия", "Анель", "Асель",
        "Асия", "Аяулым", "Белла", "Берта", "Валерия", "Ванда", "Василиса", "Вера", "Вероника", "Виктория",
        "Гаянэ", "Генриетта", "Глафира", "Джульетта", "Диана", "Дина", "Доминика", "Евдокия", "Евфросиния", "Екатерина"
    ]

    # Извлекаем имя (предполагаем, что имя идёт после фамилии)
    name_parts = full_name.split()
    if len(name_parts) >= 2:
        first_name = name_parts[1]  # Вторая часть — имя
    elif len(name_parts) == 1:
        first_name = name_parts[0]  # Если только одно слово — возможно имя
    else:
        return "male"  # По умолчанию мужчины

    # Убираем регистр
    first_name_lower = first_name.lower()

    # Проверяем мужские и женские имена
    if any(name.lower() in first_name_lower for name in male_names):
        return "male"
    elif any(name.lower() in first_name_lower for name in female_names):
        return "female"
    else:
        # Если имя не найдено — определяем по окончанию
        if first_name.endswith(('а', 'я', 'ия')) and not any(end in first_name for end in ['Илья', 'Арсений', 'Андрей', 'Георгий', 'Григорий']):
            return "female"
        else:
            return "male"  # По умолчанию мужчины