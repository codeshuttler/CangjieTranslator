import argparse
import glob
import os
import json
import random
import shutil
import time
from typing import Dict
import tqdm
from cjtrans.lang.compiler.cj_compiler import compile_and_run_cj
from cjtrans.lang.syntax.cj_check import parse_error_messages
from cjtrans.translate.translator import Translator
from cjtrans.lm_inference import ModelPredictor
from cjtrans.openai_inference import OpenaiModelPredictor
from cjtrans.utils.bash_utils import remove_color_codes
from cjtrans.utils.file_utils import read_file, write_to_file
from cjtrans.utils.md_utils import extract_code_block
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import jinja2


def apply_jinja_template(template: str, data: Dict[str, str]) -> str:
    jinja_template: jinja2.Template = jinja2.Template(template)
    return jinja_template.render(data)


def main():
    parser = argparse.ArgumentParser(description="test model")
    parser.add_argument("--input", type=str, help="input path")
    parser.add_argument("--output", type=str, help="output path")
    parser.add_argument("--lang", type=str, default="java", help="source language")
    parser.add_argument("--few-shot-num", type=int, default=1, help="few shot number")
    parser.add_argument(
        "--prompt-path",
        type=str,
        default="resources/prompts/baseline.json",
        help="prompt path",
    )
    parser.add_argument(
        "--example-path",
        type=str,
        default="resources/examples/leetcode_java_examples.jsonl",
        help="prompt path",
    )
    parser.add_argument("--model", type=str, help="LLM path")
    parser.add_argument("--tokenizer", type=str, default="", help="api key")
    parser.add_argument("--base-url", type=str, help="base url")
    parser.add_argument("--api-key", type=str, help="api key")
    parser.add_argument("--seed", default=42, type=int, help="seed")
    args = parser.parse_args()
    print(args)
    
    # 如果是deepseek，只允许在00:30到08:00直接运行
    if "deepseek-chat" in args.model:
        import datetime
        current_time = datetime.datetime.now()
        if current_time > datetime.datetime(current_time.year, current_time.month, current_time.day, 8, 0):
            print("Current time is not within the allowed range (00:30 to 08:00). Exiting.")
            return

    base_url = args.base_url
    api_key = args.api_key
    engine = OpenaiModelPredictor(args.model, base_url=base_url, api_key=api_key)
    translator = Translator(engine)

    lang_full = args.lang
    if args.lang == "java":
        source_files = list(glob.glob(os.path.join(args.input, "*/java_target.java")))
        lang_short = "java"
    elif args.lang == "python":
        source_files = list(glob.glob(os.path.join(args.input, "*/python_target.py")))
        lang_short = "py"
    elif args.lang == "cpp":
        source_files = list(glob.glob(os.path.join(args.input, "*/cpp_target.cpp")))
        lang_short = "cpp"
    else:
        raise Exception("Unknown language")

    # Read all prompts and examples
    with open(args.prompt_path, "r", encoding="utf-8") as f:
        prompts_text = f.read()
    prompts = json.loads(prompts_text)

    with open(args.example_path, "r", encoding="utf-8") as f:
        examples_text = f.read()
    examples = [json.loads(l.strip()) for l in examples_text.split("\n") if l.strip()]

    for source_target_path in tqdm.tqdm(source_files):
        dir_path = os.path.dirname(source_target_path)
        cj_target_path = os.path.join(dir_path, "cj_target.cj")
        source_test_path = os.path.join(dir_path, f"{lang_full}_test.{lang_short}")
        cj_test_path = os.path.join(dir_path, "cj_test.cj")

        out_dir_path = args.output
        dir_path = os.path.dirname(source_target_path).replace("\\", "/").split("/")[-1]
        out_sub_dir_path = os.path.join(out_dir_path, dir_path)
        out_source_target_path = os.path.join(
            out_dir_path, dir_path, f"{lang_full}_target.{lang_short}"
        )
        out_cj_target_path = os.path.join(out_dir_path, dir_path, "cj_target.cj")
        out_source_test_path = os.path.join(
            out_dir_path, dir_path, f"{lang_full}_test.{lang_short}"
        )
        out_cj_test_path = os.path.join(out_dir_path, dir_path, "cj_test.cj")

        out_cj_target_translation_path = os.path.join(
            out_dir_path, dir_path, "cj_target_translation.cj"
        )
        out_prompt_path = os.path.join(out_dir_path, dir_path, "prompt.json")

        if not os.path.exists(out_dir_path):
            os.makedirs(out_dir_path, exist_ok=False)

        if not os.path.exists(out_sub_dir_path):
            os.makedirs(out_sub_dir_path, exist_ok=False)

        if os.path.exists(source_target_path) and not os.path.exists(
            out_source_target_path
        ):
            shutil.copy(source_target_path, out_source_target_path)
        if os.path.exists(cj_target_path) and not os.path.exists(out_cj_target_path):
            shutil.copy(cj_target_path, out_cj_target_path)
        if os.path.exists(source_test_path) and not os.path.exists(
            out_source_test_path
        ):
            shutil.copy(source_test_path, out_source_test_path)
        if os.path.exists(cj_test_path) and not os.path.exists(out_cj_test_path):
            shutil.copy(cj_test_path, out_cj_test_path)

        if os.path.exists(out_cj_target_translation_path):
            continue

        source_code = read_file(source_target_path)

        # Generate prompts and examples for the current file
        selected_prompt = random.choice(prompts)
        selected_examples = random.sample(examples, args.few_shot_num)

        conversation_history = []
        if len(selected_prompt) == 2 and selected_prompt[0]["role"] == "system":
            system_prompt = selected_prompt[0]
            system_prompt["content"] = apply_jinja_template(
                system_prompt["content"],
                {
                    "source_language": args.lang,
                    "target_language": "Cangjie",
                    "source_language_markdown": args.lang,
                    "target_language_markdown": "cangjie",
                    "source_code": source_code,
                },
            )
            conversation_history.append(system_prompt)
        for example in selected_examples:
            conversation_history.append(
                {"role": "user", "content": example["source_code"]}
            )
            conversation_history.append(
                {"role": "assistant", "content": example["cj_code"]}
            )
        instruction_prompt = selected_prompt[-1]
        instruction_content = apply_jinja_template(
            instruction_prompt["content"],
            {
                "source_language": args.lang,
                "target_language": "Cangjie",
                "source_language_markdown": args.lang,
                "target_language_markdown": "cangjie",
                "source_code": source_code,
            },
        )
        conversation_history.append({"role": "user", "content": instruction_content})

        try:
            translated_code = translator.translate_with_examples(
                source_code, source_lang=args.lang, examples=conversation_history
            )
            raw_output = translated_code
            translated_code = translated_code.rstrip()
            if "```" in translated_code:
                extraction_output = extract_code_block(translated_code)
                if extraction_output is not None:
                    translated_code = extraction_output
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            print(f"Error translating code: {e}")
            translated_code = ""
            raw_output = str(e)
            
            if "Request was rejected due to rate limiting." in raw_output:
                print("Rate limit exceeded. Please try again later.")
                time.sleep(60)  # Wait for 1 minute before retrying
                continue
            
            if "have exceeded token rate limit" in raw_output:
                print("Token rate limit exceeded. Please try again later.")
                time.sleep(60)  # Wait for 1 minute before retrying
                continue
            
            if "The API deployment for this resource does not exist." in raw_output:
                print("API deployment not found. Please check your model settings.")
                break
            
            if "Request timed out." in raw_output:
                print("Request timed out. Please try again later.")
                time.sleep(60)  # Wait for 1 minute before retrying
                continue
            
            if "Connection error" in raw_output:
                print("Connection error. Please check your network connection.")
                time.sleep(60)  # Wait for 1 minute before retrying
                continue
            
            if "unsupported_country_region_territory" in raw_output or "Country, region, or territory not supported" in raw_output:
                print("Unsupported country, region, or territory. Please check your model settings.")
                time.sleep(60)  # Wait for 1 minute before retrying
                continue
            
            if "Not enough point." in raw_output:
                print("Insufficient points. Please check your model settings.")
                continue
        
        if "gpt" in args.model.lower():
            time.sleep(80)
        
        if "siliconflow" in args.model.lower():
            time.sleep(15)

        if len(translated_code) != 0:
            write_to_file(out_cj_target_translation_path, translated_code)
            write_to_file(
                out_prompt_path,
                json.dumps(
                    {"messages": conversation_history, "raw_output": raw_output},
                    ensure_ascii=False,
                    indent=4,
                ),
            )


if __name__ == "__main__":
    main()
