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


# Run Evaluation
The evaluation workflow is in the 
The entire evaluation workflow is in the `run.sh` script. The evaluation results are generated in the `results` folder. 

Due to the large file size of our evaluation results, we compressed them and placed them under `Releases`.

# LICENSE
Apache License Version 2.0