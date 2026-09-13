from dataclasses import dataclass
from enum import Enum, auto

from ..models import ParseError


class XTokenType(Enum):
    EOL = auto()
    EOF = auto()
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
    PERIOD = auto()


@dataclass
class XToken:
    type: XTokenType
    val: str
    idx: int


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

        while char := self.peek_char():
            if char == "\n":
                self.tokens.append(XToken(XTokenType.EOL, "\n", self.index))
            elif char == ";":
                self.tokens.append(XToken(XTokenType.SEMI, ";", self.index))
            elif char == "{":
                self.tokens.append(XToken(XTokenType.L_BRACKET, "{", self.index))
            elif char == "}":
                self.tokens.append(XToken(XTokenType.R_BRACKET, "}", self.index))
            elif char == "[":
                self.tokens.append(XToken(XTokenType.L_SQ_BRACKET, "[", self.index))
            elif char == "]":
                self.tokens.append(XToken(XTokenType.R_SQ_BRACKET, "]", self.index))
            elif char == ",":
                self.tokens.append(XToken(XTokenType.COMMA, ",", self.index))
            elif char == ".":
                if self.peek_char(1) == "." and self.peek_char(2) == ".":
                    self.consume_char()
                    self.consume_char()
                    self.consume_char()
                    self.tokens.append(XToken(XTokenType.ELLIPSIS, "...", self.index))
                elif self.peek_char(1).isdigit():
                    # This case is handled below
                    pass
                else:
                    self.tokens.append(XToken(XTokenType.PERIOD, ".", self.index))
            elif char == '"':
                start_index = self.index
                string = self.consume_char()
                while (string_char := self.peek_char()) and not string_char in '\n"':
                    string = string + self.consume_char()

                if not string_char or string_char == "\n":
                    raise ParseError(
                        f"unterminated string literal at index {start_index}"
                    )

                self.consume_char()
                self.tokens.append(XToken(XTokenType.STRING, string, self.index))
            elif char == "<":
                # TODO: check if UUID is valid (ie the four parts have the right lengths or whatever)
                self.consume_char()
                uuid = ""
                while (uuid_char := self.peek_char()).isalnum() or uuid_char == "-":
                    uuid = uuid + uuid_char
                    self.consume_char()

                if not self.peek_char() == ">":
                    raise ParseError(
                        f"unexpected char '{char}' during UUID at index {self.index}"
                    )

                self.consume_char()
                self.tokens.append(XToken(XTokenType.UUID, uuid, self.index))
            elif char.isalpha():
                ident = self.consume_char()
                while (ident_char := self.peek_char()).isalnum() or ident_char in "_-":
                    ident = ident + self.consume_char()

                self.tokens.append(XToken(XTokenType.IDENT, ident, self.index))
            elif char.isdigit() or (char in "-." and self.peek_char(1).isdigit()):
                num = self.consume_char()
                has_dot = False
                while (num_char := self.peek_char()).isdigit() or (
                    num_char == "." and not has_dot
                ):
                    if num_char == ".":
                        has_dot = True

                    num = num + self.consume_char()

                self.tokens.append(XToken(XTokenType.NUMBER, num, self.index))
            elif char.isspace():
                pass
            elif char == "#" or (char == "/" and self.peek_char(1) == "/"):
                self.consume_char()
                while (comment_char := self.peek_char()) and not comment_char == "\n":
                    self.consume_char()

                if self.peek_char() == "\n":
                    self.consume_char()
            else:
                raise ParseError(f"unknown char '{char}' at index {self.index}")
            self.consume_char()

        return self.tokens
