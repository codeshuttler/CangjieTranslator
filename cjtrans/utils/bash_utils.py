import re

def remove_color_codes(text: str) -> str:
    color_pattern = r'\x1b\[[0-9;]*m'
    return re.sub(color_pattern, '', text)
