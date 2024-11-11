import os
import json
import argparse
import re

IGNORE_FAILURE_PATH_PATTERN = "results/gt_failure_list.json"
if os.path.exists(IGNORE_FAILURE_PATH_PATTERN):
    IGNORE_FAILURE_LIST = json.load(open(IGNORE_FAILURE_PATH_PATTERN, "r", encoding="utf-8"))
else:
    IGNORE_FAILURE_LIST = []

def collect_execution_results(input_dir: str):
    """
    Collect execution results from the input directory and save them to the output file.
    """
    error_num = 0
    execution_num = 0
    correct_num = 0
    total_num = 0

    for root, dirs, files in os.walk(input_dir):
        for file in files:
            print(root, file)
            dir_name = os.path.basename(root)
            if dir_name in IGNORE_FAILURE_LIST:
                continue
            if file.endswith('java_target.java'):
                fixed_final_code = os.path.join(root, 'cj_target_translation_fixed.cj')
                failure_result = os.path.join(root, 'failure.txt')
                pass_result = os.path.join(root, 'pass.txt')
                
                total_num += 1
                if os.path.exists(pass_result) or os.path.exists(failure_result) or os.path.exists(fixed_final_code):
                    execution_num += 1
                if os.path.exists(failure_result):
                    error_num += 1
                if os.path.exists(pass_result):
                    correct_num += 1
    
    print(f"Compilation Succeeded: {execution_num}\nTest Failure: {error_num}\nTest Correction: {correct_num}\nTotal Number: {total_num}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect execution results from the input directory and save them to the output file.")
    parser.add_argument("--input", type=str, required=True, help="The input directory containing execution results.")
    args = parser.parse_args()

    collect_execution_results(args.input)