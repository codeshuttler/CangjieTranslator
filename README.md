# Cangjie Translator

## Purpose
In the rapidly advancing field of software development, the demand for practical code translation tools has surged, driven by the need for interoperability across different programming environments.
Existing learning-based approaches often need help with low-resource programming languages that lack sufficient parallel code corpora for training. To address these limitations, we propose a novel training framework that begins with monolingual seed corpora, generating parallel datasets via back-translation and incorporating compiler feedback to optimize the translation model.

As a case study, we apply our method to train a code translation model for a new-born low-resource programming language, **Cangjie**. We also construct a parallel test dataset for **Java-to-Cangjie** translation and test cases to evaluate the effectiveness of our approach. Experimental results demonstrate that compiler feedback greatly enhances syntactical correctness, semantic accuracy, and test pass rates of the translated Cangjie code. These findings highlight the potential of our method to support code translation in low-resource settings, expanding the capabilities of learning-based models for programming languages with limited data availability.

The artifact contains three parts:
* The first part is our test dataset.
* The second part is the evaluation scripts.
* The three part is the test results of our translation model and baselines.

# Data
We manually constructed the test dataset. Our test data is derived from TransCoder's Java code, consisting of a total of 216 test samples, which include test inputs and functions to be tested.
We manually translated the Java code into Cangjie code, with two experienced developers involved in the translation process. Both developers have over three years of Java  development experience and three months of Cangjie language development experience. It took us two weeks to complete the construction of this dataset.
The test dataset is under the repository `Releases` - [TransCoderTestCJ](https://github.com/codeshuttler/CangjieTranslator/releases/download/artifacts/results.7z).

# Setup
## Hardware
Hardware Requirements.

Minimum:
```
Requires a 64-bit processor and operating system.
Operating System: Linux distributions.
Processor: Intel Core i5-6600.
Memory: 64 GB RAM.
GPU: NVIDIA GeForce RTX 3090. (GPUs are used for neural network inference, requires at least 24GB of graphics memory. If you run neural networks on the CPU, it may take a significant amount of time.)
Network: Broadband internet connection.
Storage: Requires 128 GB of available space.
```

Tested Hardware:
```
CPU: two slots of 16 Core Intel Xeon Gold 6226R CPU 2.90GHz Processor
Memory: 8x32GB DDR4 DIMM 2933MHz Memory
GPUs: GeForce RTX 3090 GPU.
```

```
CPU: two slots of 32 Core AMD EPYC 7601 32-Core Processor
Memory: 8x32GB DDR4 DIMM 2400MHz Memory
GPUs: GeForce RTX 3090 GPU.
```

## Software

Tested System:
* 64-bit Ubuntu 22.10 with Linux kernel 5.19.0
* 64-bit Ubuntu 22.04.2 LTS Linux kernel 6.2.0

Software Requirements:
* Anaconda3-2023.09-0-Linux-x86_64 (or Miniconda)

Python Requirements:
* javalang==0.13.0
* pandas==2.2.2
* torch==2.3.1+cu121
* tqdm==4.66.4
* transformers==4.41.2
* tree-sitter==0.23.0
* tree-sitter-java==0.23.2
* matplotlib==3.9.2
* seaborn==0.13.2
* git+https://github.com/jstzwj/tree-sitter-cangjie.git
* git+https://github.com/jstzwj/cjlang.git@62d45141bc7ca63ba2c2c3cdc5871422ca3b5eef

All code in this repository is tested under the environment of `Python 3.11.9`. We use conda to construct a virtual environment to run the python program.

# Training

## Continued Pretraining

First, the original data for Continued Pretraining is stored in `raw_data/cangjie_gitee_codes.json/cangjie.json`. We use an LLM to translate the Cangjie code into Java, C++, and Python:
```bash
python source_synthetic_java.py
python source_synthetic_cpp.py
python source_synthetic_python.py
```
The outputs are saved to `datasets/generated_java`, `datasets/generated_cpp`, and `datasets/generated_python`, respectively.

Next, we generate the Continued Pretraining dataset:
```bash
python pretrain_generate.py
```
This script collects all the `datasets/generated_java/*/*/data.json` files and outputs them into `datasets/pretrain_dataset.jsonl`.

We then split the dataset and save it in Huggingface dataset format:
```bash
python save_as_hf.py datasets/pretrain_dataset.jsonl datasets/cangjie_pretrain_dataset
```
This stores the final Continued Pretraining data in `datasets/cangjie_pretrain_dataset`.

Additionally, we add Cangjie documentation data to the Continued Pretraining. First, we export it from text files to JSON:
```bash
python export_text_files_to_jsonl.py raw_data/cangjie_documents datasets/pretrain_cangjie_documents_dataset.jsonl
```
This produces the data file `datasets/pretrain_cangjie_documents_dataset.jsonl`.

We then convert the documentation data into Huggingface dataset format:
```bash
python save_as_hf.py datasets/pretrain_cangjie_documents_dataset.jsonl datasets/cangjie_pretrain_documents_dataset --test-ratio 0 --valid-ratio 0
```
This results in the dataset `datasets/cangjie_pretrain_documents_dataset`.

After obtaining `datasets/cangjie_pretrain_dataset` and `datasets/cangjie_pretrain_documents_dataset`, we specify the paths to these datasets in [LLaMA-Factory-Cangjie](https://github.com/codeshuttler/LLaMA-Factory-Cangjie) and start training. Install dependencies and execute in the LLaMA-Factory-Cangjie directory:
```bash
llamafactory-cli train hparams/cangjie/cangjie-qwen2-7b/cangjie_pretrain.yaml
```

## SFT

First, we synthesize the Instruction Fine-tuning dataset:
```bash
python sft_generate.py --languages java,python,cpp
```
This generates the initial dataset `datasets/sft_dataset_java-python-cpp.jsonl`.

Next, we perform automated cleaning of the dataset:
```bash
python sft_clean.py --input datasets/sft_dataset_cpp-java-python.jsonl --output datasets/sft_full_dataset_cleaned.jsonl --export datasets/clean_code_full
```
This produces the cleaned dataset `datasets/sft_full_dataset_cleaned.jsonl`, and you can inspect the cleaned retained data in `datasets/clean_code_full`.

We then convert it to Huggingface format:
```bash
python save_as_hf.py datasets/sft_full_dataset_cleaned.jsonl datasets/cangjie_sft_full_dataset
```
This results in the dataset `datasets/cangjie_sft_full_dataset`.

After obtaining `datasets/cangjie_sft_full_dataset`, we specify the path in [LLaMA-Factory-Cangjie](https://github.com/codeshuttler/LLaMA-Factory-Cangjie) and start training. Install dependencies and execute in the LLaMA-Factory-Cangjie directory:
```bash
llamafactory-cli train hparams/cangjie/cangjie-qwen2-7b/cangjie_sft.yaml
```

# Incremental Synthesis

We download the LeetCode dataset from Huggingface and export it locally:
```bash
python export_leetcode.py
```
This creates the directory `raw_data/leetcode_nonpara`.

We then perform Incremental Synthesis using the model obtained from SFT:
```bash
python test_model.py --lang java --input "raw_data/leetcode_nonpara" --output "results/leetcode_java_nonpara_out" --model "/data/user/github/LLaMA-Factory/saves/cangjie-qwen2-7b/full/sft_full_v2/checkpoint-22091" --device cuda:0
python test_model.py --lang python --input "raw_data/leetcode_nonpara" --output "results/leetcode_python_nonpara_out" --model "/data/user/github/LLaMA-Factory/saves/cangjie-qwen2-7b/full/sft_full_v2/checkpoint-22091" --device cuda:0
python test_model.py --lang cpp --input "raw_data/leetcode_nonpara" --output "results/leetcode_cpp_nonpara_out" --model "/data/user/github/LLaMA-Factory/saves/cangjie-qwen2-7b/full/sft_full_v2/checkpoint-22091" --device cuda:0
```

# Compiler Feedback

We use a compiler to check and fix the translation results:
```bash
python check_compile_results.py --input results/leetcode_java_nonpara_out/
python check_execution_results.py --language java --input results/leetcode_java_nonpara_out/ --auto-fix --fix-steps "simple,rule,llm"

python check_compile_results.py --input results/leetcode_python_nonpara_out/
python check_execution_results.py --language python --input results/leetcode_python_nonpara_out/ --auto-fix --fix-steps "simple,rule,llm"

python check_compile_results.py --input results/leetcode_cpp_nonpara_out/
python check_execution_results.py --language cpp --input results/leetcode_cpp_nonpara_out/ --auto-fix --fix-steps "simple,rule,llm"
```

Based on the correctly repaired code, we generate KTO positive and negative feedback data:
```bash
python feedback_generate_kto.py --language java --input results/leetcode_java_nonpara_out --output datasets/feedback_kto_java_dataset.jsonl
python feedback_generate_kto.py --language python --input results/leetcode_python_nonpara_out --output datasets/feedback_kto_python_dataset.jsonl
python feedback_generate_kto.py --language cpp --input results/leetcode_cpp_nonpara_out --output datasets/feedback_kto_cpp_dataset.jsonl
```

We then convert the KTO training data into Huggingface format:
```bash
cat datasets/feedback_kto_java_dataset.jsonl datasets/feedback_kto_python_dataset.jsonl datasets/feedback_kto_cpp_dataset.jsonl > datasets/feedback_kto_full_dataset.jsonl
python save_as_hf.py datasets/feedback_kto_full_dataset.jsonl datasets/cangjie_feedback_kto_full_dataset --test-ratio 0 --valid-ratio 0
```

After obtaining `datasets/cangjie_feedback_kto_full_dataset`, we specify the path in [LLaMA-Factory-Cangjie](https://github.com/codeshuttler/LLaMA-Factory-Cangjie) and start training. Install dependencies and execute in the LLaMA-Factory-Cangjie directory:
```bash
llamafactory-cli train hparams/cangjie/cangjie-qwen2-7b/cangjie_lora_kto.yaml
```

# Run Evaluation
The evaluation workflow is in the 
The entire evaluation workflow is in the `evaluation.sh` script. The evaluation results are generated in the `results` folder. 

Due to the large file size of our evaluation results, we compressed them and placed them under `Releases`.

# LICENSE
Apache License Version 2.0