# pip install javalang

from typing import Optional
import javalang
from javalang.tokenizer import LexerError
from javalang.parser import JavaSyntaxError

def is_valid_java_code(java_code: str):
    try:
        tree = javalang.parse.parse(java_code)
        return True
    except JavaSyntaxError as e:
        print(e.description)
        return False
    except LexerError as e:
        print(e)
        return False

def get_java_code_errors(java_code: str) -> Optional[str]:
    try:
        tree = javalang.parse.parse(java_code)
        return None
    except JavaSyntaxError as e:
        print(e.description, e.at)
        return str(e.description) + "===\n===" + str(e.at)
    except LexerError as e:
        print(e)
        return str(e)
    except StopIteration as e:
        print(e)
        return str(e)
    except TypeError as e:
        print(e)
        return str(e)
    except RecursionError as e:
        print(e)
        return str(e)

if __name__ == "__main__":
    java_code = """
    public class Main {
        public static void main(String[] args) {
            System.out.println("Hello, World!");
        }?
    }
    """

    if is_valid_java_code(java_code):
        print("输入的 Java 代码是合法的！")
    else:
        print("输入的 Java 代码不是合法的！")