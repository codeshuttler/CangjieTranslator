class CangjieASTNode:
    def __init__(self, node_type, value=None, children=None):
        self.node_type = node_type
        self.value = value
        self.children = children if children is not None else []

    def __repr__(self):
        if self.children:
            return f"{self.node_type}({self.value}, {self.children})"
        return f"{self.node_type}({self.value})"

class CangjieParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos] if self.tokens else None

    def parse(self):
        statements = []
        while self.current_token and self.current_token.type != 'EOF':
            if self.current_token.type == 'WHILE':
                statements.append(self.parse_while())
            elif self.current_token.type == 'IF':
                statements.append(self.parse_if())
            else:
                statements.append(self.parse_assignment())
        return CangjieASTNode('Program', children=statements)

    def parse_assignment(self):
        # Parse the assignment expression: identifier = expression;
        identifier = self.expect('IDENTIFIER')
        self.expect('ASSIGN')
        expression = self.parse_expression()
        self.expect('SEMICOLON')
        return CangjieASTNode('Assignment', value=identifier.value, children=[expression])

    def parse_if(self):
        # Parse the if statement: if (condition) statement
        self.expect('IF')
        self.expect('LPAREN')
        condition = self.parse_expression()
        self.expect('RPAREN')
        then_branch = self.parse_statement()
        return CangjieASTNode('IfStatement', children=[condition, then_branch])

    def parse_while(self):
        # Parse the while loop: while (condition) statement
        self.expect('WHILE')
        self.expect('LPAREN')
        condition = self.parse_expression()
        self.expect('RPAREN')
        body = self.parse_statement()
        return CangjieASTNode('WhileLoop', children=[condition, body])

    def parse_statement(self):
        # Parse a statement, which could be an assignment, if, or while
        if self.current_token.type == 'IDENTIFIER':
            return self.parse_assignment()
        elif self.current_token.type == 'IF':
            return self.parse_if()
        elif self.current_token.type == 'WHILE':
            return self.parse_while()
        else:
            raise Exception(f"Unexpected token: {self.current_token}")

    def parse_expression(self):
        # Parse expressions which can have additive and multiplicative operators
        return self.parse_additive_expression()

    def parse_additive_expression(self):
        # Handle '+' and '-' operators
        left = self.parse_multiplicative_expression()
        while self.current_token and self.current_token.type in ['PLUS', 'MINUS']:
            op = self.current_token
            self.advance()
            right = self.parse_multiplicative_expression()
            left = CangjieASTNode('BinaryOp', value=op.type, children=[left, right])
        return left

    def parse_multiplicative_expression(self):
        # Handle '*' and '/' operators
        left = self.parse_primary()
        while self.current_token and self.current_token.type in ['STAR', 'SLASH']:
            op = self.current_token
            self.advance()
            right = self.parse_primary()
            left = CangjieASTNode('BinaryOp', value=op.type, children=[left, right])
        return left

    def parse_primary(self):
        # Parse primary expressions: identifiers, numbers, and parentheses
        if self.current_token.type == 'IDENTIFIER':
            identifier = self.current_token
            self.advance()
            return CangjieASTNode('Identifier', value=identifier.value)
        elif self.current_token.type == 'NUMBER':
            number = self.current_token
            self.advance()
            return CangjieASTNode('Number', value=number.value)
        elif self.current_token.type == 'FLOAT':
            float_number = self.current_token
            self.advance()
            return CangjieASTNode('Float', value=float_number.value)
        elif self.current_token.type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr
        else:
            raise Exception(f"Unexpected token: {self.current_token}")

    def expect(self, token_type):
        if self.current_token and self.current_token.type == token_type:
            token = self.current_token
            self.advance()
            return token
        else:
            raise Exception(f"Expected token type {token_type} but got {self.current_token}")

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

