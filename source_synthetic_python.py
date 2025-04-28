import json
import os

import tqdm
from cjtrans.lang.syntax.python_check import check_grammar
from cjtrans.lm_inference import ModelPredictor

import re

from cjtrans.utils.hash_utils import calculate_md5
from cjtrans.utils.jsonl_utils import read_jsonl
from cjtrans.utils.md_utils import extract_code_block


def code_trans(predictor, source: str, target: str="Python"):
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Follow the user's exact instructions."},
        {"role": "user", "content": f"""Here is a Code Translation task.
Please convert this code to {target} accurately. Please preserve the original structure and comments of the code, including the copyright comments in the file header.
There is no limit on the length of output, regardless of complexity. Please provide the complete converted result of the code.
Source: ```cangjie
/*
 * LICENSE: 3-Clause BSD
 * https://benchmarksgame-team.pages.debian.net/benchmarksgame/license.html
 */
from std import collection.*
func f_gold (arr:Array<Int32>, l:Int32, r:Int32, x:Int32):Int32{{
    if (r >= l){{
        var mid = l + ( r - l ) / 2 
        if ( arr [ Int64(mid) ] == x ) {{return mid}}
        if ( arr [ Int64(mid) ] > x ) {{return f_gold ( arr , l , mid - 1 , x )}}
        return f_gold ( arr , mid + 1 , r , x ) // Output the result
    }}
    return -1
}}

public open class Node<K, V> where K <: Hashable & Equatable<K> {{
    public var key: Option<K> = Option<K>.None
    public var value: Option<V> = Option<V>.None
    public init() {{}}
    public init(key: K, value: V) {{
        this.key = Option<K>.Some(key)
        this.value = Option<V>.Some(value)
    }}
}}
```
Output:
```python
# LICENSE: 3-Clause BSD
# https://benchmarksgame-team.pages.debian.net/benchmarksgame/license.html

def f_gold(arr, l, r, x):
    if r >= l:
        mid = l + (r - l) // 2
        if arr[mid] == x:
            return mid
        if arr[mid] > x:
            return f_gold(arr, l, mid - 1, x)
        return f_gold(arr, mid + 1, r, x) # Output the result
    return -1

class Node:
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
```
Source: ```cangjie
{source}
```
Output:
"""}
    ]

    n_token = predictor.token_num(messages)
    print(f"Token Number: {n_token}")
    # if n_token > 4096*2:
    #     return None
    if n_token > 4096:
        return None
    out = predictor.chat(messages, max_new_tokens=4096*2)
    return out

def main():
    predictor = ModelPredictor('Qwen/Qwen2.5-72B-Instruct', device="auto", use_vllm=True)

    in_path = "raw_data/cangjie_gitee_codes.json/cangjie.json"
    out_path = "datasets/generated_python/"
    dataset = read_jsonl(in_path)
    
    out_dataset = []

    for i, data in enumerate(tqdm.tqdm(dataset[:])):
        data_hash = calculate_md5(data["content"])
        print(f"Hash md5: {data_hash}")
        sub_dir = data_hash[:2]
        code_dir = os.path.join(out_path, sub_dir, data_hash)
        data_path = os.path.join(code_dir, "data.json")
        python_path = os.path.join(code_dir, "code.py")
        cj_path = os.path.join(code_dir, "code.cj")
        errors_path = os.path.join(code_dir, "errors.json")
        if os.path.exists(python_path):
            continue
        content = data["content"]
    
        out_code = code_trans(predictor, content, "python")
        if out_code is None:
            continue
        data["trans_python_raw"] = out_code
        data["trans_python"] = extract_code_block(out_code)
        out_dataset.append(data)

        if not os.path.exists(code_dir):
            os.makedirs(code_dir, exist_ok=True)

        if data["trans_python"] is None:
            with open(errors_path, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "type": "OutputMarkdownExtractionError",
                    "message": "",
                    "code": None,
                }))
        else:
            python_has_errors = check_grammar(data["trans_python"])
            if python_has_errors:
                with open(errors_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "type": "PythonCodeParseError",
                        "message": "",
                        "code": data["trans_python"],
                    }))
                print("Invalid Python Code")
                data["trans_python"] = None

        if data["trans_python"] is not None:
            with open(python_path, "w", encoding="utf-8") as f:
                f.write(data["trans_python"])
        with open(cj_path, "w", encoding="utf-8") as f:
            f.write(data["content"])
        with open(data_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data))

if __name__ == "__main__":
    
    main()
