import re
import sys
from enum import Enum
from collections import namedtuple

class TokenType(Enum):
    NEWLINE = 1
    INDENT = 2
    DEDENT = 3
    IDENTIFIER = 4
    KEYWORD = 5
    LITERAL = 6
    OPERATOR = 7
    DELIMITER = 8
    ERROR = 9

Token = namedtuple('Token', ['type', 'value', 'line', 'column'])

def tokenize(filename):
    tokens = []
    error_count = 0
    with open(filename) as f:
        lines = f.readlines()

    line_number = 0
    indent_stack = [0]

    print("INFO SCAN - Start scanning")

    for line in lines:
        line_number += 1
        indentation = 0
        index = 0

        # Ignora los comentarios
        line = re.sub(r'#.*', '', line)

        # Calcula la indentación
        for ch in line:
            if ch == ' ':
                indentation += 1
            elif ch == '\t':
                indentation = (indentation + 8) & ~7
            else:
                break

        # Ignora las líneas en blanco
        if indentation == len(line.rstrip()):
            continue

        line = line[indentation:]

        # Maneja la indentación
        if indentation > indent_stack[-1]:
            indent_stack.append(indentation)
            tokens.append(Token(TokenType.INDENT, "", line_number, indentation))
        else:
            while indentation < indent_stack[-1]:
                indent_stack.pop()
                tokens.append(Token(TokenType.DEDENT, "", line_number, indentation))

        # Tokeniza la línea
        token_pattern = re.compile(r"(\b(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b)|([a-zA-Z][a-zA-Z0-9_]*)|([{}()[\]:,.])|(\b0\b|([1-9][0-9]*))|->|([=!<>%/*+\-]=?)|(\b0[0-9]+)|(\"(?:[^\"\\]|\\.)*\")")
        search_start = 0

        for match in token_pattern.finditer(line):
            matched = match.group(0)
            if match.group(1):
                token_type = TokenType.KEYWORD
            elif match.group(3):
                token_type = TokenType.IDENTIFIER
            elif match.group(4):
                token_type = TokenType.DELIMITER
            elif match.group(5) or match.group(6):
                token_type = TokenType.LITERAL
                matched_int = int(matched)
                if matched_int > 2147483647:
                    continue
            elif match.group(7):
                token_type = TokenType.OPERATOR
                if matched == "->":
                    token_type = TokenType.OPERATOR
            elif match.group(8):
                continue
            elif match.group(9):
                token_type = TokenType.LITERAL
                if re.search(r'\\[^"]', matched):
                    print(f"Error lexico en la linea {line_number}: '{matched}' (secuencia de escape no reconocida)")
                    error_count += 1
            else:
                token_type = TokenType.OPERATOR

            column = indentation + 1 + (match.start() - search_start)
            tokens.append(Token(token_type, matched, line_number, column))
            search_start = match.end()

        # Líneas nuevas
        tokens.append(Token(TokenType.NEWLINE, "", line_number, len(line) + 1))

        # Manejo de errores léxicos
        if search_start != len(line.rstrip()) and not all(c.isspace() or c == '\t' for c in line[search_start:].rstrip()):
            print(f"Error lexico en la linea {line_number}: '{line[search_start:].rstrip()}'")
            error_count += 1

    # Genera tokens DEDENT al final de la entrada
    while indent_stack[-1] > 0:
        indent_stack.pop()
        tokens.append(Token(TokenType.DEDENT, "", line_number, 0))

    print(f"INFO SCAN - Completed with {error_count} errors")

    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.index = -1
        self.next_token()
    
    def next_token(self):
        self.index += 1
        if self.index < len(self.tokens):
            self.current_token = self.tokens[self.index]
        else:
            self.current_token = None
    
    def match(self, expected_type):
        if self.current_token.type == expected_type:
            self.next_token()
        else:
            self.error(f"Error: Expected {expected_type}, found {self.current_token.type}")
    
    def error(self, message):
        raise Exception(message)
    
    def Program(self):
        self.DefList()
        self.StatementList()
    
    def DefList(self):
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'def':
            self.Def()
            self.DefList()
        else:
            pass  # ε production
    
    def Def(self):
        self.match(TokenType.KEYWORD)
        self.match(TokenType.IDENTIFIER)
        self.match(TokenType.DELIMITER)
        self.TypedVarList()
        self.match(TokenType.DELIMITER)
        self.Return()
        self.match(TokenType.DELIMITER)
        self.Block()
    
    def TypedVar(self):
        self.match(TokenType.IDENTIFIER)
        self.match(TokenType.DELIMITER)
        self.Type()
    
    def Type(self):
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value in ['int', 'str']:
            self.match(TokenType.KEYWORD)
        elif self.current_token.type == TokenType.DELIMITER and self.current_token.value == '[':
            self.match(TokenType.DELIMITER)
            self.Type()
            self.match(TokenType.DELIMITER)
    
    def TypedVarList(self):
        if self.current_token.type == TokenType.IDENTIFIER:
            self.TypedVar()
            self.TypedVarListTail()
        else:
            pass  # ε production
    
    def TypedVarListTail(self):
        if self.current_token.type == TokenType.DELIMITER and self.current_token.value == ',':
            self.match(TokenType.DELIMITER)
            self.TypedVar()
            self.TypedVarListTail()
        else:
            pass  # ε production
    
    def Return(self):
        if self.current_token.type == TokenType.DELIMITER and self.current_token.value == '->':
            self.match(TokenType.DELIMITER)
            self.Type()
        else:
            pass  # ε production
    
    def Block(self):
        self.match(TokenType.KEYWORD)
        self.match(TokenType.KEYWORD)
        self.Statement()
        self.StatementList()
        self.match(TokenType.KEYWORD)
    
    def StatementList(self):
        if self.current_token.type in [TokenType.IDENTIFIER, TokenType.KEYWORD] or \
           (self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'return'):
            self.Statement()
            self.StatementList()
        else:
            pass  # ε production
    
        def Statement(self):
          if self.current_token.type == TokenType.IDENTIFIER:
              self.SimpleStatement()
              self.match(TokenType.NEWLINE)
          elif self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'if':
              self.match(TokenType.KEYWORD)
              self.Expr()
              self.match(TokenType.DELIMITER)
              self.Block()
              self.ElifList()
              self.Else()
          elif self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'while':
              self.match(TokenType.KEYWORD)
              self.Expr()
              self.match(TokenType.DELIMITER)
              self.Block()
          elif self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'for':
              self.match(TokenType.KEYWORD)
              self.match(TokenType.IDENTIFIER)
              self.match(TokenType.KEYWORD)
              self.Expr()
              self.match(TokenType.DELIMITER)
              self.Block()

    def ElifList(self):
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'elif':
            self.match(TokenType.KEYWORD)
            self.Expr()
            self.match(TokenType.DELIMITER)
            self.Block()
            self.ElifList()
        else:
            pass  # ε production

    def Else(self):
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'else':
            self.match(TokenType.KEYWORD)
            self.match(TokenType.DELIMITER)
            self.Block()
        else:
            pass  # ε production

    def SimpleStatement(self):
        self.Expr()
        self.SSTail()

    def SSTail(self):
        if self.current_token.type == TokenType.DELIMITER and self.current_token.value == '=':
            self.match(TokenType.DELIMITER)
            self.Expr()
        else:
            pass  # ε production

    def Expr(self):
        self.orExpr()
        self.ExprPrime()

    def ExprPrime(self):
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'if':
            self.match(TokenType.KEYWORD)
            self.andExpr()
            self.match(TokenType.KEYWORD)
            self.andExpr()
            self.ExprPrime()
        else:
            pass  # ε production

    def orExpr(self):
        self.andExpr()
        self.orExprPrime()

    def orExprPrime(self):
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'or':
            self.match(TokenType.KEYWORD)
            self.andExpr()
            self.orExprPrime()
        else:
            pass  # ε production

    def andExpr(self):
        self.notExpr()
        self.andExprPrime()

    def andExprPrime(self):
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'and':
            self.match(TokenType.KEYWORD)
            self.notExpr()
            self.andExprPrime()
        else:
            pass  # ε production

    def notExpr(self):
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'not':
            self.match(TokenType.KEYWORD)
            self.CompExpr()
        else:
            self.CompExpr()

    def CompExpr(self):
        self.IntExpr()
        self.CompExprPrime()

    def CompExprPrime(self):
        if self.current_token.type == TokenType.OPERATOR and self.current_token.value in ['==', '!=', '<', '>', '<=', '>=', 'is']:
            self.match(TokenType.OPERATOR)
            self.IntExpr()
            self.CompExprPrime()
        else:
            pass  # ε production

    def IntExpr(self):
        self.Term()
        self.IntExprPrime()

        def IntExprPrime(self):
          if self.current_token.type == TokenType.OPERATOR and self.current_token.value == '+':
              self.match(TokenType.OPERATOR)
              self.Term()
              self.IntExprPrime()
          elif self.current_token.type == TokenType.OPERATOR and self.current_token.value == '-':
              self.match(TokenType.OPERATOR)
              self.Term()
              self.IntExprPrime()
          else:
              pass  # ε production

    def Term(self):
        self.Factor()
        self.TermPrime()

    def TermPrime(self):
        if self.current_token.type == TokenType.OPERATOR and self.current_token.value == '*':
            self.match(TokenType.OPERATOR)
            self.Factor()
            self.TermPrime()
        elif self.current_token.type == TokenType.OPERATOR and self.current_token.value == '//':
            self.match(TokenType.OPERATOR)
            self.Factor()
            self.TermPrime()
        elif self.current_token.type == TokenType.OPERATOR and self.current_token.value == '%':
            self.match(TokenType.OPERATOR)
            self.Factor()
            self.TermPrime()
        else:
            pass  # ε production

    def Factor(self):
        if self.current_token.type == TokenType.OPERATOR and self.current_token.value == '-':
            self.match(TokenType.OPERATOR)
            self.Factor()
        elif self.current_token.type == TokenType.IDENTIFIER:
            self.Name()
        elif self.current_token.type == TokenType.LITERAL:
            self.Literal()
        elif self.current_token.type == TokenType.DELIMITER and self.current_token.value == '[':
            self.List()
        elif self.current_token.type == TokenType.DELIMITER and self.current_token.value == '(':
            self.match(TokenType.DELIMITER)
            self.Expr()
            self.match(TokenType.DELIMITER)
        else:
            self.error("Factor")

    def Name(self):
        self.match(TokenType.IDENTIFIER)
        self.NameTail()

    def NameTail(self):
        if self.current_token.type == TokenType.DELIMITER and self.current_token.value == '(':
            self.match(TokenType.DELIMITER)
            self.ExprList()
            self.match(TokenType.DELIMITER)
        elif self.current_token.type == TokenType.DELIMITER and self.current_token.value == '[':
            self.List()
        else:
            pass  # ε production

    def Literal(self):
        self.match(TokenType.LITERAL)

    def List(self):
        self.match(TokenType.DELIMITER)
        self.ExprList()
        self.match(TokenType.DELIMITER)

    def ExprList(self):
        if self.current_token.type == TokenType.DELIMITER and self.current_token.value == ']':
            pass  # ε production
        else:
            self.Expr()
            self.ExprListTail()

    def ExprListTail(self):
        if self.current_token.type == TokenType.DELIMITER and self.current_token.value == ',':
            self.match(TokenType.DELIMITER)
            self.Expr()
            self.ExprListTail()
        else:
            pass  # ε production

    def CompOp(self):
        if self.current_token.type == TokenType.OPERATOR and self.current_token.value in ['==', '!=', '<', '>', '<=', '>=', 'is']:
            self.match(TokenType.OPERATOR)
        else:
            self.error("CompOp")


    def ReturnExpr(self):
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'return':
            self.match(TokenType.KEYWORD)
            self.Expr()
        else:
            pass  # ε production
    
    def Literal(self):
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value in ['None', 'True', 'False']:
            self.match(TokenType.KEYWORD)
        elif self.current_token.type == TokenType.INTEGER:
            self.match(TokenType.INTEGER)
        elif self.current_token.type == TokenType.STRING:
            self.match(TokenType.STRING)
        else:
            self.error("Literal")
    

def main():
    filename = "input.txt"
    tokens = tokenize(filename)

    for token in tokens:
        token_type_name = token.type.name
        print(f"DEBUG SCAN - {token_type_name}\t\t[ {token.value} ]\t found at ({token.line}:{token.column})")

if __name__ == "__main__":
    main()
