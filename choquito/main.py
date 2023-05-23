import re
import sys
import pyfiglet
from colorama import Fore, Style
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
            tokens.append(Token(TokenType.INDENT, " ", line_number, indentation))
        else:
            while indentation < indent_stack[-1]:
                indent_stack.pop()
                tokens.append(Token(TokenType.DEDENT, " ", line_number, indentation))

        # Tokeniza la línea
        token_pattern = re.compile(r"(\b(False|None|True|and|as|assert|async|await|break|class|continue|def|int|str|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b)|([a-zA-Z][a-zA-Z0-9_]*)|([{}()[\]:,.])|(\b0\b|([1-9][0-9]*))|->|([=!<>%/*+\-]=?)|(\b0[0-9]+)|(\"(?:[^\"\\]|\\.)*\")")
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
                    print(Fore.RED + '[-]' + Style.RESET_ALL + f" Error lexico en la linea {line_number}: '{matched}' (secuencia de escape no reconocida)")
                    error_count += 1
            else:
                token_type = TokenType.OPERATOR

            column = indentation + 1 + (match.start() - search_start)
            tokens.append(Token(token_type, matched, line_number, column))
            search_start = match.end()

        # Líneas nuevas
        tokens.append(Token(TokenType.NEWLINE, "/n", line_number, len(line) + 1))

        # Manejo de errores léxicos
        if search_start != len(line.rstrip()) and not all(c.isspace() or c == '\t' for c in line[search_start:].rstrip()):
            print(Fore.RED + '[-]' + Style.RESET_ALL +f" Error lexico en la linea {line_number}: '{line[search_start:].rstrip()}'")
            error_count += 1

    # Genera tokens DEDENT al final de la entrada
    while indent_stack[-1] > 0:
        indent_stack.pop()
        tokens.append(Token(TokenType.DEDENT, "", line_number, 0))
    

    print(Fore.BLUE + '[!]' + Style.RESET_ALL +f" INFO SCAN - Completed with {error_count} errors")
    print()
  
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.curr_token = None
        self.errors = []
        self.next()

    def next(self):
        if len(self.tokens) > 0:
            self.curr_token = self.tokens.pop(0)
            print(Fore.GREEN + '[+] ' + Style.RESET_ALL + f'Token consumido:   [ {self.curr_token.value} ]    -    Tipo de token:   {self.curr_token.type}')
        else:
            self.curr_token = None

    def error(self, message):
        if self.curr_token is None:
            self.errors.append(Fore.RED + '[-]' + Style.RESET_ALL + f" Error de sintaxis al final del archivo: {message}")
        else:
            self.errors.append(Fore.RED + '[-]' + Style.RESET_ALL + f" Error de sintaxis en línea {self.curr_token.line}: {message}")
        self.next()

    
    # Reglas de producción

    def Program(self):
        self.DefList()
        self.StatementList()

    def DefList(self):
        if self.curr_token is None:  # Asegúrese de que no hemos alcanzado el final del texto de entrada
            return
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "def":
            self.Def()
            self.DefList()


    def Def(self):
        self.match(TokenType.KEYWORD, "def")
        self.match(TokenType.IDENTIFIER)
        self.match(TokenType.DELIMITER, "(")
        self.TypedVarList()
        self.match(TokenType.DELIMITER, ")")
        self.Return()
        self.match(TokenType.DELIMITER, ":")
        self.Block()

    def TypedVar(self):
        self.match(TokenType.IDENTIFIER)
        self.match(TokenType.DELIMITER, ":")
        self.Type()

    def Type(self):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value in {"int", "str"}:
            self.match(TokenType.KEYWORD, "int")
        elif self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "[":
            self.match(TokenType.DELIMITER, "[")
            self.Type()
            self.match(TokenType.DELIMITER, "]")
        else:
            self.error("Se esperaba 'int', 'str' o '['")

    def TypedVarList(self):
        if self.curr_token.type == TokenType.IDENTIFIER:
            self.TypedVar()
            self.TypedVarListTail()

    def TypedVarListTail(self):
        if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == ",":
            self.match(TokenType.DELIMITER, ",")
            self.TypedVar()
            self.TypedVarListTail()

    def Return(self):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value == "->":
            self.match(TokenType.OPERATOR, "->")
            self.Type()

    def Block(self):
        self.match(TokenType.NEWLINE)
        self.match(TokenType.INDENT)
        self.Statement()
        self.StatementList()
        self.match(TokenType.DEDENT)
    
    def StatementList(self):
        if self.curr_token is not None and self.curr_token.type != TokenType.DEDENT:
            self.Statement()
            self.StatementList()

    def Statement(self):
        if self.curr_token.type == TokenType.KEYWORD:
            if self.curr_token.value == "if":
                self.match(TokenType.KEYWORD, "if")
                self.Expr()
                self.match(TokenType.DELIMITER, ":")
                self.Block()
                self.ElifList()
                self.Else()
            elif self.curr_token.value == "while":
                self.match(TokenType.KEYWORD, "while")
                self.Expr()
                self.match(TokenType.DELIMITER, ":")
                self.Block()
            elif self.curr_token.value == "for":
                self.match(TokenType.KEYWORD, "for")
                self.match(TokenType.IDENTIFIER)
                self.match(TokenType.KEYWORD, "in")
                self.Expr()
                self.match(TokenType.DELIMITER, ":")
                self.Block()
            elif self.curr_token.value == "return":
                self.match(TokenType.KEYWORD, "return")
                self.ReturnExpr()
                self.match(TokenType.NEWLINE)
            elif self.curr_token.value == "pass":
                self.match(TokenType.KEYWORD, "pass")
        else:
            self.SimpleStatement()
            self.match(TokenType.NEWLINE)
    
    def SimpleStatement(self):
        if self.curr_token.type == TokenType.IDENTIFIER:
            self.Expr()
            self.SSTail()
        else:
            self.error("Se esperaba una declaración simple")

    def SSTail(self):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value == "=":
            self.match(TokenType.OPERATOR, "=")
            self.Expr()

    def ReturnExpr(self):
        if self.curr_token.type != TokenType.NEWLINE:
            self.Expr()
        elif self.curr_token.type == TokenType.IDENTIFIER:
            self.Name()

    def Expr(self):
        self.orExpr()
        self.ExprPrime()

    def ExprPrime(self):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "if":
            self.match(TokenType.KEYWORD, "if")
            self.andExpr()
            self.match(TokenType.KEYWORD, "else")
            self.andExpr()
            self.ExprPrime()
    
    def ElifList(self):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "elif":
            self.Elif()
            self.ElifList()

    def Elif(self):
        self.match(TokenType.KEYWORD, "elif")
        self.Expr()
        self.match(TokenType.DELIMITER, ":")
        self.Block()

    def Else(self):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "else":
            self.match(TokenType.KEYWORD, "else")
            self.match(TokenType.DELIMITER, ":")
            self.Block()

    def match(self, token_type, token_value=None):
        if self.curr_token is None:
            self.error("Se esperaba más entrada pero se encontró el final del archivo")
            return
    
        if self.curr_token.type != token_type or (token_value is not None and self.curr_token.value != token_value):
            self.error(f"Se esperaba '{token_type} {token_value}' pero se obtuvo '{self.curr_token.type} {self.curr_token.value}'")
            self.next()
        else:
            self.next()

    def orExpr(self):
        self.andExpr()
        self.orExprPrime()

    def orExprPrime(self):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "or":
            self.match(TokenType.KEYWORD, "or")
            self.andExpr()
            self.orExprPrime()
        
    def andExpr(self):
        self.notExpr()
        self.andExprPrime()

    def andExprPrime(self):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "and":
            self.match(TokenType.KEYWORD, "and")
            self.notExpr()
            self.andExprPrime()

    def notExpr(self):
        self.CompExpr()
        self.notExprPrime()

    def notExprPrime(self):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "not":
            self.match(TokenType.KEYWORD, "not")
            self.CompExpr()
            self.notExprPrime()

    def CompExpr(self):
        self.IntExpr()
        self.CompExprPrime()

    def CompExprPrime(self):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value in {"==", "!=", "<", ">", "<=", ">="}:
            self.match(TokenType.OPERATOR, self.curr_token.value)
            self.IntExpr()
            self.CompExprPrime()

    def IntExpr(self):
        self.Term()
        self.IntExprPrime()

    def IntExprPrime(self):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value in {"+", "-"}:
            self.match(TokenType.OPERATOR, self.curr_token.value)
            self.Term()
            self.IntExprPrime()

    def Term(self):
        self.Factor()
        self.TermPrime()

    def TermPrime(self):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value in {"*", "/", "%"}:
            self.match(TokenType.OPERATOR, self.curr_token.value)
            self.Factor()
            self.TermPrime()


    def Factor(self):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value == "-":
            self.match(TokenType.OPERATOR, self.curr_token.value)
            self.Factor()
        elif self.curr_token.type == TokenType.IDENTIFIER:
            self.Name()
        elif self.curr_token.type in {TokenType.LITERAL, TokenType.KEYWORD}:
            self.Literal()
        elif self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "[":
            self.List()
        elif self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "(":
            self.match(TokenType.DELIMITER, self.curr_token.value)
            self.Expr()
            if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == ")":
                self.match(TokenType.DELIMITER, self.curr_token.value)
            else:
                self.error("Se esperaba ')'")

    def Name(self):
        if self.curr_token.type == TokenType.IDENTIFIER:
            self.match(TokenType.IDENTIFIER, self.curr_token.value)
            self.NameTail()

    def NameTail(self):
        if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "(":
            self.match(TokenType.DELIMITER, self.curr_token.value)
            self.ExprList()
            if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == ")":
                self.match(TokenType.DELIMITER, self.curr_token.value)
            else:
                self.error("Se esperaba ')'")
        elif self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "[":
            self.List()

    def Literal(self):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value in {"None", "True", "False"}:
             self.match(TokenType.KEYWORD, self.curr_token.value)
        elif self.curr_token.type == TokenType.LITERAL:
            self.match(TokenType.LITERAL, self.curr_token.value)
        else:
            self.error("Se esperaba un literal")

    def List(self):
        if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "[":
            self.match(TokenType.DELIMITER, self.curr_token.value)
            self.ExprList()
            if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "]":
                self.match(TokenType.DELIMITER, self.curr_token.value)
            else:
                self.error("Se esperaba ']'")

    def ExprList(self):
        if self.curr_token.type not in {TokenType.DELIMITER, TokenType.NEWLINE, TokenType.DEDENT}:
            self.Expr()
            self.ExprListTail()

    def ExprListTail(self):
        if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == ",":
            self.match(TokenType.DELIMITER, self.curr_token.value)
            self.Expr()
            self.ExprListTail()


    def CompOp(self):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value in {"==", "!=", "<", ">", "<=", ">=", "is"}:
            self.match(TokenType.OPERATOR, self.curr_token.value)
        else:
            self.error("Se esperaba un operador de comparación") 



from colorama import Fore, Style

def print_with_frame(text, frame_color, text_color):
    # Determinar la longitud máxima de una línea en el texto
    max_line_length = max(len(line) for line in text.split("\n"))

    # Crear el marco
    frame = "+" + "-" * (max_line_length + 2) + "+"

    # Imprimir el marco en color blanco
    print(frame_color + frame)

    # Imprimir el texto enmarcado en color personalizado
    for line in text.split("\n"):
        print(frame_color + "|" + text_color, line.center(max_line_length), frame_color + "|")

    # Imprimir el marco en color blanco
    print(frame_color + frame + Style.RESET_ALL)


# Texto a imprimir en un marco
texto = """

░█████╗░██╗░░██╗░█████╗░░█████╗░░█████╗░██████╗░██╗░░░██╗
██╔══██╗██║░░██║██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚██╗░██╔╝
██║░░╚═╝███████║██║░░██║██║░░╚═╝██║░░██║██████╔╝░╚████╔╝░
██║░░██╗██╔══██║██║░░██║██║░░██╗██║░░██║██╔═══╝░░░╚██╔╝░░
╚█████╔╝██║░░██║╚█████╔╝╚█████╔╝╚█████╔╝██║░░░░░░░░██║░░░
░╚════╝░╚═╝░░╚═╝░╚════╝░░╚════╝░░╚════╝░╚═╝░░░░░░░░╚═╝░░░

░█████╗░░█████╗░███╗░░░███╗██████╗░██╗██╗░░░░░███████╗██████╗░
██╔══██╗██╔══██╗████╗░████║██╔══██╗██║██║░░░░░██╔════╝██╔══██╗
██║░░╚═╝██║░░██║██╔████╔██║██████╔╝██║██║░░░░░█████╗░░██████╔╝
██║░░██╗██║░░██║██║╚██╔╝██║██╔═══╝░██║██║░░░░░██╔══╝░░██╔══██╗
╚█████╔╝╚█████╔╝██║░╚═╝░██║██║░░░░░██║███████╗███████╗██║░░██║
░╚════╝░░╚════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝╚══════╝╚══════╝╚═╝░░╚═╝
"""


def main():

    print_with_frame(texto, Fore.WHITE, Fore.WHITE)

    filename = "test.txt"
    print("\033[38;2;255;255;0mStart scanning...\033[0m")
    tokens = tokenize(filename)   
    for token in tokens:
        token_type_name = token.type.name
        print(Fore.GREEN + '[+]' + Style.RESET_ALL +f" DEBUG SCAN - {token_type_name}\t\t[ {token.value} ]\t found at ({token.line}:{token.column})")

    print()
    print("\033[38;2;255;255;0mStart parsing...\033[0m")

    parser = Parser(tokens)

    # Intenta parsear la gramática completa
    try:
        parser.Program()

        # Si no hay errores, entonces el código es válido
        if not parser.errors:
            print()
            print("El código de entrada pertenece al lenguaje.")
            print(Fore.GREEN + '[+]' + Style.RESET_ALL + f' No se encontraron errores.')
        else:
            print()
            print("El código de entrada NO pertenece al lenguaje. Los errores son:")
            for error in parser.errors:
                print(f"\t {error}")
            print(Fore.BLUE + '[!]' + Style.RESET_ALL + f' Se encontraron {len(parser.errors)} errores.')

    except Exception as e:
        print(Fore.RED + f"Hubo un error durante el análisis: {e}" + Style.RESET_ALL)


if __name__ == "__main__":
    main()
