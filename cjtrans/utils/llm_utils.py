from collections import defaultdict
from typing import List, Union
import transformers


def generate_ngrams(text: str, n: int, mode: str = "char") -> List[str]:
    """
    Generate N-Grams from the input text.
    :param text: Input text string
    :param n: Length of the N-Gram
    :param mode: 'char' for character-level, 'word' for word-level
    :return: List of N-Grams
    """
    if mode == "word":
        words = text.lower().split()
        return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]
    else:
        return [text[i : i + n] for i in range(len(text) - n + 1)]


def generate_ngrams_from_llm_tokenizer(
    tokenizer: Union[
        transformers.PreTrainedTokenizer, transformers.PreTrainedTokenizerFast
    ],
    text: str,
    n: int,
) -> List[str]:
    """
    Generate N-Grams using a pre-trained tokenizer.
    :param tokenizer: Pre-trained tokenizer from Hugging Face Transformers
    :param text: Input text string
    :param n: Length of the N-Gram
    :param mode: 'char' for character-level, 'word' for word-level
    :return: List of N-Grams
    """
    tokens = tokenizer.tokenize(text)
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]



def calculate_repetition_ratio(ngrams: List[str]) -> float:
    """
    Calculate the repetition ratio of N-Grams.
    :param ngrams: List of N-Grams
    :return: Repetition ratio (float)
    """
    freq = defaultdict(int)
    for gram in ngrams:
        freq[gram] += 1
    total_grams = len(ngrams)
    repeated_grams = sum(count for count in freq.values() if count > 1)
    return repeated_grams / total_grams if total_grams > 0 else 0.0


def filter_by_repetition_ratio(
    text: str,
    n: int,
    min_ratio: float,
    max_ratio: float,
    mode: str = "subword",
) -> bool:
    """
    Filter the text based on N-Gram repetition ratio.
    :param text: Input text string
    :param n: Length of the N-Gram
    :param min_ratio: Minimum allowed repetition ratio (0.0 to 1.0)
    :param max_ratio: Maximum allowed repetition ratio (0.0 to 1.0)
    :param mode: 'char' for character-level, 'word' for word-level, 'subword' for subword-level
    :return: Boolean indicating whether to keep the text (True/False)
    """
    # load qwen2 tokenizer
    if mode == "subword":
        tokenizer = transformers.AutoTokenizer.from_pretrained("Qwen/Qwen2-7B")
        ngrams = generate_ngrams_from_llm_tokenizer(tokenizer, text, n)
    else:
        ngrams = generate_ngrams(text, n, mode)
    ratio = calculate_repetition_ratio(ngrams)
    return min_ratio <= ratio <= max_ratio


if __name__ == "__main__":
    # 示例使用
    path = "results/leetcode_java_nonpara_out/cheapest-flights-within-k-stops/cj_target_translation.cj"
    path = "results/leetcode_java_nonpara_out/alien-dictionary/cj_target_translation.cj"
    path = "results/leetcode_java_nonpara_out/maximum-sum-of-two-non-overlapping-subarrays/cj_target_translation_fixed.cj"
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
    # text = "This is a sample text for testing the N-Gram repetition ratio filtering."
    n = 3  # N-Gram 的长度
    min_ratio = 0.05
    max_ratio = 0.5
    mode = "subword"  # 或者 'char'

    should_keep = filter_by_repetition_ratio(text, n, min_ratio, max_ratio, mode)
    print(f"Should keep the text: {should_keep}")
