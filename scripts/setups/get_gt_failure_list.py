
"""
This script is used to get the ground truth failure list from the cangjie dataset.
"""

import os
import json
import argparse
import glob
from typing import List
def get_gt_failure_list(dataset_path: str) -> List[str]:
    """
    This function is used to get the ground truth failure list from the cangjie dataset.
    """

    failure_list = []
    for failure_file in glob.glob(dataset_path):
        failure_list.append(os.path.basename(os.path.dirname(failure_file)))
    return failure_list

def main():
    parser = argparse.ArgumentParser(description="Get the ground truth failure list from the cangjie dataset.")
    parser.add_argument("--path-pattern", type=str, help="The path pattern to the cangjie dataset.", default="results/cangjie_para_gt/*/failure.txt")
    parser.add_argument("--output_path", type=str, help="The path to the output file.", default="results/gt_failure_list.json")
    args = parser.parse_args()
    gt_failure_list = get_gt_failure_list(args.path_pattern)
    with open(args.output_path, "w") as f:
        json.dump(gt_failure_list, f)

if __name__ == "__main__":
    main()
