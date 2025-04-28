import json
import os

import tqdm
from cjtrans.lang.syntax.java_check import get_java_code_errors, is_valid_java_code
from cjtrans.lm_inference import ModelPredictor

import re

from cjtrans.utils.hash_utils import calculate_md5
from cjtrans.utils.jsonl_utils import read_jsonl
from cjtrans.utils.md_utils import extract_code_block


def code_trans(predictor, source: str, target: str="Java"):
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Follow the user's exact instructions."},
        {"role": "user", "content": f"""Here is a Code Translation task.
Please convert this code to {target} accurately. Please preserve the original structure and comments of the code, including the copyright comments in the file header.
Please maintain the 'super' and 'extends' bounds for the generic type <T> of a Java generic class.
In Cangjie, integer literals are default to Int64 type. You should translate them as "long" in Java. For example, both "var counter = 0" and "let a = 1" would be Int64, and type conversion is required when passing it to Int32.
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
```java
/*
 * LICENSE: 3-Clause BSD
 * https://benchmarksgame-team.pages.debian.net/benchmarksgame/license.html
 */
import java.util.*;
import java.lang.*;
import java.util.Optional;

public class BINARY_SEARCH {{
    static int f_gold (int arr[],int l ,int r ,int x) {{
        if (r >= l) {{
            int mid = l + ( r - l ) / 2;
            if (arr[mid] == x) return mid;
            if (arr[mid] > x) return f_gold(arr, l,mid - 1, x);
            return f_gold(arr, mid + 1 ,r ,x ); // Output the result
        }}
        return -1;
    }}
}}

public class Node<K extends Hashable & Equatable<K>, V> {{
    private Optional<K> key;
    private Optional<V> value;
    public Node() {{
        this.key = Optional.empty();
        this.value = Optional.empty();
    }}
    public Node(K key, V value) {{
        this.key = Optional.of(key);
        this.value = Optional.of(value);
    }}
    public Optional<K> getKey() {{
        return key;
    }}
    public Optional<V> getValue() {{
        return value;
    }}
}}
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
    predictor = ModelPredictor('Qwen/Qwen2.5-72B-Instruct')

    in_path = "raw_data/cangjie_gitee_codes.json/cangjie.json"
    out_path = "datasets/generated_java/"
    dataset = read_jsonl(in_path)
    
    out_dataset = []

    for i, data in enumerate(tqdm.tqdm(dataset[:])):
        data_hash = calculate_md5(data["content"])
        print(f"Hash md5: {data_hash}")
        sub_dir = data_hash[:2]
        code_dir = os.path.join(out_path, sub_dir, data_hash)
        data_path = os.path.join(code_dir, "data.json")
        java_path = os.path.join(code_dir, "code.java")
        cj_path = os.path.join(code_dir, "code.cj")
        errors_path = os.path.join(code_dir, "errors.json")
        if os.path.exists(java_path):
            continue
        content = data["content"]
    
        out_code = code_trans(predictor, content, "java")
        if out_code is None:
            continue
        data["trans_java_raw"] = out_code
        data["trans_java"] = extract_code_block(out_code)
        out_dataset.append(data)

        if not os.path.exists(code_dir):
            os.makedirs(code_dir, exist_ok=True)

        if data["trans_java"] is None:
            with open(errors_path, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "type": "OutputMarkdownExtractionError",
                    "message": "",
                    "code": None,
                }))
        else:
            java_errors = get_java_code_errors(data["trans_java"])
            if java_errors is not None:
                with open(errors_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "type": "JavaCodeParseError",
                        "message": java_errors,
                        "code": data["trans_java"],
                    }))
                print("Invalid Java Code")
                data["trans_java"] = None

        if data["trans_java"] is not None:
            with open(java_path, "w", encoding="utf-8") as f:
                f.write(data["trans_java"])
        with open(cj_path, "w", encoding="utf-8") as f:
            f.write(data["content"])
        with open(data_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data))

if __name__ == "__main__":
    
    main()
