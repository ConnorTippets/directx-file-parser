from dataclasses import dataclass
from typing import overload, Literal
from enum import Enum


class XFileMode(Enum):
    BINARY_MODE = 0
    TEXT_MODE = 1


@dataclass
class XFile: ...


class XTextParser:
    def __init__(self):
        self.line_no = 0
        self.col_no = 0
        self.lines: list[str] = []

    def peek(self) -> str:
        try:
            return self.lines[self.line_no][self.col_no]
        except IndexError:
            return ""

    def consume(self) -> str:
        char = self.peek()

        if self.line_no >= len(self.lines):
            return char

        self.col_no += 1
        if self.col_no >= len(self.lines[self.line_no]):
            self.line_no += 1
            self.col_no = 0

        return char

    def consume_many(self, amount: int = 1) -> str:
        if self.line_no >= len(self.lines):
            return ""

        this_line = self.lines[self.line_no]
        output = this_line[self.col_no : self.col_no + amount]
        self.col_no += amount

        while len(output) < amount:
            self.line_no += 1
            self.col_no = 0
            if self.line_no >= len(self.lines):
                return output
            output = output + "\n"

            amount_left = amount - len(output)

            next_line = self.lines[self.line_no]
            output = output + next_line[self.col_no : self.col_no + amount_left]
            self.col_no += amount_left

        if self.col_no == len(this_line):
            self.line_no += 1
            self.col_no = 0

        return output

    def parse(self, contents: str) -> XFile:
        self.line_no = 0
        self.col_no = 0
        self.lines = contents.splitlines()

        print(self.consume_many(45))


@overload
def parse_x_file(contents: str, mode: Literal[XFileMode.TEXT_MODE]) -> XFile: ...


@overload
def parse_x_file(contents: bytes, mode: Literal[XFileMode.BINARY_MODE]) -> XFile: ...


@overload
def parse_x_file(contents: str | bytes, mode: XFileMode) -> XFile: ...


def parse_x_file(contents: str | bytes, mode: XFileMode) -> XFile:
    if not (isinstance(contents, str) or isinstance(contents, bytes)):
        raise ValueError("incorrect content type")
    if not mode in (XFileMode.BINARY_MODE, XFileMode.TEXT_MODE, 0, 1):
        raise ValueError("incorrect mode type")

    if isinstance(contents, str) and mode is XFileMode.BINARY_MODE:
        raise ValueError("mode was set to BINARY_MODE, but a string was provided")
    if isinstance(contents, bytes) and mode is XFileMode.TEXT_MODE:
        contents = contents.decode("utf-8")

    if isinstance(contents, str):
        return XTextParser().parse(contents)
    else:
        raise ValueError("binary mode is unsupported currently")
