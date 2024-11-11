
import os
import tqdm
from cjtrans.utils.file_utils import write_to_file
from cjtrans.utils.md_utils import extract_code_block
import datasets

DUMMY_CANGJIE_TEST = """
from std import collection.*
from std import sort.*
from std import math.*

//TOFILL
main() {
    println("hello world!")
}
"""

if __name__ == "__main__":
    OUTPUT_PATH = "raw_data/leetcode_nonpara"
    leetcode = datasets.load_dataset("greengerong/leetcode")
    train_dataset = leetcode["train"]
    for data in tqdm.tqdm(train_dataset):
        slug = data["slug"]
        java_code = data["java"].lstrip()
        if java_code.startswith("```java\n"):
            java_code = extract_code_block(java_code)

        save_dir = os.path.join(OUTPUT_PATH, slug)
        cj_translation_path = os.path.join(save_dir, "cj_target_translation.cj")
        cj_test_path = os.path.join(save_dir, "cj_test.cj")
        java_target_path = os.path.join(save_dir, "java_target.java")

        os.makedirs(save_dir, exist_ok=True)
        write_to_file(java_target_path, java_code)
        write_to_file(cj_test_path, DUMMY_CANGJIE_TEST)
        
