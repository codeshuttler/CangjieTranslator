Language Similarity
===


Java and Cangjie
=====
Java:

{'^', ';', '/=', '--', 'while', '-', '-=', 'void', '==', '|=', '%', 'static', '>', 'else', 'for', ':', 'class', 'long', 'new', 'false', 'null', '(', '!', '.', ']', '&&', '^=', '<', '!=', ')', '<=', '*=', '++', '||', '=', '*', 'return', '{', 'char', '&=', 'continue', 'case', 'boolean', '+=', '&', '>>', 'break', 'switch', '<<', 'if', '>=', 'true', '>>=', ',', 'public', '"', '/', 'import', 'double', '}', '+', 'int', '[', '?'}

Cangjie:

{'^', ';', '/=', '--', 'Int64', 'while', '..', '-', '-=', '==', 'main', '|=', 'open', '%', '>', 'else', '??', 'for', ':', 'var', 'false', 'get', 'let', '(', '!', ']', '&&', '^=', '<', 'Float32', '!=', ')', '<=', '*=', '++', '||', '=', 'Rune', '*', 'return', '{', '&=', '_', '..=', 'continue', 'Float64', 'case', '&', '+=', '>>', 'from', 'break', '<<', '//', 'match', "'", '${', 'if', 'true', '>=', '>>=', ',', '"', 'in', '/', 'Int32', 'import', '}', '+', 'func', '[', '.', '=>'}

Token set 1 size: 64

Token set 2 size: 73

Jaccard Similarity: 0.5930

Common tokens: 51


C++ and Cangjie
=====
C++:

{')', 'while', '>=', '||', 'else', 'using', '|=', 'return', 'auto', '<', 'bool', 'unsigned', '}', 'continue', ',', '^=', '==', 'switch', '%', 'size_t', '#include', 'const', 'char', '>>', '^', 'int', '{', '!=', '"', '.', 'true', 'break', ':', 'delete', '::', 'sizeof', 'and', '&=', '\\n', '-=', 'for', 'false', '+=', 'case', '/', '<=', '>>=', ']', '/=', 'double', '*=', '[', '\\0', '-', '&', "'", '?', '--', '!', 'void', ';', '(', 'long', '+', 'float', 'std', '&&', 'new', 'if', '->', '=', 'namespace', '++', '*', '>', '<<'}

Cangjie:

{')', 'while', '>=', '||', 'else', 'Float64', '|=', '..', 'return', '??', 'Float32', '..=', '<', '}', 'match', 'continue', '_', ',', '^=', 'get', 'Int64', '==', '%', 'var', 'main', 'func', 'Rune', 'import', '>>', '^', '{', '!=', '"', ':', '.', 'true', 'break', 'Int32', 'open', '&=', '//', '-=', 'for', 'false', '+=', 'case', '/', '<=', '>>=', ']', '/=', '${', '[', '*=', '-', '&', "'", '--', '=>', '!', 'from', ';', '(', '+', 'let', '&&', 'if', '=', '++', '*', '>', '<<', 'in'}

Token set 1 size: 76

Token set 2 size: 73

Jaccard Similarity: 0.5204

Common tokens: 51

Python and Cangjie
=====

Python:

{';', ')', 'from', ':', 'else', '>>=', '/=', '=', '/', '%', '&', 'def', '*=', 'return', 'False', 'if', '//', 'and', '~', 'in', '^', 'None', 'while', '+=', '>', '[', '//=', 'not', '<', '**', '<<', ']', '}', 'import', '<=', '|=', '>>', '{', '-', 'True', 'break', '-=', ',', '&=', '!=', '*', 'for', 'continue', 'or', '.', '(', 'elif', '>=', '->', 'as', 'lambda', '+', '=='}

Cangjie:

{';', 'Float32', ')', 'from', 'main', 'Int32', 'else', '>>=', '=', '/', '&&', '&', '*=', 'return', 'match', 'if', '//', 'while', '+=', '>', '=>', '<', 'Float64', 'get', '..', '"', '<<', 'import', ']', '<=', '|=', 'func', '-=', '&=', 'Int64', '--', '*', 'for', 'var', "'", '.', '(', 'false', '>=', '!', '+', '==', ':', '/=', '%', '_', 'in', '^', '[', 'true', '??', '++', '}', '>>', '{', '-', '||', '${', 'break', 'case', ',', '!=', 'continue', '^=', '..=', 'open', 'Rune', 'let'}

Token set 1 size: 58

Token set 2 size: 73

Jaccard Similarity: 0.5057

Common tokens: 44