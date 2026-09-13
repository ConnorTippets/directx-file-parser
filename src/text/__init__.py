from ..models import XHeader, XFile, ParseError
from ..text.tokenizer import XTextTokenizer


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

        print(tokens)
