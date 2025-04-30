# Test model
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/cangjie_para_out" --model "cangjie-qwen2-7b" --device cuda:0

# Check Results
python check_compile_results.py --input results/cangjie_para_out/
python check_execution_results.py --input results/cangjie_para_out/ --auto-fix --fix-steps "simple"

# Code Refinement
python export_leetcode.py
python test_model.py --lang java --input "raw_data/leetcode_nonpara" --output "results/leetcode_nonpara_out" --model "cangjie-qwen2-7b" --device cuda:0

# Check Results
python check_compile_results.py --input results/leetcode_nonpara_out/
python check_execution_results.py --input results/leetcode_nonpara_out/ --auto-fix --fix-steps "simple,rule,llm"

# Feedback kto
# python feedback_generate_kto.py --input results/leetcode_nonpara_out --output results/feedback_kto_dataset.jsonl
# python save_as_hf.py results/feedback_kto_dataset.jsonl results/cangjie_feedback_kto_dataset --test-ratio 0 --valid-ratio 0

# Test kto model
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/cangjie_para_feedback_kto_out" --model "cangjie-qwen2-7b-kto" --device cuda:1
python check_compile_results.py --input results/cangjie_para_feedback_kto_out/
python check_execution_results.py --input results/cangjie_para_feedback_kto_out/ --auto-fix --fix-steps "simple"

# Basic Statistics
python scripts/setups/cangjie_doc_basics.py "raw_data/cangjie_documents/*/*.txt"

python scripts/setups/java_data_basics.py "results/cangjie_para_gt/*/java_target.java" --output "test_java_metrics_statistics.csv"
python scripts/setups/java_data_basics.py "results/leetcode_nonpara_out/*/java_target.java" --output "incremental_java_metrics_statistics.csv"
python scripts/setups/cangjie_data_basics.py "results/clean_java/code/*/code.cj" --output "training_cangjie_metrics_statistics.csv"

# Overall effectiveness
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/rq1_cangjie_para_out" --model "cangjie-qwen2-7b-kto" --device cuda:1
python check_compile_results.py --input results/rq1_cangjie_para_out/ --use-fixed
python check_execution_results.py --input results/rq1_cangjie_para_out/ --auto-fix --fix-steps "simple,rule,llm"
python scripts/rq1/collect_execution_results.py --input "results/rq1_cangjie_para_out/"
# draw figure of test case details
python scripts/rq1/check_test_results.py "results/rq1_cangjie_para_out/"

python test_model.py --lang java --input "raw_data/leetcode_nonpara" --output "results/rq1_leetcode_nonpara_out" --model "cangjie-qwen2-7b-kto" --device cuda:0
python check_compile_results.py --input results/rq1_leetcode_nonpara_out/ --use-fixed
python check_execution_results.py --input results/rq1_leetcode_nonpara_out/ --auto-fix --fix-steps "simple,rule,llm"
python scripts/rq1/collect_execution_results.py --input "results/rq1_leetcode_nonpara_out/"

# Baseline models

fewshots=(1 2 3 4 5 10 15 20)
fewshot_best=20
prompt_groups=("baseline" "roleplay" "polite_inquiry" "clarify_usage")

# deepseek-v2.5
for i in "${fewshots[@]}"; do
    for prompt_group in "${prompt_groups[@]}"; do
        output_path="results/baselinepostfix/cangjie_java_para_out_deepseek-v2.5_${prompt_group}_${i}_shot"
        python test_model_api_icl.py --lang java \
            --few-shot-num $i \
            --input "raw_data/cangjie_para_clean_full" \
            --output ${output_path} \
            --prompt-path resources/prompts/${prompt_group}.json \
            --example-path resources/examples/leetcode_java_examples.jsonl \
            --model "deepseek-ai/DeepSeek-V2.5" \
            --base-url "https://api.siliconflow.cn/v1" \
            --api-key "sk-xxxx"
        python check_compile_results.py --input ${output_path}
        python check_execution_results.py --input ${output_path} --auto-fix --fix-steps "simple,rule,llm"
        python scripts/rq1/collect_execution_results.py --input ${output_path}
    done
done

# gpt-3.5-turbo-1106
for i in "${fewshots[@]}"; do
    for prompt_group in "${prompt_groups[@]}"; do
        output_path="results/baselinepostfix/cangjie_java_para_out_gpt-3.5-turbo-1106_${prompt_group}_${i}_shot"
        python test_model_api_icl.py --lang java \
            --few-shot-num $i \
            --input "raw_data/cangjie_para_clean_full" \
            --output ${output_path} \
            --prompt-path resources/prompts/${prompt_group}.json \
            --example-path resources/examples/leetcode_java_examples.jsonl \
            --model "gpt-3.5-turbo-1106" \
            --base-url "https://xxxx.cognitiveservices.azure.com/openai/deployments/gpt-3.5-turbo-1106/chat/completions?api-version=2025-01-01-preview" \
            --api-key "xxxxx"
        python check_compile_results.py --input ${output_path}
        python check_execution_results.py --input ${output_path} --auto-fix --fix-steps "simple,rule,llm"
        python scripts/rq1/collect_execution_results.py --input ${output_path}
    done
done

# gpt-4o-2024-05-13
for i in "${fewshots[@]}"; do
    for prompt_group in "${prompt_groups[@]}"; do
        output_path="results/baselinepostfix/cangjie_java_para_out_gpt-4o-2024-05-13_${prompt_group}_${i}_shot"
        python test_model_api_icl.py --lang java \
            --few-shot-num $i \
            --input "raw_data/cangjie_para_clean_full" \
            --output ${output_path} \
            --prompt-path resources/prompts/${prompt_group}.json \
            --example-path resources/examples/leetcode_java_examples.jsonl \
            --model "gpt-4o-2024-05-13" \
            --base-url "https://xxxx.cognitiveservices.azure.com/openai/deployments/gpt-4o-2024-05-13/chat/completions?api-version=2025-01-01-preview" \
            --api-key "xxxxx"
        python check_compile_results.py --input ${output_path}
        python check_execution_results.py --input ${output_path} --auto-fix --fix-steps "simple,rule,llm"
        python scripts/rq1/collect_execution_results.py --input ${output_path}
    done
done

# Qwen2.5-72B-Instruct
for i in "${fewshots[@]}"; do
    for prompt_group in "${prompt_groups[@]}"; do
        output_path="results/baselinepostfix/cangjie_java_para_out_qwen2.5-72b-instruct_${prompt_group}_${i}_shot"
        python test_model_api_icl.py --lang java \
            --few-shot-num $i \
            --input "raw_data/cangjie_para_clean_full" \
            --output ${output_path} \
            --prompt-path resources/prompts/${prompt_group}.json \
            --example-path resources/examples/leetcode_java_examples.jsonl \
            --model "qwen2.5-72b-instruct" \
            --base-url "https://dashscope.aliyuncs.com/compatible-mode/v1" \
            --api-key "sk-df9c2c993dec448098f915116dbfacc0"
        python check_compile_results.py --input ${output_path}
        python check_execution_results.py --input ${output_path} --auto-fix --fix-steps "simple,rule,llm"
        python scripts/rq1/collect_execution_results.py --input ${output_path}
    done
done


# Compiler feedback Effectiveness
python check_compile_results.py --input results/cangjie_para_out/ --ignore-failure
python check_compile_results.py --input results/cangjie_para_feedback_kto_out_step200/ --ignore-failure
python scripts/rq1/collect_execution_results.py --input "results/cangjie_para_out/"
python scripts/rq1/collect_execution_results.py --input "results/cangjie_para_feedback_kto_out_step200/"
python scripts/rq2/compare_test_results.py --lhs "results/cangjie_para_out/" --rhs "results/cangjie_para_feedback_kto_out_step200/"


# Rule-based versus LLM-based refinements
python scripts/rq3/count_fix_status.py --input "results/rq1_cangjie_para_out/,results/rq1_leetcode_nonpara_out/"

# Discussion

# Case Study
python scripts/discussion_casestudy/error_statistic.py --input "results/rq1_cangjie_para_out/,results/rq1_leetcode_nonpara_out/"

# Process metrics
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/discussion_cangjie_para_out_step1000" --model "cangjie-qwen2-7b/lora/sft/checkpoint-1000" --device cuda:1
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/discussion_cangjie_para_out_step2000" --model "cangjie-qwen2-7b/lora/sft/checkpoint-2000" --device cuda:1
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/discussion_cangjie_para_out_step3000" --model "cangjie-qwen2-7b/lora/sft/checkpoint-3000" --device cuda:1
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/discussion_cangjie_para_out_step4000" --model "cangjie-qwen2-7b/lora/sft/checkpoint-4000" --device cuda:1
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/discussion_cangjie_para_out_step5000" --model "cangjie-qwen2-7b/lora/sft/checkpoint-5000" --device cuda:1
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/discussion_cangjie_para_out_step6000" --model "cangjie-qwen2-7b/lora/sft/checkpoint-6000" --device cuda:1
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/discussion_cangjie_para_out_step7000" --model "cangjie-qwen2-7b/lora/sft/checkpoint-7000" --device cuda:1
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/discussion_cangjie_para_out_step8000" --model "cangjie-qwen2-7b/lora/sft/checkpoint-8000" --device cuda:1
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/discussion_cangjie_para_out_step9000" --model "cangjie-qwen2-7b/lora/sft/checkpoint-9000" --device cuda:1
python test_model.py --lang java --input "raw_data/cangjie_para_clean" --output "results/discussion_cangjie_para_out_step10000" --model "cangjie-qwen2-7b/lora/sft/checkpoint-10000" --device cuda:1


# Syntax Errors
python check_compile_results.py --input results/discussion_cangjie_para_out_step1000
python check_compile_results.py --input results/discussion_cangjie_para_out_step2000
python check_compile_results.py --input results/discussion_cangjie_para_out_step3000
python check_compile_results.py --input results/discussion_cangjie_para_out_step4000
python check_compile_results.py --input results/discussion_cangjie_para_out_step5000
python check_compile_results.py --input results/discussion_cangjie_para_out_step6000
python check_compile_results.py --input results/discussion_cangjie_para_out_step7000
python check_compile_results.py --input results/discussion_cangjie_para_out_step8000
python check_compile_results.py --input results/discussion_cangjie_para_out_step9000
python check_compile_results.py --input results/discussion_cangjie_para_out_step10000

# Execution Errors
python check_execution_results.py --input results/discussion_cangjie_para_out_step1000/ --auto-fix --fix-steps "simple,rule,llm"
python check_execution_results.py --input results/discussion_cangjie_para_out_step2000/ --auto-fix --fix-steps "simple,rule,llm"
python check_execution_results.py --input results/discussion_cangjie_para_out_step3000/ --auto-fix --fix-steps "simple,rule,llm"
python check_execution_results.py --input results/discussion_cangjie_para_out_step4000/ --auto-fix --fix-steps "simple,rule,llm"
python check_execution_results.py --input results/discussion_cangjie_para_out_step5000/ --auto-fix --fix-steps "simple,rule,llm"
python check_execution_results.py --input results/discussion_cangjie_para_out_step6000/ --auto-fix --fix-steps "simple,rule,llm"
python check_execution_results.py --input results/discussion_cangjie_para_out_step7000/ --auto-fix --fix-steps "simple,rule,llm"
python check_execution_results.py --input results/discussion_cangjie_para_out_step8000/ --auto-fix --fix-steps "simple,rule,llm"
python check_execution_results.py --input results/discussion_cangjie_para_out_step9000/ --auto-fix --fix-steps "simple,rule,llm"
python check_execution_results.py --input results/discussion_cangjie_para_out_step10000/ --auto-fix --fix-steps "simple,rule,llm"

# Collect Execution Errors
python scripts/rq1/collect_execution_results.py --input "results/discussion_cangjie_para_out_step1000/"
python scripts/rq1/collect_execution_results.py --input "results/discussion_cangjie_para_out_step2000/"
python scripts/rq1/collect_execution_results.py --input "results/discussion_cangjie_para_out_step3000/"
python scripts/rq1/collect_execution_results.py --input "results/discussion_cangjie_para_out_step4000/"
python scripts/rq1/collect_execution_results.py --input "results/discussion_cangjie_para_out_step5000/"
python scripts/rq1/collect_execution_results.py --input "results/discussion_cangjie_para_out_step6000/"
python scripts/rq1/collect_execution_results.py --input "results/discussion_cangjie_para_out_step7000/"
python scripts/rq1/collect_execution_results.py --input "results/discussion_cangjie_para_out_step8000/"
python scripts/rq1/collect_execution_results.py --input "results/discussion_cangjie_para_out_step9000/"
python scripts/rq1/collect_execution_results.py --input "results/discussion_cangjie_para_out_step10000/"

# Draw Process Metrics
python scripts/discussion_process/draw_syntax_process.py
