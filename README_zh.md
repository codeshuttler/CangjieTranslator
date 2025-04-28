# 仓颉翻译器（Cangjie Translator）

## 目的
在快速发展的软件开发领域，不同编程环境之间的互操作需求推动了实用代码翻译工具的兴起。  
现有基于学习的方法往往难以应对低资源编程语言，因为缺乏足够的平行代码语料用于训练。为了克服这些局限性，我们提出了一种新的训练框架：从单语种种子语料出发，通过回译生成平行数据集，并结合编译器反馈优化翻译模型。

作为案例研究，我们将该方法应用于一个新生的低资源编程语言——**仓颉（Cangjie）**，训练了一个代码翻译模型。我们同时构建了一个**Java到仓颉**的平行测试集以及相关测试用例，用以评估方法效果。实验结果表明，编译器反馈极大地提升了翻译后仓颉代码的语法正确率、语义准确率以及测试通过率。这些发现表明，本方法能够有效支持低资源环境下的代码翻译，拓展了学习型模型在稀缺数据编程语言上的应用潜力。

本成果包括三部分：
* 第一部分是我们构建的测试数据集；
* 第二部分是评估脚本；
* 第三部分是翻译模型和基线方法的测试结果。

# 数据
我们手动构建了测试数据集。测试数据来源于TransCoder项目中的Java代码，包含216个测试样本，覆盖测试输入和待测试的函数。  
Java代码到仓颉代码的翻译由两位经验丰富的开发者完成，二人均有超过三年的Java开发经验和三个月的仓颉开发经验。整个数据集构建耗时两周。

测试数据集托管于`Releases`目录下：[TransCoderTestCJ](https://github.com/codeshuttler/CangjieTranslator/releases/download/artifacts/results.7z)。

# 环境配置

## 硬件要求
最低配置：
```
64位处理器和操作系统  
操作系统：Linux发行版  
处理器：Intel Core i5-6600  
内存：64 GB RAM  
GPU：NVIDIA GeForce RTX 3090（神经网络推理需使用GPU，显存至少24GB。如使用CPU推理，时间会大幅延长）  
网络：宽带互联网连接  
存储空间：可用空间128 GB以上
```

测试过的硬件配置：
```
CPU：双插槽，16核 Intel Xeon Gold 6226R 2.90GHz  
内存：8×32GB DDR4 2933MHz  
GPU：NVIDIA GeForce RTX 3090
```

```
CPU：双插槽，32核 AMD EPYC 7601  
内存：8×32GB DDR4 2400MHz  
GPU：NVIDIA GeForce RTX 3090
```

## 软件要求

测试过的操作系统：
* Ubuntu 22.10 64位，Linux内核5.19.0
* Ubuntu 22.04.2 LTS 64位，Linux内核6.2.0

所需软件：
* Anaconda3-2023.09-0-Linux-x86_64（或Miniconda）

Python依赖（在Python 3.11.9下测试）：
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

我们使用conda环境来运行所有Python程序。

# 训练流程

## 持续预训练（Continued Pretraining）

首先，将原始数据放入`raw_data/cangjie_gitee_codes.json/cangjie.json`。  
利用LLM将仓颉代码翻译成Java、C++和Python代码：
```bash
python source_synthetic_java.py
python source_synthetic_cpp.py
python source_synthetic_python.py
```
数据输出至：
- `datasets/generated_java`
- `datasets/generated_cpp`
- `datasets/generated_python`

随后，生成持续预训练数据集：
```bash
python pretrain_generate.py
```
此脚本收集所有`datasets/generated_java/*/*/data.json`，输出至`datasets/pretrain_dataset.jsonl`。

将数据转换为Huggingface格式：
```bash
python save_as_hf.py datasets/pretrain_dataset.jsonl datasets/cangjie_pretrain_dataset
```
最终数据存储在`datasets/cangjie_pretrain_dataset`。

我们还加入了仓颉的文档数据，首先导出为json：
```bash
python export_text_files_to_jsonl.py raw_data/cangjie_documents datasets/pretrain_cangjie_documents_dataset.jsonl
```
得到`datasets/pretrain_cangjie_documents_dataset.jsonl`。

再转为Huggingface格式：
```bash
python save_as_hf.py datasets/pretrain_cangjie_documents_dataset.jsonl datasets/cangjie_pretrain_documents_dataset --test-ratio 0 --valid-ratio 0
```
得到数据集`datasets/cangjie_pretrain_documents_dataset`。

准备好上述两个数据集后，在[LLaMA-Factory-Cangjie](https://github.com/codeshuttler/LLaMA-Factory-Cangjie)配置路径并开始训练：
```bash
llamafactory-cli train hparams/cangjie/cangjie-qwen2-7b/cangjie_pretrain.yaml
```

## 指令微调（SFT）

首先合成指令微调数据：
```bash
python sft_generate.py --languages java,python,cpp
```
生成初步数据集`datasets/sft_dataset_java-python-cpp.jsonl`。

清洗数据：
```bash
python sft_clean.py --input datasets/sft_dataset_cpp-java-python.jsonl --output datasets/sft_full_dataset_cleaned.jsonl --export datasets/clean_code_full
```
得到清洗后的`datasets/sft_full_dataset_cleaned.jsonl`。

转换为Huggingface格式：
```bash
python save_as_hf.py datasets/sft_full_dataset_cleaned.jsonl datasets/cangjie_sft_full_dataset
```
准备好后，在[LLaMA-Factory-Cangjie](https://github.com/codeshuttler/LLaMA-Factory-Cangjie)配置路径并训练：
```bash
llamafactory-cli train hparams/cangjie/cangjie-qwen2-7b/cangjie_sft.yaml
```

# 增量合成（Incremental Synthesis）

下载LeetCode Huggingface数据集并导出本地：
```bash
python export_leetcode.py
```
得到`raw_data/leetcode_nonpara`目录。

使用SFT阶段训练好的模型进行增量合成：
```bash
python test_model.py --lang java --input "raw_data/leetcode_nonpara" --output "results/leetcode_java_nonpara_out" --model "/路径/到/sft_full_v2/checkpoint-22091" --device cuda:0
python test_model.py --lang python --input "raw_data/leetcode_nonpara" --output "results/leetcode_python_nonpara_out" --model "/路径/到/sft_full_v2/checkpoint-22091" --device cuda:0
python test_model.py --lang cpp --input "raw_data/leetcode_nonpara" --output "results/leetcode_cpp_nonpara_out" --model "/路径/到/sft_full_v2/checkpoint-22091" --device cuda:0
```

# 编译器反馈（Compiler Feedback）

对增量合成结果进行编译检查与修复：
```bash
python check_compile_results.py --input results/leetcode_java_nonpara_out/
python check_execution_results.py --language java --input results/leetcode_java_nonpara_out/ --auto-fix --fix-steps "simple,rule,llm"

python check_compile_results.py --input results/leetcode_python_nonpara_out/
python check_execution_results.py --language python --input results/leetcode_python_nonpara_out/ --auto-fix --fix-steps "simple,rule,llm"

python check_compile_results.py --input results/leetcode_cpp_nonpara_out/
python check_execution_results.py --language cpp --input results/leetcode_cpp_nonpara_out/ --auto-fix --fix-steps "simple,rule,llm"
```

基于修复后的正确代码，生成KTO（正负反馈）数据：
```bash
python feedback_generate_kto.py --language java --input results/leetcode_java_nonpara_out --output datasets/feedback_kto_java_dataset.jsonl
python feedback_generate_kto.py --language python --input results/leetcode_python_nonpara_out --output datasets/feedback_kto_python_dataset.jsonl
python feedback_generate_kto.py --language cpp --input results/leetcode_cpp_nonpara_out --output datasets/feedback_kto_cpp_dataset.jsonl
```

整合并转换为Huggingface格式：
```bash
cat datasets/feedback_kto_java_dataset.jsonl datasets/feedback_kto_python_dataset.jsonl datasets/feedback_kto_cpp_dataset.jsonl > datasets/feedback_kto_full_dataset.jsonl
python save_as_hf.py datasets/feedback_kto_full_dataset.jsonl datasets/cangjie_feedback_kto_full_dataset --test-ratio 0 --valid-ratio 0
```

最后，在[LLaMA-Factory-Cangjie](https://github.com/codeshuttler/LLaMA-Factory-Cangjie)填写数据集路径并开始最终训练：
```bash
llamafactory-cli train hparams/cangjie...
```

# 运行评测

完整的评测流程包含在 `evaluation.sh` 脚本中。评测结果会生成在 `results` 文件夹下。

由于评测结果文件较大，我们已将其压缩，并放置在 `Releases` 中。

# 许可证

Apache License Version 2.0
