import sys
import os
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
)

import os
import string
import json
import re
import argparse

from cjtrans.lang.syntax.cj_check import parse_error_messages, parse_error
def parse_args():
    parser = argparse.ArgumentParser(description="Compiler Errors Types and Number")
    parser.add_argument("--input", type=str, required=True, help="Input Folders, split by ','")
    return parser.parse_args()

def get_error_count_of_dir(dir_name: str):
    error_count_by_iter = {}
    error_count_by_code = {}
    
    for root, dirs, files in os.walk(dir_name):
        for file in files:
            dir_name = os.path.basename(root)
            if file.startswith("error_final.txt"):
                continue
            if file.startswith("error_") and file.endswith(".txt"):
                file_path = os.path.join(root, file)
                print(file_path)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = f.read()
                parts = data.split("==========")
                if len(parts) < 4:
                    continue
                method_name = parts[0].strip()
                before_error = parts[1].strip()
                error_info = parts[2].strip()
                after_error = parts[3].strip()
                
                if "simple_based" in method_name:
                    continue

                errors = parse_error_messages(error_info)
                for error in errors:
                    error_msg, error_file, error_row, error_col, error_details = parse_error(error)
                    # print(f"错误位置: {error_file}:{error_row}:{error_col}")
                    # print(f"错误信息: {error_msg}.")
                    
                    # clean error_msg
                    # 正则表达式operator 'a'替换为operator 'OP'
                    error_msg = re.sub(r"operator '.*?'", "operator <OP>", error_msg)  
                    
                    # 正则表达式替换\'.*?\'为\'\', 第一个替换为\'a\'，第二个替换为\'b\'以此类推
                    # 定义一个用于逐一替换的函数
                    count = 0
                    replacements = string.ascii_lowercase # a-z
                    def replace_match(match):
                        nonlocal count
                        replacement = replacements[count % len(replacements)]
                        count += 1
                        return f"'{replacement}'"

                    # 使用正则表达式进行替换
                    error_msg = re.sub(r"'.*?'", replace_match, error_msg)
                    if error_msg not in error_count_by_iter:
                        error_count_by_iter[error_msg] = 0
                    error_count_by_iter[error_msg] += 1
                    
                    if error_msg not in error_count_by_code:
                        error_count_by_code[error_msg] = set()
                    error_count_by_code[error_msg].add(dir_name)
    return error_count_by_iter, error_count_by_code


def main():
    args = parse_args()
    input_dir = args.input
    if "," in input_dir:
        input_dirs = input_dir.split(",")
    else:
        input_dirs = [input_dir]
    error_count_by_iter = {}
    error_count_by_code = {}
    
    for input_dir in input_dirs:
        each_error_count_by_iter, each_error_count_by_code = get_error_count_of_dir(input_dir)
        for error_type, count in each_error_count_by_iter.items():
            if error_type not in error_count_by_iter:
                error_count_by_iter[error_type] = 0
            error_count_by_iter[error_type] += count
            
        for error_type, count_set in each_error_count_by_code.items():
            if error_type not in error_count_by_code:
                error_count_by_code[error_type] = set()
            error_count_by_code[error_type] |= count_set


    print("编译器错误统计结果(按照迭代次数统计)：")
    for error_type, count in sorted(error_count_by_iter.items(), key=lambda x: x[1], reverse=True):
        print(f"{error_type}: {count}")

    print("编译器错误统计结果(按照代码统计)：")
    for error_type, count in sorted(error_count_by_code.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{error_type}: {len(count)}")

if __name__ == "__main__":
    main()
