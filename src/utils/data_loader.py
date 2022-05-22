import logging
from typing import Dict
from pathlib import Path
import gzip


def data_loader(file_path: Path) -> Dict:
    file_path = file_path.resolve()
    if not file_path.exists():
        raise FileNotFoundError(f'{file_path} does not exist.')

    if '.yml' in file_path.suffixes:
        import yaml
        logging.info(f'importing yml-file from {file_path}.')
        with open(file_path, 'r') as yaml_file_path:
            data = yaml.safe_load(yaml_file_path)

    elif '.json' in file_path.suffixes:
        import json
        logging.info(f'importing json-file from {file_path}.')
        with open(file_path, 'r') as json_file_path:
            data = json.load(json_file_path)

    elif '.pickle' in file_path.suffixes:
        import pickle
        if '.gz' in file_path.suffixes:
            logging.info(f'importing compressed pickle-file from {file_path}.')
            data = pickle.load(gzip.open(file_path, "r"))
        else:
            logging.info(f'importing pickle-file from {file_path}.')
            data = pickle.load(open(file_path, "r"))

    else:
        raise ValueError(f'file format {file_path.suffixes} not supported.')

    return data
