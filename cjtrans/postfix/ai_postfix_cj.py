import glob
import os
import re
from typing import Dict, List, Tuple

from cjtrans.translate.translator import Translator
from cjtrans.lm_inference import ModelPredictor
from cjtrans.utils.file_utils import read_file
from cjtrans.utils.md_utils import extract_code_block

MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct-GPTQ-Int4"
device = "cuda:0"  # the device to load the model onto
translator = None


def ai_fix_cj(
    cj_code: str, compiler_outputs: List[Tuple[str, str, str, str, str]], doc_path=None
) -> Tuple[str, Dict[str, str]]:
    global translator
    if translator is None:
        engine = ModelPredictor(MODEL_NAME, use_vllm=True, device=device, enforce_eager=True)
        translator = Translator(engine)
    lines = cj_code.splitlines()
    # Unique outputs
    compiler_outputs_rc = set()
    unique_compiler_outputs = []
    for error in compiler_outputs:
        error_msg, error_file, error_row, error_col, error_details = error
        if (error_row, error_col) in compiler_outputs_rc:
            continue
        compiler_outputs_rc.add((error_row, error_col))
        unique_compiler_outputs.append(error)
    compiler_outputs = unique_compiler_outputs

    if len(compiler_outputs) > 0:
        error = compiler_outputs[-1]
    else:
        return "\n".join(lines), {}

    # Mark the error line
    for error in reversed(compiler_outputs):
        error_msg, error_file, error_row, error_col, error_details = error
        if error_file is None:
            return "\n".join(lines), {}
        error_line_index = error_row - 1
        if error_line_index >= len(lines):
            return "\n".join(lines), {}
        error_line = lines[error_line_index]
        new_line = error_line + f"    // Here is the ERROR LINE. {error_msg}"
        lines[error_line_index] = new_line

    doc = None
    doc_selected = None
    if doc_path is not None:
        cj_docs = glob.glob(os.path.join(doc_path, "**", "*.txt"), recursive=True)
        cj_docs = filter(lambda x: not x.startswith('2_'), list(cj_docs))
        # print(list(cj_docs))
        model_out = translator.index_document(list(cj_docs), error_msg + "\n" + error_details)
        match = re.search(r"```(.*)```", model_out)
        if match:
            doc_selected = match.group(1)
            if not os.path.exists(doc_selected):
                doc_selected = os.path.join(doc_path, doc_selected)
            print(doc_selected, error_msg + "\n" + error_details)
            if os.path.exists(doc_selected):
                doc = read_file(doc_selected)
    model_out = translator.correct_code(
        "\n".join(lines), error_msg + "\n" + error_details, related_doc=doc
    )
    code = extract_code_block(model_out)
    if code is None:
        print(model_out)
    return code, {"doc": doc, "doc_selected": doc_selected, "model_out": model_out}
