from core.utils import parse_time_to_seconds, get_points_by_place, normalize_event_name

def load_target_events(target_json_data):
    events = {}
    for event in target_json_data:
        gender = "female" if any(x in event["event_name"].lower() for x in ["женщины", "девушки", "юниорки"]) else "male"
        key = normalize_event_name(event["event_name"])
        full_key = f"{key}_{gender}"

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
            gender = "female" if any(x in event["event_name"].lower() for x in ["женщины", "девушки", "юниорки"]) else "male"
            key = normalize_event_name(event["event_name"])
            full_key = f"{key}_{gender}"

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