from parsers.krasnoyarsk_parser import KrasnoyarskParser
from parsers.russian_parser import RussianParser

def get_parser_by_type(protocol_type: str):
    if protocol_type == "russian":
        return RussianParser(), False
    elif protocol_type == "krasnoyarsk":
        return KrasnoyarskParser(), True
    else:
        raise ValueError(f"Неизвестный тип протокола: {protocol_type}")