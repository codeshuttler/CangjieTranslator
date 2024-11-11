
from typing import List
import tqdm
import tree_sitter_java as tsjava
from tree_sitter import Language, Parser, Node

def get_cyclomatic_complexity(code: str) -> int:

    JAVA_LANGUAGE = Language(tsjava.language())
    parser = Parser(JAVA_LANGUAGE)
    tree = parser.parse(code.encode(), encoding="utf8")
    
    def count_cc(node: Node):
        if node.type == 'ERROR':
            return 0, 0, 0
        cond_count = 0
        loop_count = 0
        case_count = 0
        if node.type in  ["for_statement", "while_statement", "do_statement"]:
            cond_count += 1
        elif node.type in  ["if_statement"]:
            alternative = node.child_by_field_name("alternative")
            if alternative is not None:
                loop_count += 2
            else:
                loop_count += 1
        elif node.type in  ["switch_label"]:
            if node.children[0].type != "default":
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
        if node.type == 'method_declaration':
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
static String f_gold(String num) {
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
    out = get_cyclomatic_complexity(code)
    print(out)