import pdfplumber
import re

class RussianParser:
    def parse(self, pdf_path, is_manual=False):
        events = []
        current_event = None

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=1, y_tolerance=1)
                if not text:
                    continue
                lines = text.split('\n')

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Проверяем, новый ли это заголовок дисциплины
                    if self.is_event_header(line):
                        if current_event:
                            events.append(current_event)
                        current_event = {
                            "event_name": line,
                            "results": []
                        }
                        continue

                    # Парсим строку результата
                    if current_event and re.match(r'^\d+[)\s]?', line):
                        record = self.parse_result_line(line, is_manual=is_manual)
                        if record:
                            current_event["results"].append(record)

            if current_event:
                events.append(current_event)

        return events

    def is_event_header(self, line):
        """Определяет заголовок дисциплины."""
        return bool(re.search(r'^(Ныряние|Плавание|Подводное плавание|эстафета).*[Женщины|Мужчины|Смешанная]', line))

    def parse_result_line(self, line, is_manual=False):
        parts = line.split()
        if not parts:
            return None

        try:
            place = parts[0].rstrip(')')
            idx = 1

            # Разряд
            rank = None
            if idx < len(parts) and parts[idx] in ['МС', 'КМС', 'ЗМС', 'МСМК', '1', '2']:
                rank = parts[idx]
                idx += 1

            # Год рождения
            year_idx = None
            for i in range(idx, min(idx + 5, len(parts))):
                if re.fullmatch(r'\d{4}', parts[i]):
                    year_idx = i
                    break

            if year_idx is not None:
                full_name = ' '.join(parts[idx:year_idx])
                year = parts[year_idx]
                idx = year_idx + 1

                # Команда
                team_parts = []
                while idx < len(parts) and not re.match(r'\d{2}:\d{2},\d{2}', parts[idx]) and parts[idx] != 'Фальстарт':
                    team_parts.append(parts[idx])
                    idx += 1
                team = ' '.join(team_parts)

                # Результат и финал
                result = final = rank2 = points = note = None
                if idx < len(parts) and re.match(r'\d{2}:\d{2},\d{2}', parts[idx]):
                    result = parts[idx]
                    idx += 1
                if idx < len(parts) and re.match(r'\d{2}:\d{2},\d{2}', parts[idx]):
                    final = parts[idx]
                    idx += 1
                if idx < len(parts) and parts[idx] in ['МС', 'КМС', 'ЗМС', 'МСМК', '1', '2']:
                    rank2 = parts[idx]
                    idx += 1
                if idx < len(parts) and parts[idx].isdigit():
                    points = int(parts[idx])
                    idx += 1
                note = ' '.join(parts[idx:]) if idx < len(parts) else ''

                return {
                    "place": place,
                    "rank": rank,
                    "full_name": full_name,
                    "birth_year": year,
                    "team": team,
                    "result": result,
                    "final": final,
                    "rank_after": rank2,
                    "points": points,
                    "note": note,
                    "is_manual_timing": False
                }

            else:
                # Эстафета
                team = parts[1] if len(parts) > 1 else ''
                result = parts[2] if len(parts) > 2 and re.match(r'\d{2}:\d{2},\d{2}', parts[2]) else None
                points = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else None
                return {
                    "place": place,
                    "team": team,
                    "result": result,
                    "points": points,
                    "is_relay": True,
                    "is_manual_timing": is_manual
                }

        except Exception as e:
            print(f"Ошибка парсинга строки: '{line}' — {e}")
            return None