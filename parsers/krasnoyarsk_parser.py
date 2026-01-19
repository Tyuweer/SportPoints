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

                    if self.is_event_header(line):
                        if current_event:
                            events.append(current_event)
                        current_event = {
                            "event_name": line,
                            "results": []
                        }
                        continue

                    if current_event and re.match(r'^\d+[)\s]?', line):
                        record = self.parse_result_line_krasnoyarsk(line, is_manual=is_manual)
                        if record:
                            current_event["results"].append(record)

            if current_event:
                events.append(current_event)

        return events

    def is_event_header(self, line):
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

            rank = None
            if idx < len(parts) and parts[idx] in ['МС', 'КМС', 'ЗМС', 'МСМК', 'I', 'II', 'III', 'б\\р', 'юн']:
                rank = parts[idx]
                idx += 1

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

                # Собираем токены до результата
                team_parts = []
                result = None
                
                for i in range(idx, len(parts)):
                    token = parts[i]
                    
                    # Результат: 44,53 или 1.45,68 или 01:44,53
                    if re.match(r'\d{1,2}[,.]\d{2}$', token) or \
                       re.match(r'\d+\.\d{2},\d{2}$', token) or \
                       re.match(r'\d{1,2}:\d{2},\d{2}$', token) or \
                       token in ['DNS', 'DSQ', 'DNF']:
                        result = token
                        idx = i + 1
                        break
                    else:
                        team_parts.append(token)

                team = ' '.join(team_parts)

                # Остальное — норматив
                normative = ' '.join(parts[idx:]) if idx < len(parts) else None

                return {
                    "place": place,
                    "rank": rank,
                    "full_name": full_name,
                    "birth_date": birth_date,
                    "team": team,
                    "result": result,
                    "status": result if result in ['DNS', 'DSQ', 'DNF'] else None,
                    "normative": normative,
                    "is_manual_timing": True
                }

            else:
                return None

        except Exception as e:
            print(f"Ошибка парсинга строки: '{line}' — {e}")
            return None