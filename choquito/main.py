#librerias
import re
import sys
import pyfiglet
from colorama import Fore, Style
from enum import Enum
from collections import namedtuple


# Definir los TokenType como un Enum
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



from anytree import Node, RenderTree
from anytree.exporter import DotExporter
from graphviz import Digraph

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.curr_token = None
        self.errors = []
        self.ast_root = None
        self.error_found = False  # Agregar esta línea
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
            if not self.has_error_in_line(self.curr_token.line):
                self.errors.append(Fore.RED + '[-]' + Style.RESET_ALL + f" Error de sintaxis en línea {self.curr_token.line}: {message}")
        self.next()

    def has_error_in_line(self, line):
        for error in self.errors:
            if f"línea {line}" in error:
                return True
        return False

    def match(self, token_type, token_value=None):
        if self.curr_token is None:
            self.error("Se esperaba más entrada pero se encontró el final del archivo")
            return

        if self.curr_token.type != token_type or (token_value is not None and self.curr_token.value != token_value):
            self.error(f"Se esperaba '{token_type} {token_value}' pero se obtuvo '{self.curr_token.type} {self.curr_token.value}'")
            self.next()
        else:
            self.next()

    def Program(self):
        self.ast_root = Node("Program")
        self.DefList(self.ast_root)
        self.StatementList(self.ast_root)

    def DefList(self, parent):
        if self.curr_token is None:  # Asegúrese de que no hemos alcanzado el final del texto de entrada
            return
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "def":
            def_node = Node("Def", parent=parent)
            self.match(TokenType.KEYWORD, "def")
            func_name = self.curr_token.value  # Obtener el nombre de la función
            self.match(TokenType.IDENTIFIER)
            self.match(TokenType.DELIMITER, "(")
            self.TypedVarList(def_node)
            self.match(TokenType.DELIMITER, ")")
            self.Return(def_node)
            self.match(TokenType.DELIMITER, ":")
            self.Block(def_node)
            def_node.name = func_name  # Asignar el nombre de la función al nodo
            self.DefList(parent)

    def TypedVar(self, parent):
        self.match(TokenType.IDENTIFIER)
        self.match(TokenType.DELIMITER, ":")
        self.Type(parent)

    def Type(self, parent):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value in {"int", "str"}:
            Node(self.curr_token.value, parent=parent)
            self.match(TokenType.KEYWORD, "int")
        elif self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "[":
            node = Node("List", parent=parent)
            self.match(TokenType.DELIMITER, "[")
            self.Type(node)
            self.match(TokenType.DELIMITER, "]")
        else:
            self.error("Se esperaba 'int', 'str' o '['")

    def TypedVarList(self, parent):
        if self.curr_token.type == TokenType.IDENTIFIER:
            self.TypedVar(parent)
            self.TypedVarListTail(parent)

    def TypedVarListTail(self, parent):
        if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == ",":
            self.match(TokenType.DELIMITER, ",")
            self.TypedVar(parent)
            self.TypedVarListTail(parent)

    def Return(self, parent):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value == "->":
            node = Node("Return", parent=parent)
            self.match(TokenType.OPERATOR, "->")
            self.Type(node)

    def Block(self, parent):
        self.match(TokenType.NEWLINE)
        self.match(TokenType.INDENT)
        self.Statement(parent)
        self.StatementList(parent)
        self.match(TokenType.DEDENT)

    def StatementList(self, parent):
        if self.curr_token is not None and self.curr_token.type != TokenType.DEDENT:
            self.Statement(parent)
            self.StatementList(parent)

    def Statement(self, parent):
        if self.curr_token.type == TokenType.KEYWORD:
            if self.curr_token.value == "if":
                node = Node("If", parent=parent)
                self.match(TokenType.KEYWORD, "if")
                self.Expr(node)
                self.match(TokenType.DELIMITER, ":")
                self.Block(node)
                self.ElifList(node)
                self.Else(node)
            elif self.curr_token.value == "while":
                node = Node("While", parent=parent)
                self.match(TokenType.KEYWORD, "while")
                self.Expr(node)
                self.match(TokenType.DELIMITER, ":")
                self.Block(node)
            elif self.curr_token.value == "for":
                node = Node("For", parent=parent)
                self.match(TokenType.KEYWORD, "for")
                self.match(TokenType.IDENTIFIER)
                self.match(TokenType.KEYWORD, "in")
                self.Expr(node)
                self.match(TokenType.DELIMITER, ":")
                self.Block(node)
            elif self.curr_token.value == "return":
                node = Node("Return", parent=parent)
                self.match(TokenType.KEYWORD, "return")
                self.ReturnExpr(node)
                self.match(TokenType.NEWLINE)
            elif self.curr_token.value == "pass":
                self.match(TokenType.KEYWORD, "pass")
        else:
            self.SimpleStatement(parent)
            self.match(TokenType.NEWLINE)

    def SimpleStatement(self, parent):
        if self.curr_token.type == TokenType.IDENTIFIER:
            self.Expr(parent)
            self.SSTail(parent)
        else:
            self.error("Se esperaba una declaración simple")

    def SSTail(self, parent):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value == "=":
            node = Node("Assignment", parent=parent)
            assign_op = self.curr_token.value  # Obtener el operador de asignación
            self.match(TokenType.OPERATOR, assign_op)
            self.Expr(node)
            node.name = assign_op  # Asignar el operador de asignación al nodo


    def ReturnExpr(self, parent):
        if self.curr_token.type != TokenType.NEWLINE:
            self.Expr(parent)
        elif self.curr_token.type == TokenType.IDENTIFIER:
            self.Name(parent)

    def Expr(self, parent):
        self.orExpr(parent)
        self.ExprPrime(parent)

    def ExprPrime(self, parent):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "if":
            # Eliminado el nodo "TernaryExpr" y ahora el parent adoptará a los hijos directamente
            if_node = Node("If", parent=parent)
            self.match(TokenType.KEYWORD, "if")
            self.andExpr(if_node)
            self.match(TokenType.KEYWORD, "else")
            else_node = Node("Else", parent=parent)
            self.andExpr(else_node)
            self.ExprPrime(parent)


    def ElifList(self, parent):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "elif":
            self.Elif(parent)
            self.ElifList(parent)

    def Elif(self, parent):
        node = Node("Elif", parent=parent)
        self.match(TokenType.KEYWORD, "elif")
        self.Expr(node)
        self.match(TokenType.DELIMITER, ":")
        self.Block(node)

    def Else(self, parent):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "else":
            node = Node("Else", parent=parent)
            self.match(TokenType.KEYWORD, "else")
            self.match(TokenType.DELIMITER, ":")
            self.Block(node)

    def orExpr(self, parent):
        self.andExpr(parent)
        self.orExprPrime(parent)

    def orExprPrime(self, parent):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "or":
            node = Node("Or", parent=parent)
            self.match(TokenType.KEYWORD, "or")
            self.andExpr(node)
            self.orExprPrime(node)

    def andExpr(self, parent):
        self.notExpr(parent)
        self.andExprPrime(parent)

    def andExprPrime(self, parent):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "and":
            node = Node("And", parent=parent)
            self.match(TokenType.KEYWORD, "and")
            self.notExpr(node)
            self.andExprPrime(node)

    def notExpr(self, parent):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value == "not":
            node = Node("Not", parent=parent)
            self.match(TokenType.KEYWORD, "not")
            self.CompExpr(node)
        else:
            self.CompExpr(parent)

    def CompExpr(self, parent):
        self.IntExpr(parent)
        self.CompExprPrime(parent)

    def CompExprPrime(self, parent):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value in {"==", "!=", "<", ">", "<=", ">="}:
            node = Node(self.curr_token.value, parent=parent)
            self.match(TokenType.OPERATOR, self.curr_token.value)
            self.IntExpr(node)
            self.CompExprPrime(node)

    def IntExpr(self, parent):
        self.Term(parent)
        self.IntExprPrime(parent)

    def IntExprPrime(self, parent):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value in {"+", "-"}:
            node = Node(self.curr_token.value, parent=parent)
            self.match(TokenType.OPERATOR, self.curr_token.value)
            self.Term(node)
            self.IntExprPrime(node)

    def Term(self, parent):
        self.Factor(parent)
        self.TermPrime(parent)

    def TermPrime(self, parent):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value in {"*", "/", "%"}:
            node = Node(self.curr_token.value, parent=parent)
            self.match(TokenType.OPERATOR, self.curr_token.value)
            self.Factor(node)
            self.TermPrime(node)

    def Factor(self, parent):
        if self.curr_token.type == TokenType.OPERATOR and self.curr_token.value == "-":
            node = Node("Negation", parent=parent)
            self.match(TokenType.OPERATOR, self.curr_token.value)
            self.Factor(node)
        elif self.curr_token.type == TokenType.IDENTIFIER:
            self.Name(parent)
        elif self.curr_token.type in {TokenType.LITERAL, TokenType.KEYWORD}:
            self.Literal(parent)
        elif self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "[":
            self.List(parent)
        elif self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "(":
            self.match(TokenType.DELIMITER, self.curr_token.value)
            self.Expr(parent)
            if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == ")":
                self.match(TokenType.DELIMITER, self.curr_token.value)
            else:
                self.error("Se esperaba ')'")

    def Name(self, parent):
        if self.curr_token.type == TokenType.IDENTIFIER:
            node = Node(self.curr_token.value, parent=parent)
            self.match(TokenType.IDENTIFIER, self.curr_token.value)
            self.NameTail(node)

    def NameTail(self, parent):
        if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "(":
            # Eliminado el nodo "FunctionCall" y ahora el parent adoptará a los hijos directamente
            self.match(TokenType.DELIMITER, self.curr_token.value)
            self.ExprList(parent)
            if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == ")":
                self.match(TokenType.DELIMITER, self.curr_token.value)
            else:
                self.error("Se esperaba ')'")
        elif self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "[":
            self.List(parent)

    def Literal(self, parent):
        if self.curr_token.type == TokenType.KEYWORD and self.curr_token.value in {"None", "True", "False"}:
            node = Node(self.curr_token.value, parent=parent)
            self.match(TokenType.KEYWORD, self.curr_token.value)
        elif self.curr_token.type == TokenType.LITERAL:
            node = Node(str(self.curr_token.value), parent=parent)  # Convertir el valor a una cadena
            self.match(TokenType.LITERAL, self.curr_token.value)
        else:
            self.error("Se esperaba un literal")

    def List(self, parent):
        if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "[":
            node = Node("List", parent=parent)
            self.match(TokenType.DELIMITER, self.curr_token.value)
            self.ExprList(node)
            if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == "]":
                self.match(TokenType.DELIMITER, self.curr_token.value)
            else:
                self.error("Se esperaba ']'")

    def ExprList(self, parent):
        if self.curr_token.type not in {TokenType.DELIMITER, TokenType.NEWLINE, TokenType.DEDENT}:
            self.Expr(parent)
            self.ExprListTail(parent)

    def ExprListTail(self, parent):
        if self.curr_token.type == TokenType.DELIMITER and self.curr_token.value == ",":
            self.match(TokenType.DELIMITER, self.curr_token.value)
            self.Expr(parent)
            self.ExprListTail(parent)

    def export_ast(self, filename):
        graph = Digraph(format='png')
        self._add_ast_nodes(graph, self.ast_root)
        graph.render(filename, view=True)

    def _add_ast_nodes(self, graph, node):
        if node.is_leaf:
            graph.node(str(id(node)), label=node.name)
        else:
            graph.node(str(id(node)), label=node.name)
            for child in node.children:
                self._add_ast_nodes(graph, child)
                graph.edge(str(id(node)), str(id(child)))

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
        print(Fore.GREEN + '[+]' + Style.RESET_ALL + f" DEBUG SCAN - {token_type_name}\t\t[ {token.value} ]\t found at ({token.line}:{token.column})")

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
            print("No se encontraron errores.")
            print()

            # Exportar el AST a un archivo
            parser.export_ast("ast")

            # Mostrar el AST
            print("AST:")
            print_tree(parser.ast_root)
        else:
            print()
            print("El código de entrada NO pertenece al lenguaje. Los errores son:")
            for error in parser.errors:
                print(f"\t {error}")
            print(Fore.BLUE + '[!]' + Style.RESET_ALL + f' Se encontraron {len(parser.errors)} errores.')
    except Exception as e:
        print(f"Hubo un error durante el análisis: {e}")


def print_tree(node, prefix=''):
    print(f"{prefix}{node.name}")
    for child in node.children:
        print_tree(child, prefix + '  ')


if __name__ == "__main__":
    main()
