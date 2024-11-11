"""
This script is used to check the test results of the cangjie dataset.
"""

import argparse
import os
import json
import pandas as pd
from typing import Dict, List
from matplotlib.colors import LinearSegmentedColormap
IGNORE_FAILURE_PATH_PATTERN = "results/gt_failure_list.json"
if os.path.exists(IGNORE_FAILURE_PATH_PATTERN):
    IGNORE_FAILURE_LIST = json.load(open(IGNORE_FAILURE_PATH_PATTERN, "r", encoding="utf-8"))
else:
    IGNORE_FAILURE_LIST = []

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


def check_test_results(directory_pattern: str) -> None:
    """
    This function is used to check the test results of the cangjie dataset.
    """
    test_case_statistics: Dict[str, List[int]] = {}
    test_case_fix_num: Dict[str, int] = {}
    for root, dirs, files in os.walk(directory_pattern):
        for file in files:
            print(root, file)
            if os.path.basename(root) in IGNORE_FAILURE_LIST:
                continue
            if file.endswith('java_target.java'):
                failure_result = os.path.join(root, 'failure.txt')
                pass_result = os.path.join(root, 'pass.txt')
                
                if not os.path.exists(failure_result) and not os.path.exists(pass_result):
                    continue
                
                # get error fix number
                fix_num = 0
                simple_num = 0
                while fix_num < 11:
                    error_log = os.path.join(root, f'error_{fix_num}.txt')

                    if os.path.exists(error_log):
                        # read error_log
                        with open(error_log, 'r', encoding='utf-8') as f:
                            error_content = f.read()
                        if "simple_based" in error_content:
                            fix_num += 1
                            simple_num += 1
                            continue
                    else:
                        break
                    
                    fix_num += 1
                
                fix_num = fix_num - simple_num
                
                dir_name = os.path.basename(root)
                
                test_case_fix_num[dir_name] = fix_num
                
                # if has failure.txt, then check if the file is in the failure.txt
                if os.path.exists(failure_result):
                    with open(failure_result, 'r', encoding='utf-8') as f:
                        failure_content = f.read()

                    # split by '=========='
                    failure_parts = failure_content.split('==========')
                    if len(failure_parts) != 2:
                        print(f"Error: failure.txt is not in the correct format in {os.path.join(root, file)}")
                        continue
                    
                    java_outputs = failure_parts[0].strip()
                    cangjie_outputs = failure_parts[1].strip()

                    java_lines = java_outputs.splitlines()
                    cangjie_lines = cangjie_outputs.splitlines()

                    # if 'exception' in line.lower() or 'at ' in line.lower(), replace line as '<Exception>'
                    for i, line in enumerate(java_lines):
                        if 'exception' in line.lower() or 'at ' in line.lower():
                            java_lines[i] = '<Exception>'

                    for i, line in enumerate(cangjie_lines):
                        if 'exception' in line.lower() or 'at ' in line.lower():
                            cangjie_lines[i] = '<Exception>'
                    
                    # remove 'Wrong input' lines
                    java_lines = [line for line in java_lines if "Wrong input" not in line]
                    cangjie_lines = [line for line in cangjie_lines if "Wrong input" not in line]
                    
                    # Merge contigous <Exception> lines as one line
                    java_lines = merge_exception_lines(java_lines)
                    cangjie_lines = merge_exception_lines(cangjie_lines)
                    
                    # get dir name from root
                    if dir_name not in test_case_statistics:
                        test_case_statistics[dir_name] = []
                    
                    # check pass number
                    max_case = max(len(java_lines), len(cangjie_lines))
                    for i in range(max_case):
                        if i < len(java_lines) and i < len(cangjie_lines):
                            if java_lines[i].strip() == cangjie_lines[i].strip():
                                test_case_statistics[dir_name].append(1)
                            else:
                                test_case_statistics[dir_name].append(0)
                        elif i < len(java_lines):
                            test_case_statistics[dir_name].append(0)
                        else:
                            test_case_statistics[dir_name].append(1)
                elif os.path.exists(pass_result):
                    with open(pass_result, 'r', encoding='utf-8') as f:
                        pass_content = f.read()

                    output_lines = pass_content.splitlines()
                    for line in output_lines:
                        if 'exception' in line.lower() or 'at ' in line.lower():
                            output_lines[i] = '<Exception>'
                    
                    output_lines = merge_exception_lines(output_lines)
                    
                    # get dir name from root
                    if dir_name not in test_case_statistics:
                        test_case_statistics[dir_name] = []
                    
                    # check pass number
                    for i in range(len(output_lines)):
                        test_case_statistics[dir_name].append(1)        

                if len(test_case_statistics[dir_name]) > 10:
                    test_case_statistics[dir_name] = test_case_statistics[dir_name][:10]
    # print test case statistics
    # for dir_name, cases in test_case_statistics.items():
    #     print(f"{dir_name}: {cases}")
    
    # plot test case statistics
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    
    plt.rcParams['font.family'] = 'Times New Roman'

    # Convert test_case_statistics to a DataFrame
    # All arrays must be of the same length
    max_length = max([len(cases) for cases in test_case_statistics.values()])
    for dir_name, cases in test_case_statistics.items():
        test_case_statistics[dir_name] = cases + [0] * (max_length - len(cases))
    
    # sort by key (test case name)
    test_case_statistics = dict(sorted(test_case_statistics.items()))
    
    # Plot heatmap
    # rename test case as 1, 2, 3, ..., 10
    renamed_test_case_statistics = {}
    for i, dir_name in enumerate(test_case_statistics.keys()):
        pass_vec = test_case_statistics[dir_name]
        new_pass_vec = []
        for x in pass_vec:
            if x == 0:
                new_pass_vec.append(-1)
            else:
                new_pass_vec.append(test_case_fix_num[dir_name])
        renamed_test_case_statistics[f'{i+1}'] = new_pass_vec
    
    """
    Draw Repair Attempts
    """
    all_repair_attempts = list(set(test_case_fix_num.values()))
    all_repair_attempts.sort()

    repair_attempt_counts = {attempt: 0 for attempt in all_repair_attempts}

    for attempt in test_case_fix_num.values():
        repair_attempt_counts[attempt] += 1

    df_repair_attempts = pd.DataFrame(list(repair_attempt_counts.items()), columns=['Repair Attempts', 'Count'])

    plt.figure(figsize=(3.5, 2.5))
    sns.barplot(x='Repair Attempts', y='Count', data=df_repair_attempts, color='steelblue')
    plt.xlabel('Repair Attempts')
    plt.ylabel('Count')
    plt.savefig('figures/repair_attempts.pdf')
    
    """
    Draw pass/fail of test cases
    """
    # if use color to represent the fix number, then use the following code
    # use the test_case_fix_num to represent the color
    df = pd.DataFrame(renamed_test_case_statistics)
    plt.figure(figsize=(10, 2.5))
    colors = ['#fcc06f'] + [plt.cm.Blues(i / 10) for i in range(10)]
    cmap = LinearSegmentedColormap.from_list('custom_cmap', colors)

    sns.heatmap(df, annot=False, fmt='d', cmap=cmap, cbar_kws={'label': 'Repair Attempts'})
    # plt.title('Test Case Statistics')
    plt.xlabel('Problem ID')
    plt.ylabel('Pass/Fail of Test Cases')
    
    plt.savefig('figures/test_case_statistics.pdf')
    
    
    """
    Draw pass rate of test cases
    """
    # Calculate pass rate
    pass_rate = {}
    for dir_name, cases in test_case_statistics.items():
        pass_rate[dir_name] = sum(cases) / len(cases)
    
    # Plot histplot()：直方图，和上面统一配色
    plt.figure(figsize=(3.5, 2.5))
    sns.histplot(pass_rate, cumulative=False, color='steelblue')
    # plt.title('Pass Rate')
    plt.xlabel('Pass Rate')
    plt.ylabel('Count')
    plt.savefig('figures/pass_rate.pdf')
    
    
def main():
    """
    This function is used to check the test results of the cangjie dataset.
    """
    parser = argparse.ArgumentParser(description="Check test results of cangjie dataset")
    parser.add_argument('directory_pattern', type=str, help="The directory pattern for cangjie files, e.g., 'results/rq1_cangjie_para_out/'")
    args = parser.parse_args()
    check_test_results(args.directory_pattern)

if __name__ == "__main__":
    main()