from typing import List
import tqdm
import tree_sitter_cangjie as tscangjie
from tree_sitter import Language, Parser, Node

def count_function_parameters(code: str) -> int:
    CJ_LANGUAGE = Language(tscangjie.language())
    parser = Parser(CJ_LANGUAGE)
    tree = parser.parse(code.encode(), encoding="utf8")
    
    def count_params(node: Node) -> int:
        param_count = 0
        if node.type == "function_parameters":
            for child in node.children:
                if child.type not in ['unnamed_parameter_list', 'named_parameter_list']:
                    continue
                for subchild in child.children:
                    if subchild.type in ['unnamed_parameter', 'named_parameter', 'default_parameter']:
                        param_count += 1
        else:
            for n in node.children:
                param_count += count_params(n)
        return param_count
    
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
        ret.append(count_params(method))
    return ret

if __name__ == "__main__":
    code = """

from std import collection.*
from std import sort.*
from std import math.*

func isOneBitCharacter(bits: Array<Int32>, a: Int32, c !: Int64 = 0): Bool {
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
    out = count_function_parameters(code)
    print(out)