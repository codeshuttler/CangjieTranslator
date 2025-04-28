# para_data: cangjie_para -> cangjie_para_format -> cangjie_para_clean_full

sft_checkpoint_path="/data/user/LLaMA-Factory/saves/cangjie-qwen2-7b/full/sft_full_v2/checkpoint-22091"

# Synthetic Data
python source_synthetic_java.py
python source_synthetic_cpp.py
python source_synthetic_python.py

# Pretrain
python pretrain_generate.py
python save_as_hf.py datasets/pretrain_dataset.jsonl datasets/cangjie_pretrain_dataset
python export_text_files_to_jsonl.py raw_data/cangjie_documents datasets/pretrain_cangjie_documents_dataset.jsonl
python save_as_hf.py datasets/pretrain_cangjie_documents_dataset.jsonl datasets/cangjie_pretrain_documents_dataset --test-ratio 0 --valid-ratio 0

# SFT
python sft_generate.py --languages java,python,cpp
python sft_clean.py --input datasets/sft_dataset_cpp-java-python.jsonl --output datasets/sft_full_dataset_cleaned.jsonl --export datasets/clean_code_full
python save_as_hf.py datasets/sft_full_dataset_cleaned.jsonl datasets/cangjie_sft_full_dataset

# Use model to translate cangjie code to xxx(java, python, cpp)
python test_model.py --lang java --input "raw_data/cangjie_para_clean_full" --output "results/cangjie_sft_full_para_out/cangjie_java_para_out" --model $sft_checkpoint_path --device cuda:0
python test_model.py --lang python --input "raw_data/cangjie_para_clean_full" --output "results/cangjie_sft_full_para_out/cangjie_python_para_out" --model $sft_checkpoint_path --device cuda:0
python test_model.py --lang cpp --input "raw_data/cangjie_para_clean_full" --output "results/cangjie_sft_full_para_out/cangjie_cpp_para_out" --model $sft_checkpoint_path --device cuda:0

# Check java Results
python check_compile_results.py --input results/cangjie_sft_full_para_out/cangjie_java_para_out/
python check_execution_results.py --language java --input results/cangjie_sft_full_para_out/cangjie_java_para_out/ --auto-fix --fix-steps "simple"

# Check python Results
python check_compile_results.py --input results/cangjie_sft_full_para_out/cangjie_python_para_out/
python check_execution_results.py --language python --input results/cangjie_sft_full_para_out/cangjie_python_para_out/ --auto-fix --fix-steps "simple"

# Check cpp Results
python check_compile_results.py --input results/cangjie_sft_full_para_out/cangjie_cpp_para_out/
python check_execution_results.py --language cpp --input results/cangjie_sft_full_para_out/cangjie_cpp_para_out/ --auto-fix --fix-steps "simple"

# Code Refinement
python export_leetcode.py
python test_model.py --lang java --input "raw_data/leetcode_nonpara" --output "results/leetcode_java_nonpara_out" --model $sft_checkpoint_path --device cuda:0
python test_model.py --lang python --input "raw_data/leetcode_nonpara" --output "results/leetcode_python_nonpara_out" --model $sft_checkpoint_path --device cuda:0
python test_model.py --lang cpp --input "raw_data/leetcode_nonpara" --output "results/leetcode_cpp_nonpara_out" --model $sft_checkpoint_path --device cuda:0

# Check Results
python check_compile_results.py --input results/leetcode_java_nonpara_out/
python check_execution_results.py --language java --input results/leetcode_java_nonpara_out/ --auto-fix --fix-steps "simple,rule,llm"

python check_compile_results.py --input results/leetcode_python_nonpara_out/
python check_execution_results.py --language python --input results/leetcode_python_nonpara_out/ --auto-fix --fix-steps "simple,rule,llm"

python check_compile_results.py --input results/leetcode_cpp_nonpara_out/
python check_execution_results.py --language cpp --input results/leetcode_cpp_nonpara_out/ --auto-fix --fix-steps "simple,rule,llm"

# Feedback kto
python feedback_generate_kto.py --language java --input results/leetcode_java_nonpara_out --output datasets/feedback_kto_java_dataset.jsonl
python feedback_generate_kto.py --language python --input results/leetcode_python_nonpara_out --output datasets/feedback_kto_python_dataset.jsonl
python feedback_generate_kto.py --language cpp --input results/leetcode_cpp_nonpara_out --output datasets/feedback_kto_cpp_dataset.jsonl

cat datasets/feedback_kto_java_dataset.jsonl datasets/feedback_kto_python_dataset.jsonl datasets/feedback_kto_cpp_dataset.jsonl > datasets/feedback_kto_full_dataset.jsonl
python save_as_hf.py datasets/feedback_kto_full_dataset.jsonl datasets/cangjie_feedback_kto_full_dataset --test-ratio 0 --valid-ratio 0
