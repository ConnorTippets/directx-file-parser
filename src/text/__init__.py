from ..models import XHeader, XFile, ParseError
from .tokenizer import XTextTokenizer
from .parser import XTextParser


class XFileLoader:
    def __init__(self):
        self.header: XHeader | None = None

    def load(self, contents: str, header: XHeader) -> XFile:
        self.header = header
        contents = "\n".join(contents.splitlines()[1:])

        tokenizer = XTextTokenizer()
        try:
            tokens = tokenizer.tokenize(contents)
        except ParseError:
            print(tokenizer.tokens)
            raise

        parser = XTextParser()
        try:
            file = parser.parse(tokens)
        except ParseError:
            print(parser.file)
            raise

        print(file)

        return file
