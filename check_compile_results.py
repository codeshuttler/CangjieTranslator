import argparse
import glob
import json
import os
import tqdm

from cjtrans.lang.syntax.cj_check import check_cj, parse_error, parse_error_messages
from cjtrans.utils.bash_utils import remove_color_codes
from cjtrans.utils.file_utils import write_to_file
from cjtrans.lang.syntax.cj_check import check_cj_from_file


IGNORE_FAILURE_PATH_PATTERN = "results/gt_failure_list.json"
if os.path.exists(IGNORE_FAILURE_PATH_PATTERN):
    IGNORE_FAILURE_LIST = json.load(open(IGNORE_FAILURE_PATH_PATTERN, "r", encoding="utf-8"))
else:
    IGNORE_FAILURE_LIST = []

USE_TREE_SITTER = True

def main():
    parser = argparse.ArgumentParser(description="test model")
    parser.add_argument("--input", type=str, help="input path")
    parser.add_argument("--use-fixed", action="store_true", help="use fixed cj_target_translation_fixed.cj")
    parser.add_argument("--ignore-failure", action="store_true", help="ignore failure list")
    args = parser.parse_args()
    
    files = list(glob.glob(os.path.join(args.input, "*/cj_target_translation.cj")))

    error_num = 0
    correct_num = 0

    error_paths = []
    correct_paths = []

    for cj_file in tqdm.tqdm(files):
        dir_name = os.path.basename(os.path.dirname(cj_file))
        if args.ignore_failure and dir_name in IGNORE_FAILURE_LIST:
            continue
        # if exists cj_target_translation_fixed.cj, use it
        if args.use_fixed and os.path.exists(cj_file.replace("cj_target_translation.cj", "cj_target_translation_fixed.cj")):
            read_path = cj_file.replace("cj_target_translation.cj", "cj_target_translation_fixed.cj")
            cj_code = open(read_path, "r", encoding="utf8").read()
        # error_final.txt
        elif args.use_fixed and os.path.exists(cj_file.replace("cj_target_translation.cj", "error_final.txt")):
            read_path = cj_file.replace("cj_target_translation.cj", "error_final.txt")
            content = open(read_path, "r", encoding="utf8").read()
            parts = content.split("==========")
            if len(parts) > 2:
                cj_code = parts[1]
        else:
            cj_code = open(cj_file, "r", encoding="utf8").read()
        
        if USE_TREE_SITTER:
            has_error_info = check_cj(cj_code, use_tree_sitter=True)
            has_error_info2 = check_cj(cj_code, use_tree_sitter=False)
            if has_error_info == True and has_error_info2 == False:
                print(f"This file contains error(s): {cj_file}")
            if has_error_info:
                # print(f"输出中包含错误信息: {cj_file}")
                error_num += 1
                error_paths.append(cj_file)
            else:
                correct_num += 1
                correct_paths.append(cj_file)
        else:
            output = check_cj_from_file(cj_file)
            output = remove_color_codes(output)
            if "error" in output:
                print(f"This file contains error(s): {cj_file}")
                
                errors = parse_error_messages(output)
                for error in errors:
                    error_msg, error_file, error_row, error_col, error_details = parse_error(error)
                    print(f"Error Position: {error_file}:{error_row}:{error_col}")
                    print(f"Error Message: {error_msg}.")
                    
                error_num += 1
                error_paths.append(cj_file)
            else:
                correct_num += 1
                correct_paths.append(cj_file)

    print(f"Error Number: {error_num}\nCorrect Number: {correct_num}\nTotal Number: {error_num+correct_num}")


if __name__ == "__main__":
    main()