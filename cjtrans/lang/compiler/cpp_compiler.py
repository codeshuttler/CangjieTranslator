import os
import subprocess
from typing import Optional, Tuple
import uuid
import re

from cjtrans.utils.file_utils import write_to_file
from cjtrans.utils.hash_utils import calculate_md5

def compile_and_run_cpp_single(code: str, temp_path: str = "./temp_dir") -> Tuple[Optional[str], Optional[str]]:
    os.makedirs(temp_path, exist_ok=True)
    final_code = code

    file_id = calculate_md5(final_code)
    code_path = os.path.join(temp_path, f"{file_id}.cpp")
    write_to_file(code_path, final_code)
    out_bin_path = os.path.join(temp_path, f"{file_id}_bin")

    try:
        compile_output = subprocess.check_output(
            f"g++ {code_path} -o {out_bin_path}",
            shell=True,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
    except subprocess.CalledProcessError as e:
        print("Compiler CalledProcessError", e.output)
        return e.output, None
    if "error" in compile_output:
        return compile_output, None

    try:
        output = subprocess.check_output(
            f"./{file_id}_bin",
            shell=True,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            cwd=os.path.dirname(code_path),
        )
    except subprocess.CalledProcessError as e:
        print("CalledProcessError", e.output)
        return compile_output, e.output
    return compile_output, output

def compile_and_run_cpp(test_case: str, target_function: str, target_mark: str = "//TOFILL", temp_path: str = "./temp_dir") -> Tuple[Optional[str], Optional[str]]:
    os.makedirs(temp_path, exist_ok=True)
    final_code = test_case.replace(target_mark, target_function)
    return compile_and_run_cpp_single(final_code, temp_path=temp_path)
