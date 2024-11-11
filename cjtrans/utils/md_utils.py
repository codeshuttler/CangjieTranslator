import re
def extract_code_block(markdown_string: str):
    pattern = r"```[a-zA-Z]*\n([\s\S]*?)\n```"  # Match ```code``` code block
    match = re.search(pattern, markdown_string)
    if match:
        code_block = match.group(1)
        return code_block.strip()
    else:
        return None

def contains_chinese(text: str) -> bool:
    pattern = re.compile(r'[\u4e00-\u9fff]')  # Unicode range for Chinese characters
    return bool(pattern.search(text))
