from .text import XFileLoader
from .models import XFile, ParseError, parse_header


def parse_x_file(contents: bytes) -> XFile:
    if len(contents) < 16:
        raise ParseError("not a .X file")

    header = parse_header(contents[:16].decode("ascii"))

    if header["encoding"] == "txt ":
        loader = XFileLoader()
        return loader.load(contents.decode("utf-8"), header)
    else:
        raise ValueError("binary mode is unsupported currently")
