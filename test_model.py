import argparse
import glob
import os
import shutil
import tqdm
from cjtrans.lang.compiler.cj_compiler import compile_and_run_cj
from cjtrans.lang.syntax.cj_check import parse_error_messages
from cjtrans.translate.translator import Translator
from cjtrans.lm_inference import ModelPredictor
from cjtrans.utils.bash_utils import remove_color_codes
from cjtrans.utils.file_utils import read_file, write_to_file
from cjtrans.utils.md_utils import extract_code_block
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def main():
    parser = argparse.ArgumentParser(description="test model")
    parser.add_argument("--input", type=str, help="input path")
    parser.add_argument("--output", type=str, help="output path")
    parser.add_argument("--lang", type=str, default="java", help="source language")
    parser.add_argument("--model", type=str, help="LLM path")
    parser.add_argument("--device", type=str, help="Inference device")
    args = parser.parse_args()
    device = args.device
    model_path = args.model
    engine = ModelPredictor(model_path, use_vllm=False, device=device)
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

        translated_code = translator.translate(source_code, source_lang=args.lang)
        translated_code = translated_code.rstrip()
        if "```" in translated_code:
            extraction_output = extract_code_block(translated_code)
            if extraction_output is not None:
                translated_code = extraction_output

        write_to_file(out_cj_target_translation_path, translated_code)


if __name__ == "__main__":
    main()
