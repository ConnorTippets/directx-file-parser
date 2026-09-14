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

    def peek(self, ahead: int = 0) -> str:
        try:
            return self.contents[self.index + ahead]
        except IndexError:
            return ""

    def consume(self) -> str:
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

        while char := self.peek():
            if char == "\n":
                self.tokens.append(XToken(XTokenType.EOL, "EOL", self.index))
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
                if self.peek(1) == "." and self.peek(2) == ".":
                    self.consume()
                    self.consume()
                    self.consume()
                    self.tokens.append(XToken(XTokenType.ELLIPSIS, "...", self.index))
                elif self.peek(1).isdigit():
                    # This case is handled below
                    pass
                else:
                    self.tokens.append(XToken(XTokenType.PERIOD, ".", self.index))
            elif char == '"':
                start_index = self.index
                string = self.consume()
                while (string_char := self.peek()) and not string_char in '\n"':
                    string = string + self.consume()

                if not string_char or string_char == "\n":
                    raise ParseError(
                        f"unterminated string literal at index {start_index}"
                    )

                self.tokens.append(XToken(XTokenType.STRING, string, self.index))
            elif char == "<":
                # TODO: check if UUID is valid (ie the four parts have the right lengths or whatever)
                self.consume()
                uuid = ""
                while (uuid_char := self.peek()).isalnum() or uuid_char == "-":
                    uuid = uuid + uuid_char
                    self.consume()

                if not self.peek() == ">":
                    raise ParseError(
                        f"unexpected char '{char}' during UUID at index {self.index}"
                    )

                self.tokens.append(XToken(XTokenType.UUID, uuid, self.index))
            elif char.isalpha():
                ident = self.consume()
                while (ident_char := self.peek()).isalnum() or ident_char in "_-":
                    ident = ident + self.consume()

                self.tokens.append(XToken(XTokenType.IDENT, ident, self.index))
                continue
            elif char.isdigit() or (char in "-." and self.peek(1).isdigit()):
                num = self.consume()
                has_dot = False
                while (num_char := self.peek()).isdigit() or (
                    num_char == "." and not has_dot
                ):
                    if num_char == ".":
                        has_dot = True

                    num = num + self.consume()

                self.tokens.append(XToken(XTokenType.NUMBER, num, self.index))
                continue
            elif char.isspace():
                pass
            elif char == "#" or (char == "/" and self.peek(1) == "/"):
                self.consume()
                while (comment_char := self.peek()) and not comment_char == "\n":
                    self.consume()
            else:
                raise ParseError(f"unknown char '{char}' at index {self.index}")
            self.consume()

        return self.tokens
