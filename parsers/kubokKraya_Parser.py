import pdfplumber
import re
from core.utils import is_athlete_row
from core.utils import is_event_header
from core.utils import normalize_line
from core.utils import normalize_event_name


class KubokKraya_Parser:
    def parse(self, pdf_path, is_manual=True):
        events = []
        current_event = None
        seen_events = set()

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=1, y_tolerance=1)
                if not text:
                    continue
                lines = text.split('\n')

                for line in lines:
                    line = line.strip()
                    
                    if 'в/к' in line.lower() or 'в.к.' in line.lower() or 'вк' in line.lower():
                        continue

                    parts = line.split()
                    if not is_athlete_row(parts):
                        continue

                    # Проверяем, новый ли это заголовок дисциплины
                    if is_event_header(line):
                        line_ = normalize_event_name(line)
                        if line_ in seen_events:
                            continue
                        if current_event:
                            events.append(current_event)
                        current_event = {
                            "event_name": line_,
                            "results": []
                        }
                        seen_events.add(line_)
                        continue

                    # Парсим строку результата
                    if current_event and re.match(r'^\d+', line):
                        record = self.parse_result_line_krais(line, is_manual=is_manual)
                        if record:
                            current_event["results"].append(record)

            if current_event:
                events.append(current_event)

        return events

    def parse_result_line_krais(self, line, is_manual=True):
        line = normalize_line(line)
        parts = line.split()

        if not parts:
                return None

        try:
            place = None
            idx = 0
            if parts[0].isdigit():
                place = parts[0]
                idx = 1

            # Разряд
            rank = None
            # Сначала проверяем возможные комбинации с "юн"
            if idx + 1 < len(parts):
                # Проверяем комбинацию "римская цифра + юн"
                if parts[idx] in ['I', 'II', 'III', '1', '2', '3'] and parts[idx + 1] == 'юн':
                    rank = f"{parts[idx]} юн"
                    idx += 2
                else:
                    # Проверяем одиночные разряды
                    if parts[idx] in ['I', 'II', 'III', '1', '2', '3', 'МС', 'КМС', 'ЗМС', 'МСМК', 
                                    'б\\р', 'б/р', 'мс', 'кмс', 'змс', 'мсмк']:
                        rank = parts[idx]
                        idx += 1

            # Имя
            name_parts = []
            birth_date = None
            team_parts = []

            while idx < len(parts):
                part = parts[idx]
                # Проверяем, не содержит ли часть дату рождения внутри
                # Например: "Михайлович30.01.2008"
                date_match = re.search(r'\d{2}\.\d{2}\.(19|20)\d{2}$', part)
                if date_match:
                # Разделяем часть на имя и дату
                    name_part = re.sub(r'\d{2}\.\d{2}\.(19|20)\d{2}$', '', part)
                    if name_part:
                        name_parts.append(name_part)
                    birth_date = date_match.group(0)
                    idx += 1
                        # Дата будет обработана на следующей итерации
                    break

                # Если это год рождения
                if re.fullmatch(r'\d{4}', part):
                    break
                if re.fullmatch(r'\d{2}\.\d{2}\.(19|20)\d{2}', part):
                    birth_date = part
                    break
                
                # Если это результат
                time_pattern = r'\d{1,2}[,.:]\d{2}([,.:]\d{2})?$'
                if (re.match(time_pattern, part) or part in ['DNS', 'DSQ', 'DNF']) and not re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', part):
                    break
                # Если это команда
                if '.' in part and len(part) > 2 or '""' in part and len(part) > 2:  # Например "КСШ г.Ачинск"
                    break
                name_parts.append(part)
                idx += 1

            if not name_parts:
                return None

            full_name = ' '.join(name_parts)

            # Извлекаем год рождения из birth_date
            birth_year = None
            if birth_date:
                if re.fullmatch(r'\d{4}', birth_date):
                    # Это просто год
                    birth_year = birth_date
                elif '.' in birth_date:
                    # Это полная дата ДД.ММ.ГГГГ - берем последнюю часть
                    birth_year = birth_date.split('.')[-1]
            
            # Если birth_date не был найден в цикле, проверяем текущую часть
            if not birth_date and idx < len(parts):
                current_part = parts[idx]
                # Проверяем, не дата ли это
                if re.fullmatch(r'\d{2}\.\d{2}\.(19|20)\d{2}', current_part):
                    birth_date = current_part
                    birth_year = current_part.split('.')[-1]
                    idx += 1
                elif re.fullmatch(r'\d{4}', current_part):
                    birth_date = current_part
                    birth_year = current_part
                    idx += 1

            # Команда — ищем до результата
            team_parts = []
            while idx < len(parts):
                part = parts[idx]
                # Если это результат
                if re.match(r'\d{1,2}[,.:]\d{2}([,.:]\d{2})?$', part) or part in ['DNS', 'DSQ', 'DNF']:
                    break
                team_parts.append(part)
                idx += 1

            team = ' '.join(team_parts)

            # Результат
            result = None
            
            if idx < len(parts):
                token = parts[idx]
                if re.match(r'\d{1,2}[,.:]\d{2}([,.:]\d{2})?$', token):
                    result = token
                    idx += 1

            # Остальное — норматив, очки
            normative = None
            points = None
            rest_parts = parts[idx:]

            i = 0
            while i < len(rest_parts):
                p = rest_parts[i]
                
                if not normative:
                # Проверка на разряд (включая комбинацию с "юн")
                    if p in ['I', 'II', 'III', '1', '2', '3']:
                        # Проверяем, не идет ли дальше "юн"
                        if i + 1 < len(rest_parts) and rest_parts[i + 1] == 'юн':
                            rank_with_jun = f"{p} юн"
                            normative = rank_with_jun
                            i += 2  # Пропускаем и цифру, и "юн"
                            continue
                        else:
                            normative = p
                            i += 1
                            continue
                
                    # Проверка на другие разряды
                    elif p in ['КМС', 'МС', 'б\\р', 'б/р', 'ЗМС', 'МСМК']:
                        if not normative:
                            normative = p
                        i += 1
                        continue
                
                    # Проверка на одиночное "юн" (если вдруг отдельно стоит)
                    elif p == 'юн':
                        normative = 'юн' if not normative else normative + ' юн'
                        i += 1
                        continue
                # Проверка на очки
                if p.isdigit() and int(p) <= 50:
                    points = int(p)
                    i += 1
                    continue
                if p == 'лично' or p == 'Лично' or p == 'ЛИЧНО':
                    points = p
                    i += 1
                    continue
                # Если это не разряд и не очки, то все остальное - норматив
                else:
                    # Собираем оставшиеся части как норматив
                    remaining = ' '.join(rest_parts[i:])
                    normative = remaining if not normative else normative + ' ' + remaining
                    break

            return {
                "place": place,
                "rank": rank,
                "full_name": full_name,
                "birth_year": birth_year,
                "team": team,
                "result": result,
                "normative": normative,
                "points": points,
                "is_manual_timing": is_manual
            }

        except Exception as e:
            print(f"Ошибка парсинга строки: '{line}' — {e}")
            return None


    
    