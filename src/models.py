from dataclasses import dataclass
from typing import TypedDict


class ParseError(Exception): ...


class XHeader(TypedDict):
    version: str
    encoding: str
    float_size: str


@dataclass
class XFile: ...


def parse_header(header: str) -> XHeader:
    if not header[0:4] == "xof ":
        raise ParseError("expected 'xof ' at position 0")

    version = header[4:8]
    encoding = header[8:12]
    float_size = header[8:16]

    return {"version": version, "encoding": encoding, "float_size": float_size}
