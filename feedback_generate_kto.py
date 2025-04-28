import glob
import argparse
import json
import os
import random
import re

from cjtrans.myers import Insert, Keep, myers_diff
from cjtrans.utils.file_utils import read_file

INSTRUCTIONS = []
TASK_INSTRUCTIONS_PATH = "resources/sft_prompts/task.json"
with open(TASK_INSTRUCTIONS_PATH, "r", encoding="utf-8") as f:
    INSTRUCTIONS = json.loads(f.read())

def feedback_generate(path: str, out_path: str, language: str):
    lang_full = language
    if language == "java":
        lang_short = "java"
    elif language == "python":
        lang_short = "py"
    elif language == "cpp":
        lang_short = "cpp"
    else:
        raise Exception("Unknown language")

    dataset_out = []
    success_cj_files = glob.glob(os.path.join(path, "*", "cj_target_translation_fixed.cj"))
    for success_cj_file in success_cj_files:
        dir_path = os.path.dirname(success_cj_file)
        
        cj_target_translation_path = os.path.join(dir_path , "cj_target_translation.cj")
        cj_target_translation_fixed_path = os.path.join(dir_path , "cj_target_translation_fixed.cj")
        cj_target_path = os.path.join(dir_path , "cj_target.cj")
        cj_test_path = os.path.join(dir_path , "cj_test.cj")
        
        if language == "java":
            java_target_path = os.path.join(dir_path , "java_target.java")
            java_test_path = os.path.join(dir_path , "java_test.java")
        elif language == "python":
            python_target_path = os.path.join(dir_path , "python_target.py")
            python_test_path = os.path.join(dir_path , "python_test.py")
        elif language == "cpp":
            cpp_target_path = os.path.join(dir_path , "cpp_target.cpp")
            cpp_test_path = os.path.join(dir_path , "cpp_test.cpp")
        else:
            raise Exception("Unknown language")
            
        # Check Error File
        error_0_file = os.path.join(os.path.dirname(success_cj_file), "error_0.txt")
        if not os.path.exists(error_0_file):
            has_error = False
        else:
            has_error = True
        print(success_cj_file)

        if language == "java":
            source_target_code = read_file(java_target_path)
            # source_test_case = read_file(java_test_path)
        elif language == "python":
            source_target_code = read_file(python_target_path)
            # source_test_case = read_file(python_test_path)
        elif language == "cpp":
            source_target_code = read_file(cpp_target_path)
            # source_test_case = read_file(cpp_test_path)
        else:
            raise Exception("Unknown language")

        cj_target_trans_code = read_file(cj_target_translation_path)
        cj_test_case = read_file(cj_test_path)
        
        chosen_code = read_file(cj_target_translation_fixed_path)
        rejected_code = cj_test_case.replace("//TOFILL", cj_target_trans_code)
        
        # Clean Code
        chosen_code = re.sub(r'main\s*\(\s*\)\s*\{[^}]*\}', "", chosen_code).strip()
        rejected_code = re.sub(r'main\s*\(\s*\)\s*\{[^}]*\}', "", rejected_code).strip()
        
        chosen_code = re.sub(r'from std import .*', "", chosen_code).strip()
        rejected_code = re.sub(r'from std import .*', "", rejected_code).strip()

        # Line Level Diff
        chosen_code_line = chosen_code.splitlines(keepends=False)
        rejected_code_line = rejected_code.splitlines(keepends=False)
        
        diff_lines = myers_diff(rejected_code_line, chosen_code_line)
        first_diff_line_index = 0
        for line_num, elem in enumerate(diff_lines):
            if isinstance(elem, Keep):
                # print(' ' + elem.line)
                pass
            elif isinstance(elem, Insert):
                # print('+' + elem.line)
                first_diff_line_index = line_num
                break
            else:
                # print('-' + elem.line)
                first_diff_line_index = line_num
                break
        
        if has_error:
            cj_prompt = '\n'.join(rejected_code_line[:first_diff_line_index])
            
            # Instructions Construction
            instruct = random.choice(INSTRUCTIONS)
            instruct = instruct\
                .replace("{SOURCE_LANG}", language)\
                .replace("{TARGET_LANG}", "Cangjie")\
                .replace("{SOURCE_CODE}", source_target_code)\
                + "\n\n" + f"The following is the beginning part of code converted to Cangjie:\n```cangjie\n{cj_prompt}\n```\nComplete the code."
            sample = {
                "messages": [
                    {
                        "role": "user",
                        "content": instruct
                    },
                    {
                        "role": "assistant",
                        "content": '\n'.join(chosen_code_line[first_diff_line_index:])
                    }
                ],
                "label": True,
            }
            dataset_out.append(sample)
            
            sample = {
                "messages": [
                    {
                        "role": "user",
                        "content": instruct
                    },
                    {
                        "role": "assistant",
                        "content": '\n'.join(rejected_code_line[first_diff_line_index:])
                    }
                ],
                "label": False,
            }
            dataset_out.append(sample)
        else:
            # Instructions Construction
            instruct = random.choice(INSTRUCTIONS)
            instruct = instruct\
                .replace("{SOURCE_LANG}", language)\
                .replace("{TARGET_LANG}", "Cangjie")\
                .replace("{SOURCE_CODE}", source_target_code)
            sample = {
                "messages": [
                    {
                        "role": "user",
                        "content": instruct
                    },
                    {
                        "role": "assistant",
                        "content": chosen_code
                    }
                ],
                "label": True,
            }
            dataset_out.append(sample)
    
    with open(out_path, "w", encoding="utf-8") as f:
        for sample in dataset_out:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    print(f"Dataset saved to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="feedback_generate")
    parser.add_argument("--input", type=str, default="results/leetcode_nonpara_out", help="input path")
    parser.add_argument("--language", type=str, default="java", help="language")
    parser.add_argument("--output", type=str, default="results/pretrain_dataset.jsonl", help="output path")

    args = parser.parse_args()
    feedback_generate(args.input, args.output, args.language)
