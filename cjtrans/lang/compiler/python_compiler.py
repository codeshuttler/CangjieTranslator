import os
import subprocess
from typing import Optional, Tuple
import uuid
import re

from cjtrans.utils.file_utils import write_to_file
from cjtrans.utils.hash_utils import calculate_md5

import py_compile

def compile_and_run_python_single(code: str, temp_path: str = "./temp_dir") -> Tuple[Optional[str], Optional[str]]:
    os.makedirs(temp_path, exist_ok=True)
    # if "main() {" in target_function:
    #     final_code = target_function
    # else:
    final_code = code

    file_id = calculate_md5(final_code)
    code_path = os.path.join(temp_path, f"{file_id}.py")
    write_to_file(code_path, final_code)
    
    try:
        py_compile.compile(code_path, doraise=True)
        compile_output = ""
    except py_compile.PyCompileError as e:
        return e.msg, None

    try:
        output = subprocess.check_output(
            f"python {file_id}.py",
            shell=True,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            cwd=os.path.dirname(code_path),
        )
    except subprocess.CalledProcessError as e:
        # print(e.output)
        return compile_output, e.output
    return compile_output, output

def compile_and_run_python(test_case: str, target_function: str, target_mark: str = "#TOFILL", temp_path: str = "./temp_dir") -> Tuple[Optional[str], Optional[str]]:
    os.makedirs(temp_path, exist_ok=True)
    final_code = test_case.replace(target_mark, target_function)
    return compile_and_run_python_single(final_code, temp_path=temp_path)
