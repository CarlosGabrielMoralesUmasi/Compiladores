# COMPILERZZZ

# CHOCOPY Scanner and Parser

This project implements a scanner and parser for the "CHOCOPY" programming language. The scanner is responsible for tokenizing the source code into CHOCOPY files, while the parser is responsible for checking the structure and grammar of the code.

## Requirements

-Python 3.x
- `re` library
- `sys` library
- `pyfiglet` library
- `colorama` library

## Facility

1. Clone this repository:

    ```bash
    git clone
2. Access the project directory:
-cd chocopy-scanner-parser
3. Optionally, it is recommended to create and activate a virtual environment for the project.
## Use
The project consists of two main files: scanner.py and parser.py. Here's how to use each of them:

### Scanner (scanner.py)
The scanner takes care of tokenizing the source code into CHOCOPY files. To run the scanner, use the following command:
- python scanner.py file.chocopy
Replace file.chocopy with the path to the file you want to scan. The scanner will display the list of generated tokens and any lexical errors found.
#### Usage
To use the scanner, follow these steps:

1. Import the necessary modules:

- import re
- from enum import Enum
- from collections import namedtuple
2. Define the TokenType enumeration class, which represents the different types of tokens:
 ```class TokenType(Enum):
    NEWLINE = 1
    INDENT = 2
    DEDENT = 3
    IDENTIFIER = 4
    KEYWORD = 5
    LITERAL = 6
    OPERATOR = 7
    DELIMITER = 8
    ERROR = 9
```
3. Define the Token named tuple, which represents a single token with its type, value, line number, and column:
```Token = namedtuple('Token', ['type', 'value', 'line', 'column'])```
4. Implement the tokenize function, which takes a filename as input and returns a list of tokens:
```def tokenize(filename):
    tokens = []
    # Read the file and store the lines
    with open(filename) as f:
        lines = f.readlines()

    line_number = 0
    indent_stack = [0]

    # Process each line
    for line in lines:
        line_number += 1
        indentation = len(line) - len(line.lstrip())

        # Ignore blank lines
        if indentation == len(line):
            continue

        line = line[indentation:]

        # Handle indentation
        if indentation > indent_stack[-1]:
            indent_stack.append(indentation)
            tokens.append(Token(TokenType.INDENT, " ", line_number, indentation))
        else:
            while indentation < indent_stack[-1]:
                indent_stack.pop()
                tokens.append(Token(TokenType.DEDENT, " ", line_number, indentation))

        # Tokenize the line
        token_pattern = re.compile(r"(\b(False|None|True|and|as|assert|async|await|break|class|continue|def|int|str|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b)|([a-zA-Z][a-zA-Z0-9_]*)|([{}()[\]:,.])|(\b0\b|([1-9][0-9]*))|->|([=!<>%/*+\-]=?)|(\b0[0-9]+)|(\"(?:[^\"\\]|\\.)*\")")
        matches = token_pattern.findall(line)

        for match in matches:
            token_value = next(value for value in match if value)
            token_type = TokenType.KEYWORD if match[0] else TokenType.IDENTIFIER if match[2] else TokenType.DELIMITER if match[3] else TokenType.LITERAL

            tokens.append(Token(token_type, token_value, line_number, line.index(token_value) + 1))

    return tokens
```


### Parser (parser.py)
The parser is responsible for checking the structure and grammar of the source code in CHOCOPY files. To run the parser, use the following command:
- python parser.py file.chocopy
Replace file.chocopy with the path to the file you want to scan. The parser will display the tokens consumed and any syntax errors found.

## License

This project is licensed under the MIT License. For details, see the [LICENSE](LICENSE) file.


## Participants
-Carlos Gabriel Morales Umasi

-Joey Patrick Flores Davila
