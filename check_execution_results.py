import argparse
import glob
import json
import os
from typing import List, Optional, Union
import openai
import tqdm

from cjtrans.lang.compiler.cpp_compiler import compile_and_run_cpp, compile_and_run_cpp_single
from cjtrans.lang.compiler.java_compiler import compile_and_run_java, compile_and_run_java_single
from cjtrans.lang.compiler.python_compiler import compile_and_run_python, compile_and_run_python_single
from cjtrans.lang.syntax.cj_check import check_cj, parse_error, parse_error_messages
from cjtrans.lang.compiler.cj_compiler import compile_and_run_cj, compile_and_run_cj_single
from cjtrans.postfix.ai_postfix_cj import ai_fix_cj
from cjtrans.postfix.postfix_cj import fix_cj
from cjtrans.postfix.simplefix_cj import simple_fix_cj
from cjtrans.utils.bash_utils import remove_color_codes
from cjtrans.utils.file_utils import read_file, write_to_file


def have_compilation_error(code: str) -> bool:
    # try compile
    cj_compile_output, cj_output = compile_and_run_cj_single(code)
    if not isinstance(cj_compile_output, str):
        print(type(cj_compile_output), cj_compile_output)
    cj_compile_output = remove_color_codes(cj_compile_output)
    
    return len(cj_compile_output.strip()) != 0 and "error" in cj_compile_output


def merge_exception_lines(log_lines: list[str]) -> list[str]:
    merged_lines = []
    temp_line = ""

    for line in log_lines:
        if "<Exception>" in line:
            if temp_line:
                temp_line += " " + line.strip()  # Merge with the previous exception line
            else:
                temp_line = line.strip()  # Start a new exception block
        else:
            if temp_line:
                merged_lines.append(temp_line)  # Append the merged exception block
                temp_line = ""
            merged_lines.append(line.strip())  # Append the non-exception line

    if temp_line:
        merged_lines.append(temp_line)  # Append the last exception block if exists

    return merged_lines

def parse_test_out(content: str) -> List[str]:
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if 'exception' in line.lower() or 'at ' in line.lower():
            lines[i] = '<Exception>'
        
        # True to true, False to false
        if 'True' in line:
            lines[i] = line.replace('True', 'true')
        if 'False' in line:
            lines[i] = line.replace('False', 'false')
    
    lines = [line for line in lines if "Wrong input" not in line]
    ret = merge_exception_lines(lines)
    return ret


def process_code_fix(fix_steps: Optional[Union[List[str], str]], final_code: str, error_path: str, model: str, base_url: str, api_key: str):
    if fix_steps is None:
        fix_steps = "simple,rule,llm"
    if isinstance(fix_steps, str):
        fix_steps = fix_steps.split(",")
    cur_fix_step = 0

    last_code = None
    fix_method = fix_steps[cur_fix_step]
    for try_i in range(8):
        if not have_compilation_error(final_code):
            break

        # Fix Code
        cj_compile_output, cj_output = compile_and_run_cj_single(final_code)
        cj_compile_output = remove_color_codes(cj_compile_output)
        errors = parse_error_messages(cj_compile_output)
        error_messages = []
        for error in errors:
            error_msg, error_file, error_row, error_col, error_details = parse_error(error)
            error_messages.append((error_msg, error_file, error_row, error_col, error_details))

        if fix_method == "rule":
            fixed_final_code, details = fix_cj(final_code, error_messages)
            write_to_file(
                error_path.replace(".txt", f"_{try_i}.txt"),
                "\n==========\n".join(
                    [
                        "rule_based",
                        final_code,
                        cj_compile_output,
                        fixed_final_code,
                        json.dumps(details, ensure_ascii=False),
                    ]
                ),
            )
            final_code = fixed_final_code
        elif fix_method == "llm":
            try:
                fixed_final_code, details = ai_fix_cj(
                    final_code,
                    error_messages,
                    doc_path="raw_data/cangjie_documents/tutorial",
                    model_name=model,
                    base_url=base_url,
                    api_key=api_key,
                )
            except ValueError as e:
                fixed_final_code = None
                details = {"error_message": str(e)}
            except openai.BadRequestError as e:
                if "Please reduce the length of the messages or completion." in str(e):
                    fixed_final_code = None
                    details = {"error_message": str(e)}
                else:
                    raise e
            if fixed_final_code is None:
                fixed_final_code = final_code
            write_to_file(
                error_path.replace(".txt", f"_{try_i}.txt"),
                "\n==========\n".join(
                    [
                        "llm_based",
                        final_code,
                        cj_compile_output,
                        fixed_final_code,
                        json.dumps(details, ensure_ascii=False),
                    ]
                ),
            )
            final_code = fixed_final_code
        elif fix_method == "simple":
            fixed_final_code, details = simple_fix_cj(
                final_code,
                error_messages,
            )
            if fixed_final_code is None:
                fixed_final_code = final_code
            write_to_file(
                error_path.replace(".txt", f"_{try_i}.txt"),
                "\n==========\n".join(
                    [
                        "simple_based",
                        final_code,
                        cj_compile_output,
                        fixed_final_code,
                        json.dumps(details, ensure_ascii=False),
                    ]
                ),
            )
            final_code = fixed_final_code
        else:
            fixed_final_code = final_code
            write_to_file(
                error_path.replace(".txt", f"_{try_i}.txt"),
                "\n==========\n".join(
                    [
                        "unknown_fix",
                        final_code,
                        cj_compile_output,
                        fixed_final_code,
                        json.dumps({}, ensure_ascii=False),
                    ]
                ),
            )

        if last_code == final_code:
            cur_fix_step += 1
            if cur_fix_step < len(fix_steps):
                fix_method = fix_steps[cur_fix_step]
            else:
                break
        last_code = final_code

    return final_code

def main():
    parser = argparse.ArgumentParser(description="test model")
    parser.add_argument("--input", type=str, default="results/cangjie_para_out/", help="input path")
    parser.add_argument('--auto-fix', action='store_true',help="Enable auto-fix mode")
    parser.add_argument('--fix-steps', type=str, help="Set fix steps", default="simple,rule,llm")
    parser.add_argument('--test-ground-truth', action='store_true', help="Enable testing of ground truth function")
    parser.add_argument('--language', type=str, help="The language tested", default="java")
    parser.add_argument("--model", default="Qwen/Qwen2.5-72B-Instruct-GPTQ-Int4", type=str, help="LLM path")
    parser.add_argument("--base-url", default="http://frp-cat.com:60934/v1", type=str, help="base url")
    parser.add_argument("--api-key", default="your_api_key", type=str, help="api key")

    args = parser.parse_args()

    files = list(glob.glob(os.path.join(args.input, "*/cj_test.cj")))

    total_num = 0
    error_num = 0
    execution_num = 0
    correct_num = 0

    error_paths = []
    execution_paths = []
    correct_paths = []

    for cj_file in tqdm.tqdm(files):
        print(cj_file)
        total_num += 1

        dir_path = os.path.dirname(cj_file)
        
        cj_target_translation_path = os.path.join(dir_path , "cj_target_translation.cj")
        cj_target_path = os.path.join(dir_path , "cj_target.cj")
        cj_test_path = os.path.join(dir_path , "cj_test.cj")
        cj_target_translation_fixed_path = os.path.join(dir_path , "cj_target_translation_fixed.cj")
        
        java_target_path = os.path.join(dir_path , "java_target.java")
        java_test_path = os.path.join(dir_path , "java_test.java")
        
        python_target_path = os.path.join(dir_path , "python_target.py")
        python_test_path = os.path.join(dir_path , "python_test.py")
        
        cpp_target_path = os.path.join(dir_path , "cpp_target.cpp")
        cpp_test_path = os.path.join(dir_path , "cpp_test.cpp")

        error_path = os.path.join(dir_path , "error.txt")
        error_final_path = os.path.join(dir_path , "error_final.txt")
        failure_path = os.path.join(dir_path , "failure.txt")
        pass_path = os.path.join(dir_path , "pass.txt")
        # print(cj_target_path.replace("results/cangjie_para_out", "raw_data/cangjie_para_clean"))
        
        if not os.path.exists(cj_target_translation_path):
            continue
        if not os.path.exists(cj_test_path):
            continue

        cj_target_trans_code = read_file(cj_target_translation_path)
        cj_target_code = read_file(cj_target_path)
        cj_test_case = read_file(cj_test_path)
        if not args.test_ground_truth:
            final_code = cj_test_case.replace("//TOFILL", cj_target_trans_code)
        else:
            final_code = cj_test_case.replace("//TOFILL", cj_target_code)
        
        if os.path.exists(pass_path) or os.path.exists(failure_path) \
            or os.path.exists(error_final_path): # or os.path.exists(os.path.join(dir_path , "error_0.txt")) \
            continue

        if not os.path.exists(cj_target_translation_fixed_path):
            if args.auto_fix:
                final_code = process_code_fix(
                    fix_steps = args.fix_steps,
                    final_code = final_code,
                    error_path = error_path,
                    model = args.model,
                    base_url = args.base_url,
                    api_key = args.api_key,
                )
        else:
            final_code = read_file(cj_target_translation_fixed_path)
        
        pass_test = not have_compilation_error(final_code)

        if not pass_test:
            cj_compile_output, cj_output = compile_and_run_cj_single(final_code)
            cj_compile_output = remove_color_codes(cj_compile_output)
            write_to_file(error_path.replace(".txt", f"_final.txt"), "\n==========\n".join(["final", final_code, cj_compile_output, "None"]))

            print(f"The output contains error information: {cj_target_translation_path}")
            error_num += 1
            error_paths.append(cj_target_translation_path)
        else:
            if cj_target_trans_code.count("//") < 10 and cj_target_trans_code.count("import") < 5:
                execution_num += 1
                execution_paths.append(cj_target_translation_path)
                write_to_file(cj_target_translation_fixed_path, final_code)
            else:
                error_num += 1
                error_paths.append(cj_target_translation_path)

        # Run and Compare results
        if args.language == "java":
            if not os.path.exists(java_target_path) and not os.path.exists(java_test_path):
                raise ValueError("Java file not found")
            if os.path.exists(java_target_path) and not os.path.exists(java_test_path):
                source_compile_output, source_output = compile_and_run_java_single(
                    read_file(java_target_path),
                )
            else:
                source_compile_output, source_output = compile_and_run_java(
                    test_case=read_file(java_test_path),
                    target_function=read_file(java_target_path),
                )
        elif args.language == "python":
            if not os.path.exists(python_target_path) and not os.path.exists(python_test_path):
                raise ValueError("Python file not found")
            if os.path.exists(python_target_path) and not os.path.exists(python_test_path):
                source_compile_output, source_output = compile_and_run_python_single(
                    read_file(python_target_path),
                )
            else:
                source_compile_output, source_output = compile_and_run_python(
                    test_case=read_file(python_test_path),
                    target_function=read_file(python_target_path),
                )
        elif args.language == "cpp":
            if not os.path.exists(cpp_target_path) and not os.path.exists(cpp_test_path):
                raise ValueError("C++ file not found")
            if os.path.exists(cpp_target_path) and not os.path.exists(cpp_test_path):
                source_compile_output, source_output = compile_and_run_cpp_single(
                    read_file(cpp_target_path),
                )
            else:
                source_compile_output, source_output = compile_and_run_cpp(
                    test_case=read_file(cpp_test_path),
                    target_function=read_file(cpp_target_path),
                )
        else:
            raise ValueError("Unsupported language")
        cj_compile_output, cj_output = compile_and_run_cj_single(final_code)

        if source_output is not None and cj_output is not None:
            source_results = parse_test_out(source_output.strip())
            cj_results = parse_test_out(cj_output.strip())

            if source_results == cj_results:
                correct_num += 1
                correct_paths.append(cj_target_translation_path)
                write_to_file(pass_path, cj_output)
            else:
                write_to_file(failure_path, source_output + "\n==========\n" + cj_output)

    print(f"Errors: {error_num}\nExecution Successful: {execution_num}\nTest Passed: {correct_num}\nTotal Files: {total_num}")


if __name__ == "__main__":
    main()
