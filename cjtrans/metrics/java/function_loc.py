from typing import List
import tqdm
import tree_sitter_java as tsjava
from tree_sitter import Language, Parser, Node

def count_function_loc(code: str) -> int:
    JAVA_LANGUAGE = Language(tsjava.language())
    parser = Parser(JAVA_LANGUAGE)
    tree = parser.parse(code.encode(), encoding="utf8")

    def get_loc(node: Node) -> int:
        start_line = node.start_point[0]
        end_line = node.end_point[0]
        return end_line - start_line + 1
    
    def get_method_declaration(node: Node) -> List[Node]:
        if node.type == 'ERROR':
            return []
        result = []
        if node.type == 'method_declaration':
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
static String f_gold(String num, int a) {
    int l = num.length();
    int i;
    for (i = l - 1; i >= 0; i--) {
        if (num.charAt(i) == '0') {
            num = num.substring(0, i) + '1' + num.substring(i + 1);
            break;
        } else {
            num = num.substring(0, i) + '0' + num.substring(i + 1);
        }
    }

    if (i < 0) {
        num = "1" + num;
    }
    return num;
}

static String f_gold2(String num) {
    int l = num.length();
    int i;
    for (i = l - 1; i >= 0; i--) {
        if (num.charAt(i) == '0') {
            num = num.substring(0, i) + '1' + num.substring(i + 1);
            break;
        } else {
            num = num.substring(0, i) + '0' + num.substring(i + 1);
        }
    }

    return num;
}
"""
    out = count_function_loc(code)
    print(out)