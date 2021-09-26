from json_configparser import ConfigArgs
from typing import NamedTuple, Dict


class Arguments(NamedTuple):
    stockfish_binary_path: str
    time: int
    log_level: str


def create_args_object(config_path):
    args_object = ConfigArgs(Arguments)
    dict_args = args_object.parse_json(config_path)
    return Arguments(**dict_args)
