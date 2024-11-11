import json
from typing import List, Dict

def read_jsonl(file_path: str) -> List[Dict]:
    """
    Read a JSON Lines file and return a list of dictionaries.

    Args:
        file_path (str): The path to the JSON Lines file.

    Returns:
        List[Dict]: A list of dictionaries containing the data from the JSON Lines file.
    """
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            data.append(json.loads(line))
    return data

def write_jsonl(data: List[Dict], file_path: str) -> None:
    """
    Write a list of dictionaries to a JSON Lines file.

    Args:
        data (List[Dict]): The list of dictionaries to be written to the file.
        file_path (str): The path to the output JSON Lines file.
    """
    with open(file_path, 'w') as file:
        for item in data:
            file.write(json.dumps(item, ensure_ascii=False) + '\n')

def filter_jsonl(file_path: str, key: str, value: str) -> List[Dict]:
    """
    Filter a JSON Lines file based on a key-value pair and return filtered data.

    Args:
        file_path (str): The path to the JSON Lines file.
        key (str): The key to filter on.
        value (str): The value to filter on.

    Returns:
        List[Dict]: A list of dictionaries containing the filtered data.
    """
    filtered_data = []
    with open(file_path, 'r') as file:
        for line in file:
            json_obj = json.loads(line)
            if key in json_obj and json_obj[key] == value:
                filtered_data.append(json_obj)
    return filtered_data
