# Compiladores

## Description
 
The program is an implementation of a lexical analyzer in Python, also known as a lexer or scanner. Its purpose is to analyze a string of text and generate a sequence of tokens, which are units of syntax in the text. This program includes a Hash Table, a data structure used to store and retrieve key-value pairs, which is used to identify keywords in the text.

## How it works
The program reads a string of text and performs a lexical analysis by identifying each token in the text. It begins by defining several constants, including the set of digits and letters that are allowed in the text. It then defines a dictionary of delimiter characters, such as parentheses and commas, along with their corresponding token names. The program also defines a Hash Table to store the keywords that are found in the text.

The program creates an instance of the AnalizadorLexico class, which initializes several attributes, including the text to be analyzed and the position of the lexer in the text. The class includes several methods that are used to perform the lexical analysis. The getChar method returns the next character in the text, and the peekChar method returns the following character without advancing the lexer's position.

The crearNumero method is called when the lexer encounters a sequence of digits in the text. It reads the digits and creates a Token object to represent the integer value.

The crearTokens method is used to generate all the tokens in the text. It iterates through each character in the text, identifying the appropriate token for each character. If a keyword is identified, the method uses the Hash Table to retrieve its token name. If a digit is identified, the method calls the crearNumero method to create a token for the integer value. If a delimiter is identified, the method retrieves its token name from the dictionary of delimiter characters.

## Usage
To use the program, simply create an instance of the AnalizadorLexico class and pass in a string of text to be analyzed. The program will generate a sequence of Token objects, which can be printed using the getTokens method.

## Limitations
This program is designed to analyze a single line of text and may not work as expected for multi-line text or complex syntax. Additionally, the program is designed to identify integers and keywords in the text but does not handle other data types or complex expressions. Finally, the program is limited by the maximum size of the Hash Table, which may affect its ability to identify keywords in very large texts.
## Participants
Carlos Gabriel Morales Umasi
Joey Patrick Flores Davila
