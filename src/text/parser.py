from .tokenizer import XToken, XTokenType

from ..models import XFile, ParseError


class XTextParser:
    def __init__(self):
        self.index = 0
        self.tokens: list[XToken] = []
        self.file: XFile = XFile()

    def peek(self) -> XToken:
        try:
            return self.tokens[self.index]
        except IndexError:
            return XToken(XTokenType.EOF, "", self.index)

    def consume(self) -> XToken:
        try:
            token = self.tokens[self.index]
            self.index += 1
            return token
        except IndexError:
            return XToken(XTokenType.EOF, "", self.index)

    def try_parse_template_def(self):
        tok = self.peek()
        if tok.type == XTokenType.IDENT and tok.val == "template":
            print("parsing template")
            self.consume()

            if not (name_tok := self.peek()).type == XTokenType.IDENT:
                raise ParseError(
                    f"`{name_tok.val}` at index {name_tok.idx} is not a valid template name"
                )

            name = self.consume().val
            print(f"template name is {name}")

            if not (l_brack := self.peek()).type == XTokenType.L_BRACKET:
                raise ParseError(
                    f"expected '{{' during template def at {l_brack.idx}, got `{l_brack.val}`"
                )

            self.consume()

            if not (newline := self.peek()).type == XTokenType.EOL:
                raise ParseError(
                    f"expected newline during template def at {newline.idx}, got `{newline.val}`"
                )

            self.consume()

            if not (uuid_tok := self.peek()).type == XTokenType.UUID:
                raise ParseError(
                    f"expected UUID during template def at {uuid_tok.idx}, got `{uuid_tok.val}`"
                )

            uuid = self.consume().val
            print(f"template uuid is {uuid}")
            breakpoint()

        while not self.peek().type in (XTokenType.EOL, XTokenType.EOF):
            self.consume()

        if self.peek().type == XTokenType.EOL:
            self.consume()

    def parse(self, tokens: list[XToken]) -> XFile:
        self.index = 0
        self.tokens = tokens
        self.file = XFile()

        while not self.peek().type == XTokenType.EOF:
            self.try_parse_template_def()
