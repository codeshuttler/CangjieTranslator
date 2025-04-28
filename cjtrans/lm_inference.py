import json
import os
from typing import Dict, List, Optional, Union
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Check  vllm module
try:
    import vllm
    from vllm.lora.request import LoRARequest

except ImportError:
    print("vllm module not found, please install it first.")
    exit(1)


class ModelPredictor(object):
    def __init__(
        self,
        model_path: str,
        use_vllm: bool = False,
        device: str = "cuda",
        torch_dtype="auto",
        load_8bit=False,
        load_4bit=False,
        enforce_eager=False,
        max_lora_rank=256,
        enable_prefix_caching=True,
        max_model_len=8192,
        gpu_memory_utilization=0.9
    ) -> None:
        # 加载模型
        self.model_path = model_path
        self.use_vllm = use_vllm

        if self.use_vllm:
            self.lora_adapter = None
            # 不存在 config.json 文件
            if os.path.exists(model_path) and not os.path.exists(os.path.join(model_path, "config.json")):
                print(f"No supported config format found in {model_path}, enable lora")
                # read adapter config get base model path
                adapter_config = json.load(open(os.path.join(model_path, "adapter_config.json"), "r", encoding="utf-8"))
                base_model_path = adapter_config.get("base_model_name_or_path", None)
                if base_model_path is None:
                    raise ValueError(f"No base model path found in {model_path}")

                self.lora_adapter = LoRARequest("lora_adapter", 1, model_path)
                self.model_path = base_model_path
                enable_lora=True
            else:
                enable_lora=False
            if device == "auto":
                num_gpu = len(os.environ["CUDA_VISIBLE_DEVICES"].split(","))
            else:
                num_gpu = 1
            self.llm = vllm.LLM(
                model=self.model_path,
                trust_remote_code=True,
                enable_prefix_caching=enable_prefix_caching,
                dtype=torch_dtype,
                enable_lora=enable_lora,
                enforce_eager=enforce_eager,
                max_lora_rank=max_lora_rank,
                tensor_parallel_size=num_gpu,
                max_model_len=max_model_len,
                gpu_memory_utilization=gpu_memory_utilization,
            )
        else:
            args = {}
            if load_8bit:
                args["load_in_8bit"] = True
            if load_4bit:
                args["load_in_4bit"] = True

            self.device = device
            if self.device == "auto":
                device_map = "auto"
                self.device = "cuda"
            else:
                device_map = self.device

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map=device_map,
                torch_dtype=torch_dtype,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                # attn_implementation="flash_attention_2",
                **args
            )
            if device_map != "auto":
                self.model.to(self.device)

        # 加载tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        # self.tokenizer.padding_side = 'left'
        # self.tokenizer.pad_token = self.tokenizer.unk_token

    def token_num(self, text: Union[str, Dict[str, str]]):
        if not isinstance(text, str):
            text = self.tokenizer.apply_chat_template(
                text,
                tokenize=False,
                add_generation_prompt=True
            )
        model_inputs = self.tokenizer([text], return_tensors="pt")
        return model_inputs.input_ids.shape[1]

    def inference_single(
        self,
        input: str,
        max_length: int = 2048,
        truncation: bool = False,
        max_new_tokens: int = 2048,
        do_sample: Optional[bool] = None,
        num_beams: Optional[int] = None,
        temperature: Optional[float] = None,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
    ):
        if self.use_vllm:
            prompts = [input]
            gen_params = {}
            if temperature is not None:
                gen_params["temperature"] = temperature
            if top_k is not None:
                gen_params["top_k"] = top_k
            if top_p is not None:
                gen_params["top_p"] = top_p
            sampling_params = vllm.SamplingParams(max_tokens=max_new_tokens, **gen_params)
            if self.lora_adapter is not None:
                outputs = self.llm.generate(prompts, sampling_params, use_tqdm=False, lora_request=self.lora_adapter)
            else:
                outputs = self.llm.generate(prompts, sampling_params, use_tqdm=False)

            outputs_text_list = []
            # Print the outputs.
            for output in outputs:
                generated_text = output.outputs[0].text
                outputs_text_list.append(generated_text)
            output_text = outputs_text_list[0]
        else:
            input_ids = self.tokenizer(
                [input],
                return_tensors="pt",
                padding="longest",
                max_length=max_length,
                truncation=truncation,
            )["input_ids"].to(self.device)

            gen_params = {}
            if do_sample is not None:
                gen_params["do_sample"] = do_sample
            if num_beams is not None:
                gen_params["num_beams"] = num_beams
            if temperature is not None:
                gen_params["temperature"] = temperature
            if top_k is not None:
                gen_params["top_k"] = top_k
            if top_p is not None:
                gen_params["top_p"] = top_p

            outputs_ids = self.model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id,
                **gen_params
            )
            outputs = self.tokenizer.batch_decode(outputs_ids, skip_special_tokens=True)
            output_text = outputs[0]
        return output_text

    def inference_batch(
        self,
        inputs: List[str],
        max_length: int = 2048,
        truncation: bool = False,
        max_new_tokens: int = 2048,
        do_sample: Optional[bool] = None,
        num_beams: Optional[int] = None,
        temperature: Optional[float] = None,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
    ):
        if self.use_vllm:
            prompts = inputs
            gen_params = {}
            if temperature is not None:
                gen_params["temperature"] = temperature
            if top_k is not None:
                gen_params["top_k"] = top_k
            if top_p is not None:
                gen_params["top_p"] = top_p
            sampling_params = vllm.SamplingParams(max_tokens=max_new_tokens, **gen_params)
            if self.lora_adapter is not None:
                outputs = self.llm.generate(prompts, sampling_params, use_tqdm=False, lora_request=self.lora_adapter)
            else:
                outputs = self.llm.generate(prompts, sampling_params, use_tqdm=False)

            outputs_text_list = []
            # Print the outputs.
            for output in outputs:
                generated_text = output.outputs[0].text
                outputs_text_list.append(generated_text)
        else:
            input_ids = self.tokenizer(
                inputs,
                return_tensors="pt",
                padding="longest",
                max_length=max_length,
                truncation=truncation,
            )["input_ids"].to(self.device)

            gen_params = {}
            if do_sample is not None:
                gen_params["do_sample"] = do_sample
            if num_beams is not None:
                gen_params["num_beams"] = num_beams
            if temperature is not None:
                gen_params["temperature"] = temperature
            if top_k is not None:
                gen_params["top_k"] = top_k
            if top_p is not None:
                gen_params["top_p"] = top_p

            outputs_ids = self.model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id,
                **gen_params
            )
            outputs = self.tokenizer.batch_decode(outputs_ids, skip_special_tokens=True)
        return outputs

    def chat(
        self,
        messages: Dict[str, str],
        max_new_tokens: int = 2048,
        do_sample: Optional[bool] = None,
        num_beams: Optional[int] = None,
        temperature: Optional[float] = None,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
    ):
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        if self.use_vllm:
            prompts = [text]
            gen_params = {}
            if temperature is not None:
                gen_params["temperature"] = temperature
            if top_k is not None:
                gen_params["top_k"] = top_k
            if top_p is not None:
                gen_params["top_p"] = top_p
            sampling_params = vllm.SamplingParams(max_tokens=max_new_tokens, **gen_params)
            if self.lora_adapter is not None:
                outputs = self.llm.generate(prompts, sampling_params, use_tqdm=False, lora_request=self.lora_adapter)
            else:
                outputs = self.llm.generate(prompts, sampling_params, use_tqdm=False)

            outputs_text_list = []
            for output in outputs:
                generated_text = output.outputs[0].text
                outputs_text_list.append(generated_text)
            response = outputs_text_list[0]
        else:
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
            attention_mask = torch.ones(
                model_inputs.input_ids.shape, dtype=torch.long, device=self.device
            )

            gen_params = {}
            if do_sample is not None:
                gen_params["do_sample"] = do_sample
            if num_beams is not None:
                gen_params["num_beams"] = num_beams
            if temperature is not None:
                gen_params["temperature"] = temperature
            if top_k is not None:
                gen_params["top_k"] = top_k
            if top_p is not None:
                gen_params["top_p"] = top_p

            generated_ids = self.model.generate(
                model_inputs.input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                **gen_params
            )

            generated_ids = [
                output_ids[len(input_ids) :]
                for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[
                0
            ]
        return response


if __name__ == "__main__":
    predictor = ModelPredictor('../models/Qwen1.5-110B-Chat/', load_8bit=True)
    prompt = "Give me a short introduction to large language model."
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]

    out = predictor.chat(messages)
    print(out)
