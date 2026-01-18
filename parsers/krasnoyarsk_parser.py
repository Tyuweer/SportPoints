import pdfplumber
import re

class KrasnoyarskParser:
    def parse(self, pdf_path, is_manual=True):
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
                        record = self.parse_result_line_krasnoyarsk(line, is_manual=is_manual)
                        if record:
                            current_event["results"].append(record)

            if current_event:
                events.append(current_event)

        return events

    def is_event_header(self, line):
        """Определяет заголовок дисциплины."""
        return bool(re.search(r'Плавание|Ныряние|Подводное плавание|эстафета', line)) and any(x in line for x in ['женщины', 'мужчины', 'юниор', 'девушки', 'юноши'])

    def parse_result_line_krasnoyarsk(self, line, is_manual=True):
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
            if idx < len(parts) and parts[idx] in ['МС', 'КМС', 'ЗМС', 'МСМК', 'I', 'II', 'III', 'б\\р', 'юн']:
                rank = parts[idx]
                idx += 1

            # Дата рождения
            birth_date = None
            date_idx = None
            for i in range(idx, min(idx + 5, len(parts))):
                if re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', parts[i]):
                    birth_date = parts[i]
                    date_idx = i
                    break

            if date_idx is not None:
                full_name = ' '.join(parts[idx:date_idx])
                idx = date_idx + 1

                # Команда
                team_parts = []
                while idx < len(parts) and not re.match(r'\d{1,2}:\d{2},\d{2}|\d{1,2},\d{2}|DNS|DSQ|DNF|в/к|б/р', parts[idx]):
                    team_parts.append(parts[idx])
                    idx += 1
                team = ' '.join(team_parts)

                # Результат
                result = status = None
                if idx < len(parts):
                    token = parts[idx]
                    if token in ['DNS', 'DSQ', 'DNF']:
                        status = token
                    elif re.match(r'\d{1,2},\d{2}', token):  # 44,20
                        result = token
                    elif re.match(r'\d{1,2}:\d{2},\d{2}', token):  # 00:44,20
                        result = token
                    idx += 1

                # Норматив
                normative = None
                if idx < len(parts):
                    rest = ' '.join(parts[idx:])
                    if any(x in rest for x in ['I', 'II', 'III', 'в/к', 'б/р', 'юн']):
                        normative = rest

                return {
                    "place": place,
                    "rank": rank,
                    "full_name": full_name,
                    "birth_date": birth_date,
                    "team": team,
                    "result": result,
                    "status": status,
                    "normative": normative,
                    "is_manual_timing": True
                }

            else:
                # Строка без даты — например, только DNS
                return None

        except Exception as e:
            print(f"Ошибка парсинга строки: '{line}' — {e}")
            return None