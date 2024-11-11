import os
import subprocess
from typing import Optional, Tuple
import uuid
import re

from cjtrans.utils.file_utils import write_to_file
from cjtrans.utils.hash_utils import calculate_md5

def get_class_name(code: str) -> Optional[str]:
    pattern = r"public\s+class\s+(\w+)\s*"

    match = re.search(pattern, code)
    if match:
        return match.group(1)
    else:
        return None

def compile_and_run_java(test_case: str, target_function: str, target_mark: str = "//TOFILL", temp_path: str = "./temp_dir") -> Tuple[Optional[str], Optional[str]]:
    os.makedirs(temp_path, exist_ok=True)
    # if "main() {" in target_function:
    #     final_code = target_function
    # else:
    final_code = test_case.replace(target_mark, target_function)

    # file_id = calculate_md5(final_code)
    file_id = get_class_name(final_code)
    if file_id is None:
        return None, None
    code_path = os.path.join(temp_path, f"{file_id}.java")
    write_to_file(code_path, final_code)

    try:
        compile_output = subprocess.check_output(
            f"javac {code_path}",
            shell=True,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
    except subprocess.CalledProcessError as e:
        # print(e.output)
        return e.output, None
    if "error" in compile_output:
        return compile_output, None

    try:
        class_path = os.path.basename(code_path.replace(".java", ""))
        output = subprocess.check_output(
            f"java {class_path}",
            shell=True,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            cwd=os.path.dirname(code_path),
        )
    except subprocess.CalledProcessError as e:
        # print(e.output)
        return compile_output, e.output
    return compile_output, output
