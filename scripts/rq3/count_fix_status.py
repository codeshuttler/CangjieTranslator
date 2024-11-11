import sys
import os
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
)

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
plt.rcParams['font.family'] = 'Times New Roman'

from typing import Dict, List, Any
import os
import argparse
import json
from cjtrans.lang.syntax.cj_check import check_cj, parse_error, parse_error_messages

IGNORE_FAILURE_PATH_PATTERN = "results/gt_failure_list.json"
if os.path.exists(IGNORE_FAILURE_PATH_PATTERN):
    IGNORE_FAILURE_LIST = json.load(open(IGNORE_FAILURE_PATH_PATTERN, "r", encoding="utf-8"))
else:
    IGNORE_FAILURE_LIST = []

def fix_statistics_single_dir(path: str):
    fix_statistics: Dict[str, Dict[str, Any]] = {}
    for root, dirs, files in os.walk(path):
        for file in files:
            # print(root, file)
            dir_name = os.path.basename(root)
            if dir_name in IGNORE_FAILURE_LIST:
                continue
            if file.endswith('java_target.java'):
                
                fixed_file = os.path.join(root, f'cj_target_translation_fixed.cj')
                # get error fix number
                fix_data = {
                    "steps": [],
                    "is_fixed": [],
                }
                for fix_num in range(11):
                    error_log = os.path.join(root, f'error_{fix_num}.txt')

                    if os.path.exists(error_log):
                        # read error_log
                        with open(error_log, 'r', encoding='utf-8') as f:
                            error_content = f.read()
                        
                        parts = error_content.split("==========")
                        errors = parse_error_messages(parts[2])
                        error_messages = []
                        for error in errors:
                            error_msg, error_file, error_row, error_col, error_details = parse_error(error)
                            error_messages.append((error_msg, error_file, error_row, error_col, error_details))

                        if "simple_based" in error_content:
                            fix_data["steps"].append({
                                "method": "simple",
                                "error_messages": error_messages,
                            })
                            continue
                        if "rule_based" in error_content:
                            fix_data["steps"].append({
                                "method": "rule",
                                "error_messages": error_messages,
                            })
                            continue
                        if "llm_based" in error_content:
                            fix_data["steps"].append({
                                "method": "llm",
                                "error_messages": error_messages,
                            })
                            continue
                    else:
                        break
                fix_data["is_fixed"] = os.path.exists(fixed_file)
                fix_statistics[dir_name] = fix_data
    return fix_statistics

def count_fix_status(input_path: str):
    if "," in input_path:
        input_paths = input_path.split(",")
    else:
        input_paths = [input_path]
    fix_statistics: Dict[str, Dict[str, Any]] = {}
    for each_input_path in input_paths:
        each_dir_fix_statistics = fix_statistics_single_dir(each_input_path)
        fix_statistics.update(each_dir_fix_statistics)

    # Draw error count change
    error_count_change = {
        "Method": [],
        "Delta": [],
        "Fixed": [],
    }
    
    for data in fix_statistics.values():
        for step_idx, step in enumerate(data["steps"]):
            if step["method"] == "simple":
                continue
            if step_idx == 0:
                continue
            if step["method"] == "rule":
                method = "Rule"
            else:
                method = "LLM"
            error_count_change["Method"].append(method)
            error_count_change["Delta"].append(len(step["error_messages"]) - len(data["steps"][step_idx - 1]["error_messages"]))
            error_count_change["Fixed"].append(data["is_fixed"])
    
    df = pd.DataFrame(error_count_change)
    sns.set_theme(rc={'figure.figsize':(3.5, 2.5)})
    sns.set_style("whitegrid")
    sns.barplot(data=df, x="Method", y="Delta", hue="Fixed", estimator="mean", errorbar=("ci", 95))
    plt.title('Error Count Change')
    plt.xlabel('Method')
    plt.ylabel('Error Count Change')
    plt.savefig('figures/error_count_change.pdf')
    
    # clear
    plt.clf()
    
    # Draw the fix reason count
    fix_reason_count = {
        "Rule": 0,
        "Rule+LLM": 0,
        "Failure": 0,
    }
    for data in fix_statistics.values():
        if any([step["method"] == "llm" for step in data["steps"]]):
            if not data["is_fixed"]:
                fix_reason_count["Failure"] += 1
            else:
                fix_reason_count["Rule+LLM"] += 1
        else:
            if not data["is_fixed"]:
                fix_reason_count["Failure"] += 1
            else:
                fix_reason_count["Rule"] += 1

    # fix_reason_count.pop("Failure")
    # draw with seaborn
    df = pd.DataFrame(fix_reason_count, index=["Rule", "Rule+LLM", "Rule-Failure", "Rule+LLM-Failure"])
    sns.set_theme(rc={'figure.figsize':(3.5, 2.5)})
    sns.set_style("whitegrid")
    sns.barplot(data=df, errorbar=None)
    plt.title('Fix Reason Count')
    plt.xlabel('Reason')
    plt.ylabel('Count')
    plt.savefig('figures/fix_reason_count.pdf')
    
    # clear
    plt.clf()

    fix_count = {
        "method": [],
        "fix_num": [],
        "is_fixed": [],
    }
    for method, data in fix_statistics.items():
        for step_method in ["rule", "llm"]:
            if len([step for step in data["steps"] if step["method"] == step_method]) == 0:
                continue
            if step_method == "rule":
                method = "Rule"
            else:
                method = "LLM"
            fix_count["method"].append(method)
            fix_count["fix_num"].append(len([step for step in data["steps"] if step["method"] == step_method]))
            fix_count["is_fixed"].append(data["is_fixed"])

    # draw with seaborn
    df = pd.DataFrame(fix_count)
    sns.set_theme(rc={'figure.figsize':(3.5, 2.5)})
    sns.set_style("whitegrid")
    sns.barplot(
        data=df,
        x="method",
        y="fix_num",
        hue="is_fixed",
        errorbar=("ci", 95),
    )
    plt.title('Fix Count by Method')
    plt.xlabel('Method')
    plt.ylabel('Fix Number')
    plt.legend(title='Is Fixed')
    plt.savefig('figures/fix_count_by_method.pdf')
    
    # clear
    plt.clf()

def main():
    parser = argparse.ArgumentParser(description="Count the fix status of the dataset")
    parser.add_argument("--input", type=str, required=True, help="The input dataset path")
    args = parser.parse_args()
    
    count_fix_status(args.input)


if __name__ == "__main__":
    main()
