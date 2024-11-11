import argparse
import glob
import json
import os
import tqdm

from cjtrans.lang.compiler.java_compiler import compile_and_run_java
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

def main():
    parser = argparse.ArgumentParser(description="test model")
    parser.add_argument("--input", type=str, default="results/cangjie_para_out/", help="input path")
    # 添加 bool 参数，用于控制是否开启自动修复
    parser.add_argument('--auto-fix', action='store_true', help="Enable auto-fix mode")
    parser.add_argument('--fix-steps', type=str, help="Set fix steps", default="simple,rule,llm")
    # 添加 --test-oracle 参数，用于控制是否测试 oracle 函数
    parser.add_argument('--test-ground-truth', action='store_true', help="Enable testing of ground truth function")

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
        # if "COUNT_ENTRIES_EQUAL_TO_X_IN_A_SPECIAL_MATRIX" not in cj_file:
        #     continue
        total_num += 1

        dir_path = os.path.dirname(cj_file)
        cj_target_translation_path = os.path.join(dir_path , "cj_target_translation.cj")
        java_target_path = os.path.join(dir_path , "java_target.java")
        cj_target_path = os.path.join(dir_path , "cj_target.cj")
        java_test_path = os.path.join(dir_path , "java_test.java")
        cj_test_path = os.path.join(dir_path , "cj_test.cj")
        cj_target_translation_fixed_path = os.path.join(dir_path , "cj_target_translation_fixed.cj")

        error_path = os.path.join(dir_path , "error.txt")
        error_final_path = os.path.join(dir_path , "error_final.txt")
        failure_path = os.path.join(dir_path , "failure.txt")
        pass_path = os.path.join(dir_path , "pass.txt")
        # print(cj_target_path.replace("results/cangjie_para_out", "raw_data/cangjie_para_clean"))

        cj_target_trans_code = read_file(cj_target_translation_path)
        cj_target_code = read_file(cj_target_path)
        cj_test_case = read_file(cj_test_path)
        if not args.test_ground_truth:
            final_code = cj_test_case.replace("//TOFILL", cj_target_trans_code)
        else:
            final_code = cj_test_case.replace("//TOFILL", cj_target_code)

        if os.path.exists(pass_path) or os.path.exists(failure_path) \
            or os.path.exists(cj_target_translation_fixed_path) \
            or os.path.exists(error_final_path): # or os.path.exists(os.path.join(dir_path , "error_0.txt")) \
            continue

        pass_test = False
        if args.auto_fix:
            fix_steps = args.fix_steps
            if fix_steps is None:
                fix_steps = "simple,rule,llm"
            fix_steps = fix_steps.split(",")
            cur_fix_step = 0

            last_code = None
            fix_method = fix_steps[cur_fix_step]
            for try_i in range(8):
                if not have_compilation_error(final_code):
                    pass_test = True
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
                    fixed_final_code, details = ai_fix_cj(
                        final_code,
                        error_messages,
                        doc_path="raw_data/cangjie_documents/tutorial",
                    )
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
                                json.dumps(details, ensure_ascii=False),
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
        else:
            if not have_compilation_error(final_code):
                pass_test = True

        if not pass_test:
            cj_compile_output, cj_output = compile_and_run_cj_single(final_code)
            cj_compile_output = remove_color_codes(cj_compile_output)
            write_to_file(error_path.replace(".txt", f"_final.txt"), "\n==========\n".join(["final", final_code, cj_compile_output, "None"]))

            print(f"This file contains error(s): {cj_target_translation_path}")
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

        # Run and Compare
        java_compile_output, java_output = compile_and_run_java(
            test_case=read_file(java_test_path),
            target_function=read_file(java_target_path),
        )
        cj_compile_output, cj_output = compile_and_run_cj_single(final_code)

        if java_output is not None and cj_output is not None:
            if java_output.strip() == cj_output.strip():
                correct_num += 1
                correct_paths.append(cj_target_translation_path)
                write_to_file(pass_path, cj_output)
            else:
                write_to_file(failure_path, java_output + "\n==========\n" + cj_output)

    print(f"Error Number: {error_num}\nExecution Number: {execution_num}\nExecution Correct Number: {correct_num}\nTotal Number: {total_num}")


if __name__ == "__main__":
    main()
