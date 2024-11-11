import argparse
import json
import random
import datasets
import pandas as pd

from cjtrans.utils.dataset_utils import save_to_dick


def main(input_path: str, output_path: str, test_ratio: float, valid_ratio: float):
    random.seed(43)
    with open(input_path, "r") as file:
        data = [json.loads(line) for line in file]

    df = pd.DataFrame.from_records(data)

    hf_dataset_raw = datasets.Dataset.from_pandas(df)
    if test_ratio+valid_ratio == 0:
        train_testvalid = {
            "train": hf_dataset_raw,
            "test": [],
        }
    else:
        train_testvalid = hf_dataset_raw.train_test_split(test_size=test_ratio+valid_ratio)
    
    if test_ratio == 0:
        test_valid = {
            "train": train_testvalid["train"],
            "test": [],
        }
    else:
        test_valid = train_testvalid["test"].train_test_split(
            test_size=test_ratio / (test_ratio+valid_ratio)
        )

    save_path = output_path

    hf_dataset = datasets.DatasetDict(
        {
            "train": train_testvalid["train"],
            "test": test_valid["test"],
            "valid": test_valid["train"],
        }
    )
    save_to_dick(hf_dataset, save_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("input_path", type=str, help="Input JSONL file path")
    parser.add_argument("output_path", type=str, help="Output path for the dataset")
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.1,
        help="Ratio for the test set (default: 0.1)",
    )
    parser.add_argument(
        "--valid-ratio",
        type=float,
        default=0.1,
        help="Ratio for the validation set (default: 0.1)",
    )
    args = parser.parse_args()

    main(args.input_path, args.output_path, args.test_ratio, args.valid_ratio)
