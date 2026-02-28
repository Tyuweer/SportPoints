
from parsers.pervenstvoKraya_Parser import PervenstvoKraya_Parser
from parsers.kubokKraya_Parser import KubokKraya_Parser
from parsers.sprinters_Day_Parser import Sprinters_Day_Parser
from parsers.stayerDay_Parser import StayerDay_Parser
from parsers.pervenstvoGoroda_Parser import PervenstvoGoroda_Parser
from parsers.kubokRossii_Parser import KubokRossii_Parser
from parsers.goldfins_Parser import Goldfins_Parser

PARSERS = {
    "Первенство Края": KubokRossii_Parser,
    "Кубок края" : KubokRossii_Parser,
    "День спринтера" : KubokRossii_Parser,
    # "День стаера" : StayerDay_Parser,
    # "Первенство города" : PervenstvoGoroda_Parser,
    "Всероссийские соревнования": KubokRossii_Parser,
    # "Всероссийские соревнования без финалов": Snowfins_Parser,
    "Золотая Ласта": Goldfins_Parser,
    # Добавляй сюда новые парсеры по мере написания:
    "Кубок Сибири": KubokRossii_Parser,
    # "Чемпионат города": CityChampParser,
}

def get_parser_by_name(parser_name: str):
    if parser_name not in PARSERS:
        raise ValueError(f"Неизвестный парсер: {parser_name}")
    return PARSERS[parser_name]()