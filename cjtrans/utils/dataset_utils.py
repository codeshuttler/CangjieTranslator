
import json
import os
import datasets
def save_to_dick(dataset: datasets.DatasetDict, save_path: str, format: str="jsonl"):
    data_path = os.path.join(save_path, "data")
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    
    for split in dataset.keys():
        split_path = os.path.join(data_path, split)
        if not os.path.exists(split_path):
            os.makedirs(split_path)
        
        if format == "jsonl":
            jsonl_file_path = os.path.join(split_path, "data.jsonl")
            with open(jsonl_file_path, "w", encoding="utf-8") as f:
                for row in dataset[split]:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
        else:
            raise Exception(f"Invalid Dataset Format {format}")
