import json
import random
import glob
import uuid
import tqdm
import argparse
import ast
import astor


TASK_INSTRUCTIONS_PATH = "resources/sft_prompts/task.json"
SYSTEM_PATH = "resources/sft_prompts/system.json"
LANGUAGE_PATH = "resources/sft_prompts/language.json"

SYSTEM_INSTRUCTIONS = []
CANGJIE_NAME = []
JAVA_NAME = []
CPP_NAME = []
PYTHON_NAME = []
INSTRUCTIONS = []


with open(TASK_INSTRUCTIONS_PATH, "r", encoding="utf-8") as f:
    INSTRUCTIONS = json.loads(f.read())

with open(SYSTEM_PATH, "r", encoding="utf-8") as f:
    SYSTEM_INSTRUCTIONS = json.loads(f.read())

with open(LANGUAGE_PATH, "r", encoding="utf-8") as f:
    LANGUAGE_NAMES = json.loads(f.read())

for name, count in LANGUAGE_NAMES["cangjie"].items():
    CANGJIE_NAME.extend([name] * count)

for name, count in LANGUAGE_NAMES["java"].items():
    JAVA_NAME.extend([name] * count)

for name, count in LANGUAGE_NAMES["cpp"].items():
    CPP_NAME.extend([name] * count)

for name, count in LANGUAGE_NAMES["python"].items():
    PYTHON_NAME.extend([name] * count)

import re

def remove_comments(code: str) -> str:
    s = code
    # Use regular expressions to remove "/*" comments
    pattern = r"/\*.*?\*/"
    s = re.sub(pattern, "", s, flags=re.DOTALL)
    # Use regular expressions to remove "//" comments
    pattern = r"//.*?$"
    s = re.sub(pattern, "", s, flags=re.MULTILINE)

    if random.random() < 0.05:
        return "\n" + s.lstrip()
    return s.lstrip()


def remove_python_comments(code: str) -> str:
    # Parse code to AST
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Fallback to regex method
        # Remove single-line comments
        return re.sub(r'#.*$', '', code)
    
    try:
        # Remove comments
        for node in ast.walk(tree):
            # Remove single line comments
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                node.value.s = ""
            # Remove multi line comments (Docstrings)
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef) or isinstance(node, ast.Module):
                if (isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Str)):
                    node.body[0].value.s = ""
    except IndexError:
        # Fallback to regex method
        # Remove single-line comments
        return re.sub(r'#.*$', '', code)
    
    # AST to source code
    try:
        final_code = astor.to_source(tree)
    except AttributeError:
        # Fallback to regex method
        # Remove single-line comments
        return re.sub(r'#.*$', '', code)
    return final_code

def generate_java_subset(pattern: str, cangjie_percent: float = 0.8, nocomment_percent: float = 0.1, line_threshold: float = 1.5):
    out_dataset = []
    files = list(glob.glob(pattern))
    for file in tqdm.tqdm(files):
        with open(file, "r", encoding="utf-8") as f:
            raw_data = json.loads(f.read())
        if raw_data["trans_java"] is None:
            continue

        inst = random.choice(INSTRUCTIONS)
        if random.random() < cangjie_percent:
            slang: str = random.choice(JAVA_NAME)
            scode: str = raw_data["trans_java"]
            tlang: str = random.choice(CANGJIE_NAME)
            tcode: str = raw_data["content"]
        else:
            slang: str = random.choice(CANGJIE_NAME)
            scode: str = raw_data["content"]
            tlang: str = random.choice(JAVA_NAME)
            tcode: str = raw_data["trans_java"]

        s_lines: int = scode.count("\n")
        t_lines: int = tcode.count("\n")
        # print(s_lines, t_lines)

        if s_lines >= t_lines * line_threshold or t_lines >= s_lines * line_threshold:
            continue
        
        scode_has_header = scode.lstrip().startswith("//") or scode.lstrip().startswith("/*")
        tcode_has_header = tcode.lstrip().startswith("//") or tcode.lstrip().startswith("/*")
        if (scode_has_header and tcode_has_header) or (not scode_has_header and not tcode_has_header):
            data = {
                "id": uuid.uuid4().hex,
                "messages": [],
                "raw": raw_data,
            }
            out_inst = (
                inst.replace("{SOURCE_LANG}", slang)
                .replace("{TARGET_LANG}", tlang)
                .replace("{SOURCE_CODE}", scode)
            )
            if random.random() > 0.5:
                data["messages"].append(
                    {"role": "system", "content": random.choice(SYSTEM_INSTRUCTIONS)}
                )
            data["messages"].append({"role": "user", "content": out_inst})

            data["messages"].append({"role": "assistant", "content": tcode})
            out_dataset.append(data)
        else:
            data = {
                "id": uuid.uuid4().hex,
                "messages": [],
                "raw": raw_data,
            }
            if random.random() > nocomment_percent:
                scode = remove_comments(scode)
                tcode = remove_comments(tcode)
            out_inst = (
                inst.replace("{SOURCE_LANG}", slang)
                .replace("{TARGET_LANG}", tlang)
                .replace("{SOURCE_CODE}", scode)
            )
            if random.random() > 0.5:
                data["messages"].append(
                    {"role": "system", "content": random.choice(SYSTEM_INSTRUCTIONS)}
                )
            data["messages"].append({"role": "user", "content": out_inst})

            data["messages"].append({"role": "assistant", "content": tcode})
            out_dataset.append(data)

    return out_dataset


def generate_python_subset(pattern: str, cangjie_percent: float = 0.8, nocomment_percent: float = 0.1, line_threshold: float = 1.5):
    out_dataset = []
    files = list(glob.glob(pattern))
    for file in tqdm.tqdm(files):
        with open(file, "r", encoding="utf-8") as f:
            raw_data = json.loads(f.read())
        if raw_data["trans_python"] is None:
            continue

        inst = random.choice(INSTRUCTIONS)
        if random.random() < cangjie_percent:
            slang: str = random.choice(PYTHON_NAME)
            scode: str = raw_data["trans_python"]
            tlang: str = random.choice(CANGJIE_NAME)
            tcode: str = raw_data["content"]
        else:
            slang: str = random.choice(CANGJIE_NAME)
            scode: str = raw_data["content"]
            tlang: str = random.choice(PYTHON_NAME)
            tcode: str = raw_data["trans_python"]

        s_lines: int = scode.count("\n")
        t_lines: int = tcode.count("\n")
        # print(s_lines, t_lines)

        if s_lines >= t_lines * line_threshold or t_lines >= s_lines * line_threshold:
            continue
        
        scode_has_header = scode.lstrip().startswith("#") or scode.lstrip().startswith("//") or scode.lstrip().startswith("/*")
        tcode_has_header = tcode.lstrip().startswith("#") or tcode.lstrip().startswith("//") or tcode.lstrip().startswith("/*")
        if (scode_has_header and tcode_has_header) or (not scode_has_header and not tcode_has_header):
            data = {
                "id": uuid.uuid4().hex,
                "messages": [],
                "raw": raw_data,
            }
            out_inst = (
                inst.replace("{SOURCE_LANG}", slang)
                .replace("{TARGET_LANG}", tlang)
                .replace("{SOURCE_CODE}", scode)
            )
            if random.random() > 0.5:
                data["messages"].append(
                    {"role": "system", "content": random.choice(SYSTEM_INSTRUCTIONS)}
                )
            data["messages"].append({"role": "user", "content": out_inst})

            data["messages"].append({"role": "assistant", "content": tcode})
            out_dataset.append(data)
        else:
            data = {
                "id": uuid.uuid4().hex,
                "messages": [],
                "raw": raw_data,
            }
            if random.random() > nocomment_percent:
                if slang in PYTHON_NAME:
                    scode = remove_python_comments(scode)
                else:
                    scode = remove_comments(scode)
                if tlang in PYTHON_NAME:
                    tcode = remove_python_comments(tcode)
                else:
                    tcode = remove_comments(tcode)
            out_inst = (
                inst.replace("{SOURCE_LANG}", slang)
                .replace("{TARGET_LANG}", tlang)
                .replace("{SOURCE_CODE}", scode)
            )
            if random.random() > 0.5:
                data["messages"].append(
                    {"role": "system", "content": random.choice(SYSTEM_INSTRUCTIONS)}
                )
            data["messages"].append({"role": "user", "content": out_inst})

            data["messages"].append({"role": "assistant", "content": tcode})
            out_dataset.append(data)

    return out_dataset


def generate_cpp_subset(pattern: str, cangjie_percent: float = 0.8, nocomment_percent: float = 0.1, line_threshold: float = 1.5):
    out_dataset = []
    files = list(glob.glob(pattern))
    for file in tqdm.tqdm(files):
        with open(file, "r", encoding="utf-8") as f:
            raw_data = json.loads(f.read())
        if raw_data["trans_cpp"] is None:
            continue

        inst = random.choice(INSTRUCTIONS)
        if random.random() < cangjie_percent:
            slang: str = random.choice(JAVA_NAME)
            scode: str = raw_data["trans_cpp"]
            tlang: str = random.choice(CANGJIE_NAME)
            tcode: str = raw_data["content"]
        else:
            slang: str = random.choice(CANGJIE_NAME)
            scode: str = raw_data["content"]
            tlang: str = random.choice(JAVA_NAME)
            tcode: str = raw_data["trans_cpp"]

        s_lines: int = scode.count("\n")
        t_lines: int = tcode.count("\n")
        # print(s_lines, t_lines)

        if s_lines >= t_lines * line_threshold or t_lines >= s_lines * line_threshold:
            continue

        scode_has_header = scode.lstrip().startswith("//") or scode.lstrip().startswith("/*")
        tcode_has_header = tcode.lstrip().startswith("//") or tcode.lstrip().startswith("/*")
        if (scode_has_header and tcode_has_header) or (not scode_has_header and not tcode_has_header):
            data = {
                "id": uuid.uuid4().hex,
                "messages": [],
                "raw": raw_data,
            }
            out_inst = (
                inst.replace("{SOURCE_LANG}", slang)
                .replace("{TARGET_LANG}", tlang)
                .replace("{SOURCE_CODE}", scode)
            )
            if random.random() > 0.5:
                data["messages"].append(
                    {"role": "system", "content": random.choice(SYSTEM_INSTRUCTIONS)}
                )
            data["messages"].append({"role": "user", "content": out_inst})

            data["messages"].append({"role": "assistant", "content": tcode})
            out_dataset.append(data)
        else:
            data = {
                "id": uuid.uuid4().hex,
                "messages": [],
                "raw": raw_data,
            }
            if random.random() > nocomment_percent:
                scode = remove_comments(scode)
                tcode = remove_comments(tcode)
            out_inst = (
                inst.replace("{SOURCE_LANG}", slang)
                .replace("{TARGET_LANG}", tlang)
                .replace("{SOURCE_CODE}", scode)
            )
            if random.random() > 0.5:
                data["messages"].append(
                    {"role": "system", "content": random.choice(SYSTEM_INSTRUCTIONS)}
                )
            data["messages"].append({"role": "user", "content": out_inst})

            data["messages"].append({"role": "assistant", "content": tcode})
            out_dataset.append(data)

    return out_dataset


def main():

    # Get language list from argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--languages", default="java", type=str)
    args = parser.parse_args()

    languages = args.languages.split(",")
    # unique and sort strip lower
    languages = sorted(list(set([lang.strip().lower() for lang in languages])))

    out_dataset = []

    if "java" in languages:
        print("Generating Java dataset...")
        java_dataset = generate_java_subset("datasets/generated_java/*/*/data.json")
        out_dataset.extend(java_dataset)

    if "python" in languages:
        print("Generating Python dataset...")
        python_dataset = generate_python_subset(
            "datasets/generated_python/*/*/data.json"
        )
        out_dataset.extend(python_dataset)

    if "cpp" in languages:
        print("Generating C++ dataset...")
        cpp_dataset = generate_cpp_subset("datasets/generated_cpp/*/*/data.json")
        out_dataset.extend(cpp_dataset)

    out_dataset.extend(
        [
            {
                "id": uuid.uuid4().hex,
                "messages": [
                    {"role": "user", "content": "你知道仓颉编程语言吗？"},
                    {
                        "role": "assistant",
                        "content": "仓颉语言（Cangjie Language）是华为自研的一门编程语言。该语言已经正式开启内测阶段，部分开发者已经获得了仓颉的源代码。仓颉语言并非中文编程语言，与中文没有直接的关联。仓颉的语法类似于Go和Java。该语言的开发旨在为鸿蒙生态基础设施建设提供支持，华为消费者业务软件部总裁龚体表示，仓颉语言将为鸿蒙生态系统的发展提供重要支持。当前仓颉语言仍处于内测阶段，团队和内测成员正在积极改进代码并修复bug。目前，我们还需要等待官方进一步披露有关仓颉语言的详细信息，以便更全面地了解这门编程语言的特性和用途。",
                    },
                ],
            },
            {
                "id": uuid.uuid4().hex,
                "messages": [
                    {"role": "user", "content": "介绍一下仓颉编程语言"},
                    {
                        "role": "assistant",
                        "content": "仓颉语言（Cangjie Language）是华为自研的一门编程语言。该语言已经正式开启内测阶段，部分开发者已经获得了仓颉的源代码。仓颉语言并非中文编程语言，与中文没有直接的关联。仓颉的语法类似于Go和Java。该语言的开发旨在为鸿蒙生态基础设施建设提供支持，华为消费者业务软件部总裁龚体表示，仓颉语言将为鸿蒙生态系统的发展提供重要支持。当前仓颉语言仍处于内测阶段，团队和内测成员正在积极改进代码并修复bug。目前，我们还需要等待官方进一步披露有关仓颉语言的详细信息，以便更全面地了解这门编程语言的特性和用途。",
                    },
                ],
            },
            {
                "id": uuid.uuid4().hex,
                "messages": [
                    {"role": "user", "content": "简单地介绍一下仓颉编程语言"},
                    {
                        "role": "assistant",
                        "content": "仓颉语言（Cangjie Language）是华为自研的一门编程语言。该语言已经正式开启内测阶段，部分开发者已经获得了仓颉的源代码。仓颉语言并非中文编程语言，与中文没有直接的关联。仓颉的语法类似于Go和Java。该语言的开发旨在为鸿蒙生态基础设施建设提供支持，华为消费者业务软件部总裁龚体表示，仓颉语言将为鸿蒙生态系统的发展提供重要支持。当前仓颉语言仍处于内测阶段，团队和内测成员正在积极改进代码并修复bug。目前，我们还需要等待官方进一步披露有关仓颉语言的详细信息，以便更全面地了解这门编程语言的特性和用途。",
                    },
                ],
            },
            {
                "id": uuid.uuid4().hex,
                "messages": [
                    {"role": "user", "content": "仓颉编程语言的特点是什么？"},
                    {
                        "role": "assistant",
                        "content": "仓颉编程语言具有原生智能化、天生全场景，高性能、强安全等特点。从语言规范的制定到实现，以及未来的语言社区都将实现自主可控。仓颉内置了AgentDSL框架，简化了agent协作和符号表达式。仓颉语言使用用户模式线程和并发对象库来简化开发并提高资源利用率，在编译器和运行时都进行了性能优化。此外，还提供了包括调试、静态验证、性能分析和测试的工具。",
                    },
                ],
            },
            {
                "id": uuid.uuid4().hex,
                "messages": [
                    {
                        "role": "user",
                        "content": "Do you know about the Cangjie programming language?",
                    },
                    {
                        "role": "assistant",
                        "content": "Cangjie Language is a programming language developed by Huawei. The language has entered the official beta testing phase, and some developers have already obtained the source code for Cangjie. Cangjie Language is not a programming language based on Chinese, and it has no direct connection to the Chinese language. The syntax of Cangjie is similar to Go and Java. The development of this language aims to provide support for the infrastructure construction of the HarmonyOS ecosystem. Gong Ti, President of Huawei's Consumer Business Software Department, stated that Cangjie Language will provide important support for the development of the HarmonyOS ecosystem. Currently, Cangjie Language is still in the beta testing phase, and the team and beta testers are actively improving the code and fixing bugs. We still need to wait for further official disclosures to gain a more comprehensive understanding of the features and applications of Cangjie Language.",
                    },
                ],
            },
            {
                "id": uuid.uuid4().hex,
                "messages": [
                    {
                        "role": "user",
                        "content": "你可以用仓颉编程语言写一个hello world吗？",
                    },
                    {
                        "role": "assistant",
                        "content": '当然可以！\n```cangjie\nmain(){\n    println("Hello world!")\n}\n```\n上面这段仓颉代码会在控制台输出字符串“Hello world!”。',
                    },
                ],
            },
            {
                "id": uuid.uuid4().hex,
                "messages": [
                    {
                        "role": "user",
                        "content": 'Can you write a "hello world" program in Cangjie programming language?',
                    },
                    {
                        "role": "assistant",
                        "content": 'Certainly!\n```cangjie\nmain(){\n    println("Hello world!")\n}\n```\nThe above Cangjie code will output the string "Hello world!" to the console.',
                    },
                ],
            },
        ]
    )
    with open(f"datasets/sft_dataset_{'-'.join(languages)}.jsonl", "w", encoding="utf-8") as f:
        for data in out_dataset:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
