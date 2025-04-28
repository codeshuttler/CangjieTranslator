import glob
import json
import os
import random
import re
import datasets
import pandas as pd
import tqdm

from cjtrans.utils.cj_utils import remove_comments
from cjtrans.utils.dataset_utils import save_to_dick
from cjtrans.utils.jsonl_utils import write_jsonl


PROMPT_LIST = [
    "",
    "Here is a snippet of cangjie code:",
    "Here is a piece of Cangjie code.",
    "Here is an example of Cangjie code.",
    "This is a code snippet for the Cangjie Language.",
    "The following code demonstrates the Cangjie Language.",
    "Here is a section of Cangjie code.",
    "Below is a block of Cangjie code.",
    "Presented below is a snippet of Cangjie code.",
    "The following code represents the Cangjie.",
    "Enclosed herewith is a sample of Cangjie code.",
    "Here you can find a snippet showcasing Cangjie code.",
    "This snippet illustrates the usage of Cangjie language.",
    "Displayed here is a snippet of text in Cangjie code.",
    "The subsequent text presents a Cangjie code snippet.",
    "Referenced below is a concise Cangjie code sample.",
    "Following is a compact Cangjie code excerpt.",
    "Provided below is a brief Cangjie code demonstration.",
    "Here you'll find an example of Cangjie script.",
    "This block showcases the Cangjie language in action.",
    "The code snippet below highlights Cangjie language.",
    "Here's a demonstration of Cangjie script usage.",
    "Presented here is a brief excerpt of Cangjie code.",
    "This snippet showcases the Cangjie input method.",
    "Here you can see a Cangjie language example.",
    "The following text displays a Cangjie code snippet.",
    "The Cangjie script below provides a quick example.",
    "Displayed below is a practical Cangjie coding example.",
    "下面是一段仓颉（cangjie）代码: ",
    "下面是一段仓颉语言的代码: ",
    "以下是一个仓颉代码示例：",
    "这里展示了一段仓颉代码：",
    "这是仓颉代码的一个片段：",
    "这个示例演示了仓颉代码。",
    "这段代码展示了Cangjie语言",
    "这里有一段仓颉代码。",
    "以下是一块仓颉代码。",
    "以下是一块仓颉代码: ",
    "下面展示了一段仓颉代码片段。",
    "以下是Cangjie的代码。",
    "这里附上了一个仓颉代码示例。",
    "这里有一个Cangjie代码片段：",
    "这里有一个仓颉代码片段：",
    "这是一个Cangjie代码示例。",
]


def main():
    random.seed(43)
    out_dataset = []
    files = list(glob.glob("datasets/generated_java/*/*/data.json"))
    for file in tqdm.tqdm(files):
        with open(file, "r", encoding="utf-8") as f:
            raw_data = json.loads(f.read())

        code = raw_data["content"]
        code_no_comments = remove_comments(raw_data["content"])

        prompt_str = random.choice(PROMPT_LIST)
        if random.random() > 0.5:
            prompt_str += "\n"
        if random.random() > 0.2:
            out_dataset.append({"text": f"{prompt_str}```cangjie\n{code}```\n"})
        else:
            out_dataset.append({"text": code})
        prompt_str = random.choice(PROMPT_LIST)
        if random.random() > 0.5:
            prompt_str += "\n"
        if random.random() > 0.2:
            out_dataset.append({"text": f"{prompt_str}```cangjie\n{code_no_comments}```\n"})
        else:
            out_dataset.append({"text": code_no_comments})

    write_jsonl(out_dataset, "datasets/pretrain_dataset.jsonl")
if __name__ == "__main__":
    main()
