
import re
from typing import List, Tuple
import os

import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser, Node, Tree
from .tree_sitter_utils import has_error

def check_grammar(cpp_code: str) -> bool:
    CPP_LANGUAGE = Language(tscpp.language())
    parser = Parser(CPP_LANGUAGE)
    tree = parser.parse(cpp_code.encode(), encoding="utf8")
    return has_error(tree.root_node)

def parse_cpp(cpp_code: str) -> Tree:
    CPP_LANGUAGE = Language(tscpp.language())
    parser = Parser(CPP_LANGUAGE)
    tree = parser.parse(cpp_code.encode(), encoding="utf8")
    return tree

