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

def fix_undeclared_identifier(line: str, error_msg: str, error_details: str) -> str:
    up_arrow_line = _get_up_arrow_line(error_details.splitlines())
    start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
    match = re.search(r"undeclared identifier '([a-zA-Z0-9_]+?)'", error_msg)
    if match:
        new_line = line
        identifier_name = match.group(1)
        if identifier_name == "Math":
            new_line = new_line.replace('Math', 'math')
        elif identifier_name == "Max":
            new_line = new_line.replace('Max', 'max')
        elif identifier_name == "Min":
            new_line = new_line.replace('Min', 'min')
        return new_line
    else:
        return line

def fix_expected_left_brace(line: str, error_msg: str, error_details: str) -> str:
    up_arrow_line = _get_up_arrow_line(error_details.splitlines())
    start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
    match = re.search(r"expected '{', found .*", error_msg)
    if match:
        new_line = line
        new_line = insert_at_index(new_line, len(new_line), "}")
        new_line = insert_at_index(new_line, start_pos, "{")
        return new_line
    else:
        return line

def fix_invalid_binary_operator_type(line: str, error_msg: str, error_details: str) -> str:
    tokenizer = Cursor(line)
    tokens = tokenizer.tokenize()
    
    up_arrow_line = _get_up_arrow_line(error_details.splitlines())
    start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
    
    # print(line)
    # print(tokens)
    
    target_token = -1
    for token_i, token in enumerate(tokens):
        if token.start_pos >= start_pos and token.end_pos <= end_pos:
            target_token = token_i
            break
    
    if target_token == -1:
        return line

    extractor = ExpressionExtractor(tokens)
    lhs, rhs = extractor.find_expressions_around_token(target_token)
    # print(lhs)
    # print(rhs)
    if len(lhs) == 0 or len(rhs) == 0:
        return line
    
    # Conversion
    basic_types = ["UInt8", "Char", "Int8", "UInt16", "Int16", "UInt32", "Int32", "UInt64", "Int64", "Float16", "Float32", "Float64"]
    
    match = re.search(r"invalid binary operator '(?:==|!=|<=|>=|[\+\-\*/<>])' on type '([a-zA-Z0-9_\-<>]+?)' and '([a-zA-Z0-9_\-<>]+?)'", error_msg)
    if match:
        lhs_type = match.group(1)
        rhs_type = match.group(2)
        if lhs_type in basic_types and rhs_type in basic_types:
            new_line = line
            lhs_level = basic_types.index(lhs_type)
            rhs_level = basic_types.index(rhs_type)
            if lhs_type == "Char" and rhs_type == "UInt8" and len(lhs) == 1 and lhs[0].type == "CHARACTER":
                new_line = insert_at_index(new_line, lhs[0].start_pos, "b")
            elif lhs_type == "UInt8" and rhs_type == "Char" and len(rhs) == 1 and rhs[0].type == "CHARACTER":
                new_line = insert_at_index(new_line, rhs[0].start_pos, "b") 
            else:
                if lhs_level > rhs_level:
                    # Cast right
                    if is_type_cast_token(rhs[0]):
                        new_line = replace_at_range(new_line, rhs[0].start_pos, rhs[0].end_pos, lhs_type)
                    else:
                        new_line = insert_at_index(new_line, rhs[-1].end_pos, ")")
                        new_line = insert_at_index(new_line, rhs[0].start_pos, f"{lhs_type}(")
                else:
                    # Cast Left
                    if is_type_cast_token(lhs[0]):
                        new_line = replace_at_range(new_line, lhs[0].start_pos, lhs[0].end_pos, rhs_type)
                    else:
                        new_line = insert_at_index(new_line, lhs[-1].end_pos, ")")
                        new_line = insert_at_index(new_line, lhs[0].start_pos, f"{rhs_type}(")
            return new_line
        elif re.match(r"Enum-Option<([a-zA-Z0-9_\-<>]+?)>", lhs_type) and rhs_type == 'Enum-Option<Generics-T>':
            new_line = line
            st = new_line[lhs[-1].end_pos:].lstrip()
            if st.startswith('== None') or st.startswith('==None'):
                new_line = replace_at_range(new_line, lhs[-1].end_pos, rhs[-1].end_pos, '.isNone()')
            return new_line
        else:
            return line
    else:
        return line
    return line

def fix_function_call(line: str, error_msg: str, error_details: str) -> str:
    up_arrow_line = _get_up_arrow_line(error_details.splitlines())
    start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
    
    # 寻找第一个左括号的位置
    left_index = line.find('(', start_pos)
    if left_index == -1:
        return line  # 如果找不到左括号，直接返回原字符串

    # 替换括号
    new_line = line[:left_index] + re.sub(r"\(.*?\)", "", line[left_index:])
    return new_line

def fix_uint8_char(line: str, error_msg: str, error_details: str) -> str:
    new_line = re.sub(r"'([a-zA-Z0-9])'", r"b'\1'", line)
    return new_line

def fix_immutable_parameter(line: str, error_msg: str, error_details: str) -> str:
    match = re.search(r"parameter '([a-zA-Z0-9_]+?)' is immutable", error_msg)
    if match:
        new_line = line
        parameter_name = match.group(1)
        up_arrow_line = _get_up_arrow_line(error_details.splitlines())
        start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
        new_line = replace_at_range(line, start_pos, end_pos, f"_{parameter_name}")
        return new_line + "\n" + " " * (count_leading_whitespace(new_line) + 4) + f"var {parameter_name} = _{parameter_name}"
    else:
        return line

def fix_immutable_variable(line: str, error_msg: str, error_details: str) -> str:
    match = re.search(r"variable '([a-zA-Z0-9_]+?)' is immutable", error_msg)
    if match:
        new_line = line
        variable_name = match.group(1)
        up_arrow_line = _get_up_arrow_line(error_details.splitlines())
        start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
        if "let" in error_details:
            new_line = line.replace("let", "var")
        elif "for" in error_details:
            new_line = line
        else:
            new_line = line
        return new_line
    else:
        return line

def fix_char_literal_to_uint8(line: str, error_msg: str, error_details: str) -> str:
    up_arrow_line = _get_up_arrow_line(error_details.splitlines())
    start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
    # 寻找第一个左括号的位置
    left_index = line.find('\'', start_pos)
    if left_index == -1:
        return line  # 如果找不到左括号，直接返回原字符串

    # 替换括号
    new_line = line[:left_index] + re.sub(r"'([a-zA-Z0-9])'", r"b'\1'", line[left_index:], count=1)
    return new_line

def fix_integer_literal_to_float(line: str, error_msg: str, error_details: str) -> str:
    match = re.search(r"cannot convert an integer literal to type '(Float[0-9]{2})'", error_msg)
    
    basic_types = ["Char", "UInt8", "Int8", "UInt16", "Int16", "UInt32", "Int32", "UInt64", "Int64", "Float16", "Float32", "Float64"]
    if match:
        new_line = line
        target_type = match.group(1)
        up_arrow_line = _get_up_arrow_line(error_details.splitlines())
        start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
        value = line[start_pos: end_pos]
        if "i" in value:
            split = value.index('i')
            value = value[:split]
        if "u" in value:
            split = value.index('u')
            value = value[:split]
        if target_type in basic_types:
            if target_type == "Float16":
                new_line = replace_at_range(line, start_pos, end_pos, f"{value}.0f16")
            elif target_type == "Float32":
                new_line = replace_at_range(line, start_pos, end_pos, f"{value}.0f32")
            elif target_type == "Float64":
                new_line = replace_at_range(line, start_pos, end_pos, f"{value}.0f64")
        else:
            new_line = line
        return new_line
    else:
        return line

def fix_static_modifier(line: str, error_msg: str, error_details: str) -> str:
    up_arrow_line = _get_up_arrow_line(error_details.splitlines())
    start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
    new_line = replace_at_range(line, start_pos, end_pos, "")
    return new_line

def fix_not_a_member(line: str, error_msg: str, error_details: str) -> str:
    up_arrow_line = _get_up_arrow_line(error_details.splitlines())
    start_pos, end_pos = _get_up_arrow_start_end_pos(up_arrow_line)
    match = re.search(r"'([a-zA-Z0-9_]+?)' is not a member of class '([a-zA-Z0-9_\-<>]+?)'", error_msg)
    if match:
        new_line = line
        member_name = match.group(1)
        class_name = match.group(2)
        # 'size' is not a member of enum 'Option<Class-ArrayList<Int32>>'
        if re.match(r"Option<([a-zA-Z0-9_\-<>]+?)>", class_name):
            new_line = insert_at_index(new_line, end_pos, ".getOrThrow()")
        elif member_name == 'insert' and re.match(r"HashSet<([a-zA-Z0-9_\-<>]+?)>", class_name):
            new_line = replace_at_range(new_line, start_pos, end_pos, "put")
        else:
            print("Not a member: ", class_name, member_name)
        return new_line
    else:
        return line

def fix_cj_line(line: str, error_msg: str, error_details: str) -> str:
    # print(line)
    fixed_line = line
    if "mismatched types" in error_msg:
        fixed_line = fix_mismatch_type(line, error_msg, error_details)
    elif "unable to infer return type, please add type annotation" in error_msg:
        pass
    elif re.search(r"expected '{', found .*", error_msg) is not None:
        fixed_line = fix_expected_left_brace(line, error_msg, error_details)
    elif re.search(r"undeclared identifier '([a-zA-Z0-9_]+?)'", error_msg) is not None:
        fixed_line = fix_undeclared_identifier(line, error_msg, error_details)
    elif re.search(r"invalid binary operator '(?:==|!=|<=|>=|[\+\-\*/<>])' on type '([a-zA-Z0-9_\-<>]+?)' and '([a-zA-Z0-9_\-<>]+?)'", error_msg) is not None:
        try:
            fixed_line = fix_invalid_binary_operator_type(line, error_msg, error_details)
        except TypeError as e:
            pass
    elif "no matching function for operator '()' function call" in error_msg:
        fixed_line = fix_function_call(line, error_msg, error_details)
    elif re.search(r"parameter '([a-zA-Z0-9_]+?)' is immutable", error_msg) is not None:
        fixed_line = fix_immutable_parameter(line, error_msg, error_details)
    elif "cannot convert a character literal to type 'UInt8'" in error_msg:
        fixed_line  = fix_char_literal_to_uint8(line, error_msg, error_details)
    elif re.search(r"cannot convert an integer literal to type 'Float[0-9]{2}'", error_msg) is not None:
        fixed_line  = fix_integer_literal_to_float(line, error_msg, error_details)
    elif re.search(r"variable '([a-zA-Z0-9_]+?)' is immutable", error_msg) is not None:
        fixed_line = fix_immutable_variable(line, error_msg, error_details)
    elif "unexpected modifier 'static' on function declaration in 'top-level' scope" in error_msg:
        fixed_line = fix_static_modifier(line, error_msg, error_details)
    elif re.search(r"'([a-zA-Z0-9_]+?)' is not a member of class '([a-zA-Z0-9_\-<>]+?)'", error_msg) is not None:
        fixed_line = fix_not_a_member(line, error_msg, error_details)
    else:
        pass
        # print(line)
        # print(error_msg)
    return fixed_line

def fix_cj(cj_code: str, compiler_outputs: List[Tuple[str, str, str, str, str]]) -> Tuple[str, Dict[str, str]]:
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
