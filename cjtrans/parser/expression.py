from typing import List
from cjtrans.parser.tokenizer import Token

def is_type_cast_token(token):
    return token.type == "IDENTIFIER" and (token.value.startswith("Int") or token.value.startswith("Float") or token.value.startswith("Char"))

class ExpressionExtractor:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens

    def find_expressions_around_token(self, bin_op_idx: int):
        """Find the left and right expressions around Token"""
        left_expr = self.extract_left_expression(bin_op_idx - 1)
        right_expr = self.extract_right_expression(bin_op_idx + 1)
        return left_expr, right_expr

    def extract_left_expression(self, index):
        """Extract the expression to the left of the PLUS token."""
        stack = []
        expr = []

        while index >= 0:
            token = self.tokens[index]

            if token.type == 'RPAREN':
                stack.append(token)
            elif token.type == 'RBRACKET':
                stack.append(token)
            elif token.type == 'RBRACE':
                stack.append(token)
            elif token.type in ['LPAREN', 'LBRACKET', 'LBRACE']:
                if stack:
                    r_token = stack.pop()
                    target_t = 'L' + r_token.type[1:]
                    if target_t != token.type:
                        break
                else:
                    expr.insert(0, token)
                    break  # Stop at the matching opening parenthesis
            
            expr.insert(0, token)
            if not stack and token.type not in ['RPAREN', 'LPAREN', 'RBRACKET', 'LBRACKET', 'RBRACE', 'LBRACE', 'ASSIGN']:
                break  # Found a complete expression

            index -= 1

        if len(expr) >= 0:
            fst_token = expr[0]
            if is_type_cast_token(fst_token):
                pass
            elif fst_token.type == "IDENTIFIER":
                pass
            elif fst_token.type in ["FLOAT", "NUMBER"]:
                pass
            else:
                expr.pop(0)
        return expr

    def extract_right_expression(self, index):
        """Extract the expression to the right of the PLUS token."""
        stack = []
        expr = []

        while index < len(self.tokens):
            token = self.tokens[index]

            if token.type == 'LPAREN':
                stack.append(token)
            elif token.type == 'LBRACKET':
                stack.append(token)
            elif token.type == 'LBRACE':
                stack.append(token)
            elif token.type in ['RPAREN', 'RBRACKET', 'RBRACE']:
                if stack:
                    l_token = stack.pop()
                    target_t = 'R' + l_token.type[1:]
                    if target_t != token.type:
                        break
                else:
                    expr.append(token)
                    break  # Stop at the matching opening parenthesis
            
            if token.type == "EOF":
                break
            expr.append(token)
            
            if index + 1 < len(self.tokens):
                cur_token = self.tokens[index]
                next_token = self.tokens[index + 1]
                if next_token.type in ["DOT", "LBRACKET", "LPAREN"]:
                    index += 1
                    continue
                
                if cur_token.type in ["DOT",] and next_token.type == "IDENTIFIER":
                    index += 1
                    continue

            if not stack and token.type not in ['LPAREN', 'RPAREN', 'RBRACKET', 'LBRACKET', 'RBRACE', 'LBRACE'] and not is_type_cast_token(token):
                break  # Found a complete expression

            index += 1

        return expr