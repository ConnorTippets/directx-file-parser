from dataclasses import dataclass
from typing import overload, Literal
from enum import Enum


class XFileMode(Enum):
    BINARY_MODE = 0
    TEXT_MODE = 1


@dataclass
class XFile: ...


class XParser:
    def __init__(self):
        self.line_no = 0
        self.col_no = 0

    @overload
    def parse(self, contents: str, mode: Literal[XFileMode.TEXT_MODE]) -> XFile: ...

    @overload
    def parse(self, contents: bytes, mode: Literal[XFileMode.BINARY_MODE]) -> XFile: ...

    @overload
    def parse(self, contents: str | bytes, mode: XFileMode) -> XFile: ...

    def parse(self, contents: str | bytes, mode: XFileMode) -> XFile:
        if not (isinstance(contents, str) or isinstance(contents, bytes)):
            raise ValueError("incorrect content type")
        if not mode in (XFileMode.BINARY_MODE, XFileMode.TEXT_MODE, 0, 1):
            raise ValueError("incorrect mode type")

        if isinstance(contents, str) and mode is XFileMode.BINARY_MODE:
            raise ValueError("mode was set to BINARY_MODE, but a string was provided")
        if isinstance(contents, bytes) and mode is XFileMode.TEXT_MODE:
            contents = contents.decode("utf-8")


@overload
def parse_x_file(contents: str, mode: Literal[XFileMode.TEXT_MODE]) -> XFile: ...


@overload
def parse_x_file(contents: bytes, mode: Literal[XFileMode.BINARY_MODE]) -> XFile: ...


@overload
def parse_x_file(contents: str | bytes, mode: XFileMode) -> XFile: ...


def parse_x_file(contents: str | bytes, mode: XFileMode) -> XFile:
    return XParser().parse(contents, mode)
