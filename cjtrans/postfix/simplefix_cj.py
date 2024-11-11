import re
from typing import Dict, List, Optional, Tuple

from cjtrans.parser.expression import ExpressionExtractor
from cjlang.lexer.cursor import Cursor

def count_leading_whitespace(s: str):
    return len(s) - len(s.lstrip())

def _get_up_arrow_line(lines: List[str]) -> Optional[str]:
    for line in lines:
        if "^" in line:
            return line
    return None

def _get_up_arrow_start_end_pos(line: str) -> Tuple[int, int]:
    if "| " in line:
        s = line.index("| ")
        line = line[s + len("| "):]

    first_caret = line.find('^')
    last_caret = line.rfind('^')
    return first_caret, last_caret + 1

def is_type_cast_token(token):
    return token.type == "IDENTIFIER" and (token.value.startswith("Int") or token.value.startswith("Float") or token.value.startswith("Char"))

def insert_at_index(s, i, char):
    return s[:i] + char + s[i:]

def replace_at_range(s, start_pos, end_pos, new_char):
    return s[:start_pos] + new_char + s[end_pos:]

def fix_mismatch_type(line: str, error_msg: str, error_details: str) -> str:
    array_match = re.search(r"expected 'Struct-Array<([a-zA-Z0-9_\-<>]+?)>', found 'Struct-Array<([a-zA-Z0-9_\-<>]+?)>'", error_details)
    general_match = re.search(r"expected '([a-zA-Z0-9_\-<>]+?)', found '([a-zA-Z0-9_\-<>]+?)'", error_details)

    basic_types = ["Char", "UInt8", "Int8", "UInt16", "Int16", "UInt32", "Int32", "UInt64", "Int64", "Float16", "Float32", "Float64"]
    if array_match:
        new_line = line
        excepted_type = array_match.group(1)
        found_type = array_match.group(2)
        up_arrow_line = _get_up_arrow_line(error_details.splitlines())
        start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
        if excepted_type in basic_types and found_type in basic_types:
            new_str = f"Array<{excepted_type}>({line[start_pos:end_pos]}.size, {{idx => {excepted_type}({line[start_pos:end_pos]}[idx])}})"
            new_line = replace_at_range(line, start_pos, end_pos, new_str)
        else:
            new_line = line
        return new_line
    elif general_match:
        new_line = line
        excepted_type = general_match.group(1)
        found_type = general_match.group(2)
        up_arrow_line = _get_up_arrow_line(error_details.splitlines())
        start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
        
        excepted_struct_array_match = re.match(r"Struct-Array<([a-zA-Z0-9_\-<>]+?)>", excepted_type)
        excepted_class_linked_list_match = re.match(r"Class-LinkedList<([a-zA-Z0-9_\-<>]+?)>", excepted_type)

        found_struct_array_match = re.match(r"Struct-Array<([a-zA-Z0-9_\-<>]+?)>", found_type)
        found_class_linked_list_match = re.match(r"Class-LinkedList<([a-zA-Z0-9_\-<>]+?)>", found_type)

        if excepted_type in basic_types and found_type in basic_types:
            new_line = insert_at_index(new_line, end_pos, ")")
            new_line = insert_at_index(new_line, start_pos, f"{excepted_type}(")
        elif re.match(r"Enum-Option<([a-zA-Z0-9_\-<>]+?)>", found_type) and found_type == f'Enum-Option<{excepted_type}>':
            new_line = insert_at_index(new_line, end_pos, ".getOrThrow()")
        elif (
            excepted_struct_array_match
            and found_class_linked_list_match
            and excepted_struct_array_match.group(1)
            == found_class_linked_list_match.group(1)
        ):
            new_line = insert_at_index(new_line, end_pos, f".toArray()")
        elif found_type.startswith('Class-') or excepted_type.startswith('Class-'):
            if excepted_type.startswith('Class-'):
                excepted_type = excepted_type[len('Class-'):]
            if excepted_type.startswith('Struct-'):
                excepted_type = excepted_type[len('Struct-'):]
            new_line = insert_at_index(new_line, end_pos, f" as {excepted_type}")

        return new_line
    else:
        return line

def fix_cj_line(line: str, error_msg: str, error_details: str) -> str:
    # print(line)
    fixed_line = line
    if "mismatched types" in error_msg:
        fixed_line = fix_mismatch_type(line, error_msg, error_details)
    return fixed_line

def simple_fix_cj(cj_code: str, compiler_outputs: List[Tuple[str, str, str, str, str]]) -> Tuple[str, Dict[str, str]]:
    lines = cj_code.splitlines()
    # Unique outputs
    compiler_outputs_rc = set()
    unique_compiler_outputs = []
    for error in compiler_outputs:
        error_msg, error_file, error_row, error_col, error_details = error
        if (error_row, error_col) in compiler_outputs_rc:
            continue
        compiler_outputs_rc.add((error_row, error_col))
        unique_compiler_outputs.append(error)
    compiler_outputs = unique_compiler_outputs

    for error in reversed(compiler_outputs):
        error_msg, error_file, error_row, error_col, error_details = error
        if error_file is None:
            continue
        error_line_index = error_row - 1
        if error_line_index >= len(lines):
            continue
        error_line = lines[error_line_index]
        # print(error_line)
        new_line = fix_cj_line(error_line, error_msg, error_details)
        lines[error_line_index] = new_line
    
    return ("\n".join(lines), {})
