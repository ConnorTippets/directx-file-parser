from dataclasses import dataclass
from typing import TypedDict
from enum import Enum, auto


class XTokenType(Enum):
    EOL = auto()
    IDENT = auto()
    L_BRACKET = auto()
    R_BRACKET = auto()


@dataclass
class XToken:
    typ: XTokenType
    val: str


class ParseError(Exception): ...


class XHeader(TypedDict):
    version: str
    encoding: str
    float_size: str


@dataclass
class XFile: ...


class XTextParser:
    def __init__(self):
        self.index = 0
        self.contents: str = ""
        self.header: XHeader | None = None
        self.tokens: list[XToken] = []

    def peek_char(self) -> str:
        try:
            return self.contents[self.index]
        except IndexError:
            return ""

    def consume_char(self) -> str:
        try:
            char = self.contents[self.index]
            self.index += 1
            return char
        except IndexError:
            return ""

    def parse(self, contents: str, header: XHeader) -> XFile:
        self.line_no = 0
        self.col_no = 0
        self.contents = "\n".join(contents.splitlines()[1:])
        self.tokens = []
        # skip the header line, already parsed

        self.header = header

        while self.peek_char():
            char = self.consume_char()
            if char == "\n":
                self.tokens.append(XToken(XTokenType.EOL, "\n"))
            elif char == "{":
                self.tokens.append(XToken(XTokenType.L_BRACKET, "{"))
            elif char == "}":
                self.tokens.append(XToken(XTokenType.R_BRACKET, "}"))
            elif char.isalpha():
                ident = char
                while (ident_char := self.peek_char()).isalnum():
                    ident = ident + ident_char
                    self.consume_char()

                self.tokens.append(XToken(XTokenType.IDENT, ident))
            elif char.isspace():
                continue
            else:
                raise ParseError(f"unknown char '{char}' at index {self.index-1}")

        print(self.tokens)


def parse_header(header: str) -> XHeader:
    if not header[0:4] == "xof ":
        raise ParseError("expected 'xof ' at position 0")

    version = header[4:8]
    encoding = header[8:12]
    float_size = header[8:16]

    return {"version": version, "encoding": encoding, "float_size": float_size}


def parse_x_file(contents: bytes) -> XFile:
    if len(contents) < 16:
        raise ParseError("not a .X file")

    header = parse_header(contents[:16].decode("ascii"))

    if header["encoding"] == "txt ":
        return XTextParser().parse(contents.decode("utf-8"), header)
    else:
        raise ValueError("binary mode is unsupported currently")
