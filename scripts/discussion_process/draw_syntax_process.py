syntax_error_count_data = {
    1000: 14,
    2000: 92,
    3000: 11,
    4000: 19,
    5000: 12,
    6000: 7,
    7000: 26,
    8000: 14,
    9000: 6,
    10000: 16,
    10221: 6
}

compile_error_count_data = {
    1000: 43,
    2000: 68,
    3000: 30,
    4000: 41,
    5000: 39,
    6000: 41,
    7000: 40,
    8000: 39,
    9000: 31,
    10000: 31,
    10221: 31
}

# plot training process
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

plt.rcParams['font.family'] = 'Times New Roman'
sns.set_style("whitegrid")

data = {
    "Step": [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 10221],
    "Syntax Error Count": [14, 92, 11, 19, 12, 7, 26, 14, 6, 16, 6],
    "Compile Error Count": [43, 68, 30, 41, 39, 41, 40, 39, 31, 31, 31],
}


df_data = {
    "step": [],
    "count": [],
    "type": [],
}

for step, count in syntax_error_count_data.items():
    df_data["step"].append(step)
    df_data["count"].append(count)
    df_data["type"].append("syntax")

for step, count in compile_error_count_data.items():
    df_data["step"].append(step)
    df_data["count"].append(count)
    df_data["type"].append("compile")

df = pd.DataFrame(df_data)
plt.figure(figsize=(3.5, 2.5))
sns.lineplot(data=df, x='step', y='count', hue='type', marker='o', markersize=4)

plt.title('Training Process')
plt.xlabel('Step')
plt.ylabel('Error Count')

plt.savefig('figures/training_process.pdf')
