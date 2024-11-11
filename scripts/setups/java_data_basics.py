import sys
import os
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
)

from cjtrans.metrics.java.function_loc import count_function_loc
from cjtrans.metrics.java.cyclomatic_complexity import get_cyclomatic_complexity
from cjtrans.metrics.java.function_parameters import count_function_parameters
from cjtrans.metrics.java.loc import get_loc

import argparse
import os
import glob
import statistics
import pandas as pd
from tqdm import tqdm

def calculate_statistics(values):
    return {
        'min': min(values),
        'max': max(values),
        'mean': statistics.mean(values),
        'median': statistics.median(values)
    }

def process_java_files(directory_pattern: str, output_file: str):
    loc_values = []
    funcloc_values = []
    cc_values = []
    param_values = []

    java_files = glob.glob(directory_pattern)

    for java_file in tqdm(java_files, desc="Processing files"):
        with open(java_file, 'r', encoding='utf-8') as file:
            code = file.read()

            loc = get_loc(code)
            func_loc = count_function_loc(code)
            cc = get_cyclomatic_complexity(code)
            params = count_function_parameters(code)

            loc_values.append(loc)
            funcloc_values.extend(func_loc)
            cc_values.extend(cc)
            param_values.extend(params)

    loc_stats = calculate_statistics(loc_values)
    floc_stats = calculate_statistics(funcloc_values)
    cc_stats = calculate_statistics(cc_values)
    param_stats = calculate_statistics(param_values)

    df = pd.DataFrame({
        'Metric': ['#LOC', '#FLOC', 'Complexity' , '#Parameters'],
        'Min': [loc_stats['min'], floc_stats['min'], cc_stats['min'], param_stats['min']],
        'Max': [loc_stats['max'], floc_stats['max'], cc_stats['max'], param_stats['max']],
        'Mean': [loc_stats['mean'], floc_stats['mean'], cc_stats['mean'], param_stats['mean']],
        'Median': [loc_stats['median'], floc_stats['median'], cc_stats['median'], param_stats['median']]
    })

    df.to_csv(output_file, index=False)
    print(f"Statistics saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Process Java files and compute metrics")
    parser.add_argument('directory_pattern', type=str, help="The file path pattern for Java files, e.g., 'results/cangjie_para_out/*/java_target.java'")
    parser.add_argument('--output', type=str, help="The output file path for cangjie files, e.g., 'cangjie_metrics_statistics.csv'", default="java_metrics_statistics.csv")
    
    args = parser.parse_args()

    process_java_files(args.directory_pattern, args.output)

if __name__ == "__main__":
    main()