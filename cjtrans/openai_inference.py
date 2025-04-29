import json
import os
from typing import Dict, List, Optional, Union
import uuid
import openai
import tiktoken
import transformers
from openai import AzureOpenAI


class OpenaiModelPredictor(object):
    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        # 加载模型
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url

        if "azure.com" in self.base_url:
            self.client = AzureOpenAI(
                azure_endpoint=base_url, api_key=api_key, api_version="2024-02-01", timeout=5*60
            )
        else:
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        if self.model_name == "deepseek-chat" or self.model_name == "deepseek-coder":
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"
            )
        elif "deepseek-v2.5" in self.model_name.lower():
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                "deepseek-ai/DeepSeek-V2.5"
            )
        elif self.model_name == "qwen2.5-72b-instruct":
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                "Qwen/Qwen2.5-72B-Instruct"
            )
        elif self.model_name == "yi-large":
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                "01-ai/Yi-1.5-34B-Chat"
            )
        elif self.model_name == "chatglm3-6b":
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                "THUDM/chatglm3-6b"
            )
        elif self.model_name == "GPT-3.5":
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"
            )
        elif "qwen" in self.model_name.lower():
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(self.model_name)
        else:
            self.tokenizer = tiktoken.encoding_for_model(self.model_name)

    def token_num(self, text: Union[str, Dict[str, str]]):
        if not isinstance(text, str):
            text = self.tokenizer.apply_chat_template(
                text, tokenize=False, add_generation_prompt=True
            )
        model_inputs = self.tokenizer.encode(text)
        return len(model_inputs)

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
        outputs = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": input}],
            max_tokens=max_length,
            temperature=temperature,
            top_p=top_p,
        )
        return outputs.choices[0].message.content

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
        results = []
        for input in inputs:
            results.append(
                self.inference_single(
                    input,
                    max_length=max_length,
                    truncation=truncation,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    do_sample=do_sample,
                    num_beams=num_beams,
                )
            )
        return results

    def chat(
        self,
        messages: Dict[str, str],
        max_length: int = 2048,
        max_new_tokens: int = 2048,
        do_sample: Optional[bool] = None,
        num_beams: Optional[int] = None,
        temperature: Optional[float] = None,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
    ):
        outputs = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=max_length,
            temperature=temperature,
            top_p=top_p,
        )
        return outputs.choices[0].message.content

    def chat_batch_json(
        self,
        task_id: str,
        messages: Dict[str, str],
        max_length: int = 2048,
        max_new_tokens: int = 2048,
        do_sample: Optional[bool] = None,
        num_beams: Optional[int] = None,
        temperature: Optional[float] = None,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
    ):
        task_id = task_id
        item = {
            "custom_id": task_id,
            "method": "POST",
            "url": "/chat/completions",
            "body": {
                "model": self.model_name,
                "messages": messages,
                "max_completion_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "n": 1,
            },
        }
        return item