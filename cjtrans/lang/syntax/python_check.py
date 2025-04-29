
import re
from typing import List, Tuple
import os

import tree_sitter_python as tspy
from tree_sitter import Language, Parser, Node, Tree
from .tree_sitter_utils import has_error

def check_grammar(python_code: str) -> bool:
    PYTHON_LANGUAGE = Language(tspy.language())
    parser = Parser(PYTHON_LANGUAGE)
    tree = parser.parse(python_code.encode(), encoding="utf8")
    return has_error(tree.root_node)

def parse_python(python_code: str) -> Tree:
    PYTHON_LANGUAGE = Language(tspy.language())
    parser = Parser(PYTHON_LANGUAGE)
    tree = parser.parse(python_code.encode(), encoding="utf8")
    return tree

