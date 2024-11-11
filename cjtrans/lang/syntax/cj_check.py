
import re
import subprocess
from typing import List, Tuple
import os

from cjtrans.utils.hash_utils import calculate_md5
from cjtrans.utils.file_utils import write_to_file
def check_cj_from_file(cj_path: str, frontend_path: str="./tpfrontend") -> str:
    try:
        output = subprocess.check_output(f"{frontend_path} {cj_path}", shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        output = e.output
    
    if "[Rebuilt Program]" in output:
        end_pos = output.index("[Rebuilt Program]")
        output = output[:end_pos]
    return output

import tree_sitter_cangjie as tscangjie
from tree_sitter import Language, Parser, Node
from cjtrans.utils.tree_sitter_utils import has_error

def check_cj(cj_code: str, use_tree_sitter: bool = True, temp_path: str = "./temp_dir") -> str:
    if use_tree_sitter:
        CJ_LANGUAGE = Language(tscangjie.language())
        parser = Parser(CJ_LANGUAGE)
        tree = parser.parse(cj_code.encode(), encoding="utf8")
        return has_error(tree.root_node)
    else:
        os.makedirs(temp_path, exist_ok=True)
        file_id = calculate_md5(cj_code)
        code_path = os.path.join(temp_path, f"{file_id}.cj")
        write_to_file(code_path, cj_code)
        output = check_cj_from_file(code_path)
        return "error" in output

def parse_error_messages(text: str) -> List[str]:
    errors = []
    current_error = None
    for line in text.splitlines():
        if line.startswith("error:") or line.startswith("note:") or line.startswith("warning:"):
            if current_error is not None:
                errors.append(current_error)
            current_error = ""
            current_error += line + "\n"
        else:
            if current_error is not None:
                current_error += line + "\n"
    if current_error is not None:
        errors.append(current_error)
    return errors

def parse_error(error: str) -> Tuple[str, str, str, str]:
    lines = error.splitlines()
    if len(lines) < 2:
        print(error)
        return None, None, None, None, None
    error_msg_line = lines[0]
    error_pos_line = lines[1]
    error_details = "\n".join(lines[2:])

    match = re.search(r"(?:error|note|warning): (.*)", error_msg_line)
    if match:
        error_msg = match.group(1)
    else:
        error_msg = None
    
    match = re.search(r"==> (.*?.cj):([0-9]{1,5}):([0-9]{1,5}):", error_pos_line)
    if match:
        error_file = match.group(1)
        error_row = int(match.group(2))
        error_col = int(match.group(3))
    else:
        error_file = None
        error_row = None
        error_col = None
    return error_msg, error_file, error_row, error_col, error_details
