from dataclasses import dataclass
from enum import Enum, auto

from ..models import XFile, ParseError


class XTokenType(Enum):
    EOL = auto()
    IDENT = auto()
    L_BRACKET = auto()
    R_BRACKET = auto()
    L_SQ_BRACKET = auto()
    R_SQ_BRACKET = auto()
    COMMA = auto()
    UUID = auto()
    SEMI = auto()
    ELLIPSIS = auto()
    NUMBER = auto()
    STRING = auto()


@dataclass
class XToken:
    typ: XTokenType
    val: str


class XTextTokenizer:
    def __init__(self):
        self.index = 0
        self.contents: str = ""
        self.tokens: list[XToken] = []

    def peek_char(self, ahead: int = 0) -> str:
        try:
            return self.contents[self.index + ahead]
        except IndexError:
            return ""

    def consume_char(self) -> str:
        try:
            char = self.contents[self.index]
            self.index += 1
            return char
        except IndexError:
            return ""

    def tokenize(self, contents: str) -> list[XToken]:
        self.line_no = 0
        self.col_no = 0
        self.contents = contents
        self.tokens = []

        while self.peek_char():
            char = self.consume_char()
            if char == "\n":
                self.tokens.append(XToken(XTokenType.EOL, "\n"))
            elif char == ";":
                self.tokens.append(XToken(XTokenType.SEMI, ";"))
            elif char == "{":
                self.tokens.append(XToken(XTokenType.L_BRACKET, "{"))
            elif char == "}":
                self.tokens.append(XToken(XTokenType.R_BRACKET, "}"))
            elif char == "[":
                self.tokens.append(XToken(XTokenType.L_SQ_BRACKET, "["))
            elif char == "]":
                self.tokens.append(XToken(XTokenType.R_SQ_BRACKET, "]"))
            elif char == ",":
                self.tokens.append(XToken(XTokenType.COMMA, ","))
            elif char == ".":
                if self.peek_char() == "." and self.peek_char(1) == ".":
                    self.consume_char()
                    self.consume_char()
                    self.tokens.append(XToken(XTokenType.ELLIPSIS, "..."))
                else:
                    raise ParseError(
                        "TODO: float values 0-1 with leading zero removed (.5)"
                    )
            elif char == '"':
                start_index = self.index - 1
                string = ""
                while (string_char := self.peek_char()) and not string_char in '\n"':
                    string = string + self.consume_char()

                if not string_char or string_char == "\n":
                    raise ParseError(
                        f"unterminated string literal at index {start_index}"
                    )

                self.consume_char()
                self.tokens.append(XToken(XTokenType.STRING, string))
            elif char == "<":
                # TODO: check if UUID is valid (ie the four parts have the right lengths or whatever)
                uuid = ""
                while (uuid_char := self.peek_char()).isalnum() or uuid_char == "-":
                    uuid = uuid + uuid_char
                    self.consume_char()

                if not self.peek_char() == ">":
                    raise ParseError(
                        f"unexpected char '{char}' during UUID at index {self.index}"
                    )

                self.consume_char()
                self.tokens.append(XToken(XTokenType.UUID, uuid))
            elif char.isalpha():
                ident = char
                while (ident_char := self.peek_char()).isalnum() or ident_char in "_-":
                    ident = ident + self.consume_char()

                self.tokens.append(XToken(XTokenType.IDENT, ident))
            elif char.isdigit() or (char == "-" and self.peek_char().isdigit()):
                num = char
                has_dot = False
                while (num_char := self.peek_char()).isdigit() or (
                    num_char == "." and not has_dot
                ):
                    if num_char == ".":
                        has_dot = True

                    num = num + self.consume_char()

                self.tokens.append(XToken(XTokenType.NUMBER, num))
            elif char.isspace():
                continue
            elif char == "#" or (char == "/" and self.peek_char() == "/"):
                while (comment_char := self.peek_char()) and not comment_char == "\n":
                    self.consume_char()

                if self.peek_char() == "\n":
                    self.consume_char()
            else:
                raise ParseError(f"unknown char '{char}' at index {self.index-1}")

        return self.tokens
