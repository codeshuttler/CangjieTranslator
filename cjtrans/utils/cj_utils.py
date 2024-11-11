

import random
import re


def remove_comments(string: str):
    s = string
    # Use regular expressions to remove "/*" comments
    pattern = r"/\*.*?\*/"
    s = re.sub(pattern, "", s, flags=re.DOTALL)
    # Use regular expressions to remove "//" comments
    pattern = r"//.*?(?=\n|$)"
    s = re.sub(pattern, "", s)

    return s.lstrip()


def get_leading_spaces(line: str) -> int:
    """Return the number of leading spaces in a line."""
    return len(line) - len(line.lstrip())

def remove_indentation(java_code: str) -> str:
    # Split the input string into lines
    lines = java_code.splitlines()

    # Filter out empty lines and calculate leading spaces for non-empty lines
    leading_spaces = [get_leading_spaces(line) for line in lines if line.strip()]
    
    # Get the minimum leading spaces across all non-empty lines
    if leading_spaces:
        min_leading_spaces = min(leading_spaces)
    else:
        return java_code  # Return the original code if it's empty or all lines are empty
    
    # Remove min_leading_spaces from each line if possible
    no_indentation_lines = [line[min_leading_spaces:] if len(line) >= min_leading_spaces else line for line in lines]
    
    # Join the processed lines back into a single string
    return "\n".join(no_indentation_lines)
