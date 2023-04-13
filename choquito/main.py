import os
import string
from typing import Text

digitos="9876543210"
letras=string.ascii_letters
letrasDigitos=letras+digitos
"Analizador Lexico"
dictDelim = {'+': 'SUMA', '-': 'RESTA', '*': 'MULTIPLICACION', '/': 'DIVISION', '%': 'MODULO', '<': 'MENOR_QUE', '>': 'MAYOR_QUE', '<=': 'MENOR_IGUAL_QUE', '>=': 'MAYOR_IGUAL_QUE', '==': 'IGUAL_QUE', '!=': 'DISTINTO_QUE', '=': 'ASIGNACION', '(': 'OPEN_PAR', ')': 'CLO_PAR', '[': 'CORCHETE_INICIA', ']': 'CORCHETE_FIN', ',': 'COMA', ':': 'DOS_PUNTOS', '.': 'PUNTO', '->': 'FLECHA'}

class HashTable:
    def __init__(self):
        self.size = 100
        self.table = [None] * self.size
        
    def hash(self, key):
        return sum((ord(key[i]) * (i + 1)) for i in range(len(key))) % self.size
      
    def put(self, key, value):
        index = self.hash(key)
        while self.table[index] is not None and self.table[index][0] != key:
            index = (index + 1) % self.size
        self.table[index] = (key, value)
      
    def get(self, key):
        index = self.hash(key)
        while self.table[index] is not None and self.table[index][0] != key:
            index = (index + 1) % self.size
        if self.table[index] is None:
            return None
        else:
            return self.table[index][1]

key_table = HashTable()
for k, v in {"False": "FALSE", "None": "NONE", "True": "TRUE", "and": "AND", "as": "AS", "assert": "ASSERT", "async": "ASYNC", "await": "AWAIT", "break": "BREAK", "class": "CLASS", "continue": "CONTINUE", "def": "DEF", "del": "DEL", "elif": "ELIF", "else": "ELSE", "except": "EXCEPT", "finally": "FINALLY", "for": "FOR", "from": "FROM", "global": "GLOBAL", "if": "IF", "import": "IMPORT", "in": "IN", "is": "IS", "lambda": "LAMBDA", "nonlocal": "NONLOCAL", "not": "NOT", "or": "OR", "pass": "PASS", "raise": "RAISE", "return": "RETURN", "try": "TRY", "while": "WHILE", "with": "WITH", "yield": "YIELD"}.items():
    key_table.put(k, v)

charEvitar = ['\t', ' ', '\n']
#numero_grande = int("2147483648")
class Token:
    def __init__(self, nombre, valor, col, fil):
        self.fil = fil
        self.col = col
        self.nombre = nombre
        self.valor = valor
    # Método que devuelve una cadena representando al token
    def __repr__(self):
        return f"DEBUG SCAN - {self.nombre} [ {self.valor} ] found at ({self.fil} : {self.col})"

class AnalizadorLexico:
    def __init__(self, text):
        self.fil = 0
        self.col = 0
        self.text = text
        self.puntero = -1
        self.contador = 0
        self.tokens = []
        self.crearTokens()
        self.getTokens()

    # Método que devuelve el siguiente carácter del texto a analizar
    def getChar(self):
        self.puntero += 1
        if self.puntero < len(self.text):
            self.fil += 1
            return self.text[self.puntero]
        return None

    # Método que devuelve el siguiente carácter del texto a analizar sin avanzar el puntero
    def peekChar(self):
        if self.puntero < (len(self.text) - 1):
            return self.text[self.puntero + 1]
        return None

    # Método que imprime los tokens encontrados durante el análisis léxico
    def getTokens(self):
        for token in self.tokens:
            print(repr(token))

    # Método que crea un token para representar un número entero encontrado en el texto

    # Método que crea un token para representar un número entero encontrado en el texto
    def crearNumero(self):
        numeroString = ""
        charActual = self.getChar()
        if charActual == "0":
            siguiente_char = self.peekChar()
            if siguiente_char is None or not siguiente_char.isdigit():
                print("Error léxico: número con ceros a la izquierda")
                return
        while charActual is not None and charActual.isdigit():
            numeroString += charActual
            if len(numeroString) > 10:
                print("Error léxico: número demasiado grande")
                return
            elif len(numeroString) == 10 and int(numeroString) > 2147483647:
                print("Error léxico: número demasiado grande")
                return
            charActual = self.getChar()
        if numeroString == "":
            print("Error léxico: número vacío")
            return
        self.tokens.append(Token("NUMERO", int(numeroString), self.col, self.fil))
    
    
    def crearIdentificador(self):
        identificadorString=""
        charActual=self.getChar()
        identificadorString+=charActual
        
        # Se recorre el código hasta encontrar algún caracter de letras o dígitos o el símbolo '_'
        while self.peekChar() != None and self.peekChar() in letrasDigitos + '_': 
            charActual=self.getChar()
            identificadorString+=charActual
        
        # Se busca si el identificador es una palabra reservada, si es así, se crea un token con su valor
        valor = key_table.get(identificadorString)
        if valor is not None:
            self.tokens.append(Token("KEY", identificadorString, self.fil, self.col))
            return
        
        # En caso contrario, se crea un token con el valor "ID"
        self.tokens.append(Token("ID",identificadorString,self.fil,self.col))

        

    def crearTokens(self):
        while self.peekChar()!=None:

            if self.peekChar() == "\n":
                self.col += 1
                self.fil = 0
            # Si el siguiente carácter es un salto de línea, se incrementa el contador de columnas y se reinicia el contador de filas.
          
            if self.peekChar() in charEvitar:
                self.puntero+=1
            # Si el siguiente carácter es un carácter a evitar, se aumenta el puntero en uno.


            elif self.peekChar() in digitos:
                self.crearNumero()
            # Si el siguiente carácter es un dígito, se crea un token para un número.


          
            elif self.peekChar() in letras:
                self.crearIdentificador()
            # Si el siguiente carácter es una letra, se crea un token para un identificador.

            elif self.peekChar() in dictDelim:
                charDelim=self.getChar()
                self.tokens.append(Token(dictDelim[charDelim],charDelim,self.fil,self.col))

           # Si el siguiente carácter es un delimitador, se crea un token para ese delimitador.

            elif self.peekChar()=='=':
                Signo=self.getChar()
                if self.peekChar() !=None and self.peekChar()=='>':
                    Signo+=self.getChar()
                    self.tokens.append(Token("PUNTERO",Signo,self.fil,self.col))
                else:
                    self.tokens.append(Token("IGUAL",Signo,self.fil,self.col))

                  # Si el siguiente carácter es un signo igual, se crea un token para igual o para puntero si el siguiente carácter es mayor que.

            #----------------------------------------------------------------------       
            elif self.peekChar()=='=':
                Signo=self.getChar()
                if self.peekChar() !=None and self.peekChar()=='=':
                    Signo+=self.getChar()
                    self.tokens.append(Token("COMPARATIVO_IGUALDAD",Signo,self.fil,self.col))
                else:
                        break

                  # Si el siguiente carácter es un signo igual, se crea un token para comparativo de igualdad si el siguiente carácter también es igual.

            #----------------------------------------------------------------------
            elif self.peekChar()=='!':
                Signo=self.getChar()
                if self.peekChar() !=None and self.peekChar()=='=':
                    Signo+=self.getChar()
                    self.tokens.append(Token("COMPARATIVO_DESIGUALDAD",Signo,self.fil,self.col))
                else:
                    self.tokens.append(Token("NEGACION",Signo,self.fil,self.col))

                  # Si el siguiente carácter es un signo de exclamación, se crea un token para comparativo de desigualdad si el siguiente carácter es igual.

            #----------------------------------------------------------------------
            elif self.peekChar()=='<':
                Signo=self.getChar()
                if self.peekChar() !=None and self.peekChar()=='=':
                    Signo+=self.getChar()
                    self.tokens.append(Token("MENOR_IGUAL_QUE",Signo,self.fil,self.col))
                else:
                    self.tokens.append(Token("MENOR_QUE",Signo,self.fil,self.col))

                  # Si el siguiente carácter es un signo menor que, se crea un token para menor que o para menor o igual que si el siguiente carácter es igual.

            #----------------------------------------------------------------------
            elif self.peekChar()=='>':
                Signo=self.getChar()
                if self.peekChar() !=None and self.peekChar()=='=':
                    Signo+=self.getChar()
                    self.tokens.append(Token("MAYOR_IGUAL_QUE",Signo,self.fil,self.col))
                else:
                    self.tokens.append(Token("MAYOR_QUE",Signo,self.fil,self.col))
            #----------------------------------------------------------------------
            elif self.peekChar()=='#':
                self.puntero+=1
          
                #self.puntero += self.source[self.puntero:].find('\n') + 1
                while self.peekChar() != '\n' and self.peekChar() is not None:
                  self.puntero += 1
                while self.peekChar()!='\n':
                    if self.getChar()!='#' :
                        if self.peekChar()=='\n' or self.peekChar()==None:
                            break
                        continue
                    else:
                        break
          
            #----------------------------------------------------------------------
            elif self.peekChar()=='-':
                Signo=self.getChar()
                if self.peekChar() !=None and self.peekChar()==digitos:
                    Signo+=self.getChar()
                    self.tokens.append(Token("NUM",Signo,self.fil,self.col))
                else:
                    self.tokens.append(Token("RESTA",Signo,self.fil,self.col))
            #----------------------------------------------------------------------
            else:
                print(f"Error: Caracter invalido \'{self.getChar()}\'")
                self.contador += 1
                print("SE ENCONTRARON", self.contador, "ERRORES")

if __name__ == "__main__":
    print("INFO SCAN - Start scanning…")
    with open("test.txt", "r") as archivo:
        contenido = archivo.read()

    analizador = AnalizadorLexico(contenido)
    analizador.getTokens()

    print("INFO SCAN - FINISHHHH scanning…")
