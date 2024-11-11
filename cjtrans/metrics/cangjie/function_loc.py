from typing import List
import tqdm
import tree_sitter_cangjie as tscangjie
from tree_sitter import Language, Parser, Node

def count_function_loc(code: str) -> int:
    CJ_LANGUAGE = Language(tscangjie.language())
    parser = Parser(CJ_LANGUAGE)
    tree = parser.parse(code.encode(), encoding="utf8")
    
    def get_loc(node: Node) -> int:
        start_line = node.start_point[0]
        end_line = node.end_point[0]
        return end_line - start_line + 1
    
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
        ret.append(get_loc(method))
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
    out = count_function_loc(code)
    print(out)