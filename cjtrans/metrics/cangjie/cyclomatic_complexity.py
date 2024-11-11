
from typing import List
import tqdm
import tree_sitter_cangjie as tscangjie

from tree_sitter import Language, Parser, Node

def get_cyclomatic_complexity(code: str) -> int:
    CJ_LANGUAGE = Language(tscangjie.language())
    parser = Parser(CJ_LANGUAGE)
    tree = parser.parse(code.encode(), encoding="utf8")
    
    def count_cc(node: Node):
        if node.type == 'ERROR':
            return 0, 0, 0
        cond_count = 0
        loop_count = 0
        case_count = 0
        if node.type in  ["for_in_expression", "while_expression", "do_while_expression"]:
            cond_count += 1
        elif node.type in  ["if_expression"]:
            alternative = node.child_by_field_name("alternative")
            if alternative is not None:
                loop_count += 2
            else:
                loop_count += 1
        elif node.type in  ["match_case"]:
            if all([c.type != 'wildcard_pattern' for c in node.children]):
                case_count += 1

        for n in node.children:
            c1, c2, c3 = count_cc(n)
            cond_count += c1
            loop_count += c2
            case_count += c3
        return cond_count, loop_count, case_count
    
    def get_method_declaration(node: Node) -> List[Node]:
        if node.type == 'ERROR':
            return []
        result = []
        if node.type == 'function_definition':
            result.append(node)
        for n in node.children:
            result.extend(get_method_declaration(n))
        
        return result
    
    methods = get_method_declaration(tree.root_node)
    ret = []
    for method in methods:
        cond_count, loop_count, case_count = count_cc(method)
        ret.append(1 + cond_count + loop_count + case_count)
    return ret

if __name__ == "__main__":
    code = """

from std import collection.*
from std import sort.*
from std import math.*

func isOneBitCharacter(bits: Array<Int32>): Bool {
    var i = 0
    for (j in 0..bits.size - 1) {
        i += Int64(bits[j])
    }
    while(true) {}
    do {} while (true)
    if (true) {
        
    } else {
        
    }
    match(a) {
        case 1 => 1
        case 2 => 2
        case _ => 3
    }
    return i == bits.size - 1
}
main() {
    println("hello world!")
}
"""
    out = get_cyclomatic_complexity(code)
    print(out)