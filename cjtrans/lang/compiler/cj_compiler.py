
import os
import subprocess
from typing import Optional, Tuple
import uuid

from cjtrans.utils.file_utils import write_to_file
from cjtrans.utils.hash_utils import calculate_md5


def compile_and_run_cj_single(code: str, target_mark: str = "//TOFILL", temp_path: str = "./temp_dir") -> Tuple[Optional[str], Optional[str]]:
    os.makedirs(temp_path, exist_ok=True)
    final_code = code
    
    file_id = calculate_md5(final_code)
    code_path = os.path.join(temp_path, f"{file_id}.cj")
    write_to_file(code_path, final_code)
    out_bin_path = os.path.join(temp_path, f"{file_id}_bin")
    
    try:
        compile_output = subprocess.check_output(f"cjc {code_path} -o {out_bin_path}", shell=True, stderr=subprocess.STDOUT, universal_newlines=True, timeout=60)
    except subprocess.CalledProcessError as e:
        compile_output = e.output
        if isinstance(compile_output, bytes):
            compile_output = compile_output.decode("utf-8")
        return compile_output, None
    except subprocess.TimeoutExpired as e:
        compile_output = e.output
        if isinstance(compile_output, bytes):
            compile_output = compile_output.decode("utf-8")
        return compile_output, None
    if isinstance(compile_output, bytes):
        compile_output = compile_output.decode("utf-8")
    if "error" in compile_output:
        return compile_output, None
    
    try:
        output = subprocess.check_output(f"./{out_bin_path}", shell=True, stderr=subprocess.STDOUT, universal_newlines=True, timeout=60)
    except subprocess.CalledProcessError as e:
        if isinstance(compile_output, bytes):
            compile_output = compile_output.decode("utf-8")
        return compile_output, e.output
    except subprocess.TimeoutExpired as e:
        if isinstance(compile_output, bytes):
            compile_output = compile_output.decode("utf-8")
        return compile_output, None
    if isinstance(compile_output, bytes):
        compile_output = compile_output.decode("utf-8")
    return compile_output, output

def compile_and_run_cj(test_case: str, target_function: str, target_mark: str = "//TOFILL", temp_path: str = "./temp_dir") -> Tuple[Optional[str], Optional[str]]:
    os.makedirs(temp_path, exist_ok=True)
    final_code = test_case.replace(target_mark, target_function)
    return compile_and_run_cj_single(final_code, target_mark=target_mark, temp_path=temp_path)