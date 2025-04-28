import json
import os
import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer


import re
import argparse

from cjtrans.utils.hash_utils import calculate_md5
from cjtrans.utils.md_utils import contains_chinese

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-72B-Instruct")
    parser.add_argument("--input", type=str, default="results/sft_dataset.jsonl")
    parser.add_argument("--output", type=str, default="results/sft_dataset_cleaned.jsonl")
    parser.add_argument("--export", type=str, default="results/clean_java/code/")
    args = parser.parse_args()
    
    dataset = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            dataset.append(json.loads(line))

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.padding_side = 'left'
    tokenizer.pad_token = tokenizer.unk_token

    out_dataset = []
    for data in tqdm.tqdm(dataset):
        messages = data["messages"]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = tokenizer([text], return_tensors="pt")
        n_tokens = model_inputs.input_ids.shape[1]
        if n_tokens > 4096:
            continue
        elif "raw" in data:
            raw = data["raw"]
            language = None
            translated_code = None
            if "trans_java" in raw:
                translated_code = raw["trans_java"]
                language = "java"
            elif "trans_python" in raw:
                translated_code = raw["trans_python"]
                language = "python"
            elif "trans_cpp" in raw:
                translated_code = raw["trans_cpp"]
                language = "cpp"
            else:
                raise Exception("No translation found")
            content_code = raw["content"]
            
            if len(translated_code.strip()) < 10 or len(content_code.strip()) < 10:
                continue
            if translated_code.count("\n") < 5 or content_code.count("\n") < 5:
                continue
            if language == "java":
                if "class" not in translated_code:
                    continue
                if "var" not in content_code and "let" not in content_code and "class" not in content_code and "func" not in content_code:
                    continue
                if not contains_chinese(content_code) and contains_chinese(translated_code):
                    continue
                if "// Implementation" in translated_code and "// Implementation" not in content_code:
                    continue
                if "extends" not in translated_code and "<:" in content_code:
                    continue
            elif language == "cpp":
                if "var" not in content_code and "let" not in content_code and "class" not in content_code and "func" not in content_code:
                    continue
                if not contains_chinese(content_code) and contains_chinese(translated_code):
                    continue
                if "// Implementation" in translated_code and "// Implementation" not in content_code:
                    continue
            elif language == "python":
                if "var" not in content_code and "let" not in content_code and "class" not in content_code and "func" not in content_code:
                    continue
                if not contains_chinese(content_code) and contains_chinese(translated_code):
                    continue
            out_dataset.append(data)
        else:
            out_dataset.append(data)

    for data in out_dataset:
        if "raw" not in data:
            continue
        data_hash = calculate_md5(data["raw"]["content"])
        dir_path = os.path.join(args.export, data_hash)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        if "trans_java" in data["raw"] and data["raw"]["trans_java"] is not None:
            with open(os.path.join(dir_path, "code.java"), "w", encoding="utf-8") as f:
                f.write(data["raw"]["trans_java"])
        if "trans_python" in data["raw"] and data["raw"]["trans_python"] is not None:
            with open(os.path.join(dir_path, "code.py"), "w", encoding="utf-8") as f:
                f.write(data["raw"]["trans_python"])
        if "trans_cpp" in data["raw"] and data["raw"]["trans_cpp"] is not None:
            with open(os.path.join(dir_path, "code.cpp"), "w", encoding="utf-8") as f:
                f.write(data["raw"]["trans_cpp"])
        with open(os.path.join(dir_path, "code.cj"), "w", encoding="utf-8") as f:
            f.write(data["raw"]["content"])
        with open(os.path.join(dir_path, "data.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(data))

    with open(args.output, "w", encoding="utf-8") as f:
        for data in out_dataset:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()