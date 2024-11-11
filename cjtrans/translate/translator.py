

from typing import List, Optional, Union
from cjtrans.lm_inference import ModelPredictor
from cjtrans.openai_inference import OpenaiModelPredictor


JAVA_EXAMPLES = [
    {"role": "user", "content": """long f_gold (int m) {
    int count[] = new int[m * 2];     
    int sum_value = 0;
    for (int i = 0; i < m; ++i)
        sum_value = sum_value + (i % 2 == 0? i : -i)
    return Math.max((long)sum_value, 0) + long(count[m]);
}"""},
    {"role": "assistant", "content": """func f_gold(m: Int32): Int64 {
    let count = Array<Int32>(m * 2, item:0)
    var sum_value = 0i32
    for (i in 0..Int64(m)) {
        if (i % 2 == 0) {
            sum_value = sum_value + Int32(i)
        } else {
            sum_value = sum_value - Int32(i)
        }
    }
    math.max(Int64(sum_value), 0) + Int64(count[Int64(m)])
}"""},
    {"role": "user", "content": """import java.lang.*;
import java.util.*;
public class HelloWorld {
  public static void main(String args[]) {
    system.out.println("Hello World!");
  }
}"""},
    {"role": "assistant", "content": """main() {
  println("Hello World!")
}"""},
        {"role": "user", "content": """class TreeNode<T> {
    T val;
    TreeNode left;
    TreeNode right;

    TreeNode(T x) {
        val = x;
    }
}
public void preorderTraversal(TreeNode root) {
    if (root == null) {
        return;
    }
    // 访问根节点
    System.out.print(root.val + " ");
    // 遍历左子树
    preorderTraversal(root.left);
    // 遍历右子树
    preorderTraversal(root.right);
}
public class Main {
  public static void main(String[] args) {
    TreeNode<Int> nodeA = new TreeNode<>(3);
    System.out.println(nodeA.val); // Output: 3

    TreeNode<Boolean> nodeB = new TreeNode<>(true);
    System.out.println(nodeA.val); // Output: true

    TreeNode<Double> nodeA = new TreeNode<>(3.14);
    System.out.println(nodeA.val); // Output: 3.14
  }
}"""},
    {"role": "assistant", "content": """public class TreeNode<T> {
    var val: Int64
    var left: ?TreeNode<T>
    var right: ?TreeNode<T>

    public init(x: Int64) {
        val = x;
    }
}
public func preorderTraversal(root: ?TreeNode<T>): Unit {
  if (let Some(node) <- root) {
    // 访问根节点
    print(node.val.getOrThrow())
    // 遍历左子树
    preorderTraversal(node.left)
    // 遍历右子树
    preorderTraversal(node.right)
  }
}
main() {
  var nodeA = TreeNode<Int64>(3)
  println(nodeA.val) // Output: 3

  var nodeB = TreeNode<Bool>(true)
  println(nodeA.val) // Output: true

  var nodeA = TreeNode<Float64>(3.14)
  println(nodeA.val) // Output: 3.14
}"""},
]



PYTHON_EXAMPLES = [
    {"role": "user", "content": """s=str(input())
def function(s):
    a=0
    h=0
    m=0
    n=len(s)
    counter=0
    if n<9:
        return 0
    while a<n-4:
        if s[a:a+5]=="heavy":
            h+=1
            a+=4
        if s[a:a+5]=="metal":
            m+=1
            counter+=h
            a+=4
        a+=1
    return counter
print(function(s))
"""},
    {"role": "assistant", "content": """func function(s: String): Int64 {
    var a = 0
    var h = 0
    var m = 0
    var n = s.size
    var counter = 0
    if (n < 9) {
        return 0
    }
    while (a < n - 4) {
        if (s[a..a + 5] == "heavy") {
            h = h + 1
            a = a + 4
        }
        if (s[a..a + 5] == "metal") {
            m = m + 1
            counter = counter + h
            a = a + 4
        }
        a = a + 1
    }
    return counter
}
main() {
    let s = readln()
    println(function(s))
}
"""},
]

class Translator(object):
    def __init__(self, inference_engine: Union[ModelPredictor, OpenaiModelPredictor]) -> None:
        self.inference_engine = inference_engine
    
    def index_document(self, doc_names: List[str], error_message: str,
            do_sample: Optional[bool] = None,
            num_beams: Optional[int] = None,
            temperature: Optional[float] = None,
            top_k: Optional[int] = None,
            top_p: Optional[float] = None,):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"""Here is a series of document filenames for a new language {doc_names}.
When I write some code in a new language, I got this error from compiler:
{error_message}.
Please provide the filename that could help resolve the compiler error, and enclose them in triple backticks, for example ```option.txt```.
"""},
        ]
        return self.inference_engine.chat(messages=messages, max_new_tokens=512,
            do_sample=do_sample,
            num_beams=num_beams,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p
        )
    
    def correct_code(self, cj_code: str,
            error_message: str,
            related_doc: Optional[str]=None,
            do_sample: Optional[bool] = None,
            num_beams: Optional[int] = None,
            temperature: Optional[float] = None,
            top_k: Optional[int] = None,
            top_p: Optional[float] = None,):
        if len(cj_code) > 4096:
            cj_code = cj_code[:4096]
        if related_doc is not None:
            related_doc_prompt = f"Here is the document of a new language:\n{related_doc}\nPlease reference the document answer following questions."
        else:
            related_doc_prompt = ""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            # {"role": "user", "content": f"Here is a snippet cangjie code: \n```cangjie\n{example_cj_code}\n```\nCompiler gives this error message: \n{example_error_message}\n Please give the correct cangjie code (Type mismatch can be converted.)."},
            # {"role": "assistant", "content": example_out},
            {"role": "user", "content": f"""{related_doc_prompt}Here is a snippet cangjie code:
```cangjie
{cj_code}
```
Cangjie Compiler gives this error message:
{error_message}

Please guess the language feature and give the correct cangjie code directly according to the compiler output."""},
        ]
        return self.inference_engine.chat(messages=messages, max_new_tokens=4096,
            do_sample=do_sample,
            num_beams=num_beams,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p
        )
    
    def translate(self, source_code: str,
            source_lang: str = "java",
            few_shot_num: int = 1,
            do_sample: Optional[bool] = None,
            num_beams: Optional[int] = None,
            temperature: Optional[float] = None,
            top_k: Optional[int] = None,
            top_p: Optional[float] = None,):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Please avoid directly modifying parameters in functions; instead, modify the copy. Please convert the following {source_lang} code into Cangjie:"},
            {"role": "assistant", "content": "OK, I will provide your translation."},
        ]
        if source_lang == "java":
            if few_shot_num > 0:
                messages.extend(JAVA_EXAMPLES[:few_shot_num*2])
        elif source_lang == "python":
            if few_shot_num > 0:
                messages.extend(PYTHON_EXAMPLES[:few_shot_num*2])
        messages.append({"role": "user", "content": source_code})
        return self.inference_engine.chat(messages=messages, max_new_tokens=4096,
            do_sample=do_sample,
            num_beams=num_beams,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p
        )