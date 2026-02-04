
from parsers.pervenstvoKraya_Parser import PervenstvoKraya_Parser
from parsers.kubokKraya_Parser import KubokKraya_Parser

PARSERS = {
    "Первенство Края": PervenstvoKraya_Parser,
    "Кубок края" : KubokKraya_Parser,
    # Добавляй сюда новые парсеры по мере написания:
    # "Кубок Сибири": SiberiaCupParser,
    # "Чемпионат города": CityChampParser,
}

def get_parser_by_name(parser_name: str):
    if parser_name not in PARSERS:
        raise ValueError(f"Неизвестный парсер: {parser_name}")
    return PARSERS[parser_name]()