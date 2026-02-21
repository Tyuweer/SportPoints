
from parsers.pervenstvoKraya_Parser import PervenstvoKraya_Parser
from parsers.kubokKraya_Parser import KubokKraya_Parser
from parsers.sprinters_Day_Parser import Sprinters_Day_Parser
from parsers.stayerDay_Parser import StayerDay_Parser
from parsers.pervenstvoGoroda_Parser import PervenstvoGoroda_Parser
from parsers.kubokRossii_Parser import KubokRossii_Parser
from parsers.snowfins_Parser import Snowfins_Parser

PARSERS = {
    "Первенство Края": PervenstvoKraya_Parser,
    "Кубок края" : KubokKraya_Parser,
    "День спринтера" : Sprinters_Day_Parser,
    "День стаера" : StayerDay_Parser,
    "Первенство города" : PervenstvoGoroda_Parser,
    "Кубок России, Чемпионат России, Первенство России с финалами": KubokRossii_Parser,
    "Снежные ласты": Snowfins_Parser,
    # Добавляй сюда новые парсеры по мере написания:
    # "Кубок Сибири": SiberiaCupParser,
    # "Чемпионат города": CityChampParser,
}

def get_parser_by_name(parser_name: str):
    if parser_name not in PARSERS:
        raise ValueError(f"Неизвестный парсер: {parser_name}")
    return PARSERS[parser_name]()