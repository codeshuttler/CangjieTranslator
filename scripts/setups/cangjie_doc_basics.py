
"""
Cangjie Document Basics
"""
import argparse
import glob
import os
from transformers import AutoTokenizer

def process_cangjie_files(directory_pattern):

    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-7B")

    file_count = 0
    total_tokens = 0
    file_paths = glob.glob(directory_pattern)
    
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        tokens = tokenizer.encode(content)
        total_tokens += len(tokens)
        file_count += 1

    print(f"Total files: {file_count}")
    print(f"Total tokens: {total_tokens}")


def main():
    parser = argparse.ArgumentParser(description="Process cangjie files and compute metrics")
    parser.add_argument('directory_pattern', type=str, help="The file path pattern for cangjie files, e.g., 'raw_data/cangjie_documents/*/*.txt'")
    
    args = parser.parse_args()

    process_cangjie_files(args.directory_pattern)

if __name__ == "__main__":
    main()
