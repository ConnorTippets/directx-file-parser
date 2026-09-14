from dataclasses import dataclass, field
from enum import Enum, auto
from uuid import UUID

from .tokenizer import XToken, XTokenType
from ..models import XFile, ParseError


class XDataType(Enum):
    WORD = auto()
    DWORD = auto()
    FLOAT = auto()
    DOUBLE = auto()
    CHAR = auto()
    UCHAR = auto()
    BYTE = auto()
    STRING = auto()


#     CSTRING = auto()
#     UNICODE = auto()

DATA_TYPES = [
    "WORD",
    "DWORD",
    "FLOAT",
    "DOUBLE",
    "CHAR",
    "UCHAR",
    "BYTE",
    "STRING",
]  # , "CSTRING", "UNICODE"]


@dataclass
class XTemplateMemberDefinition:
    is_arr: bool
    type: XDataType | str
    name: str = ""
    dimensions: list[XToken] = field(default_factory=list)


class XRestrictionType(Enum):
    OPEN = auto()
    CLOSED = auto()
    RESTRICTED = auto()


@dataclass
class XTemplateDefinition:
    type: XRestrictionType
    name: str
    uuid: UUID
    members: list[XTemplateMemberDefinition]


class XTextParser:
    def __init__(self):
        self.index = 0
        self.tokens: list[XToken] = []
        self.file: XFile = XFile()
        self.templates: dict[str, XTemplateDefinition] = {}

    def peek(self) -> XToken:
        try:
            return self.tokens[self.index]
        except IndexError:
            return XToken(XTokenType.EOF, "EOF", self.index)

    def consume(self) -> XToken:
        try:
            token = self.tokens[self.index]
            self.index += 1
            return token
        except IndexError:
            return XToken(XTokenType.EOF, "EOF", self.index)

    def parse_template_def_member(self) -> XTemplateMemberDefinition:
        if (not (type_tok := self.peek()).type == XTokenType.IDENT) or (
            not type_tok.val in DATA_TYPES + ["array"]
        ):
            raise ParseError(
                f"`{type_tok.val}` at index {type_tok.idx} is not a valid data type"
            )

        typ = self.consume().val

        if typ == "array":
            if (not (type_tok := self.peek()).type == XTokenType.IDENT) or (
                not type_tok.val in DATA_TYPES
            ):
                raise ParseError(
                    f"`{type_tok.val}` at index {type_tok.idx} is not a valid data type"
                )

            typ = self.consume().val

            if not (name_or_size_tok := self.peek()).type in (
                XTokenType.IDENT,
                XTokenType.L_SQ_BRACKET,
            ):
                if name_or_size_tok.type == XTokenType.SEMI:
                    raise ParseError("arrays must have a size")
                raise ParseError(
                    f"`{name_or_size_tok.val}` at index {name_or_size_tok.idx} is not a valid array name/size"
                )

            name = ""
            if name_or_size_tok.type == XTokenType.IDENT:
                name = self.consume().val

                if (
                    not (name_or_size_tok := self.peek()).type
                    == XTokenType.L_SQ_BRACKET
                ):
                    if name_or_size_tok.type == XTokenType.SEMI:
                        raise ParseError("arrays must have a size")
                    raise ParseError(
                        f"`{name_or_size_tok.val}` at index {name_or_size_tok.idx} is not a valid array size"
                    )

            dim_sizes: list[XToken] = []
            while not self.peek().type in (XTokenType.EOF, XTokenType.SEMI):
                if not (l_sq_brack := self.peek()).type == XTokenType.L_SQ_BRACKET:
                    raise ParseError(
                        f"expected '[' during member def at {l_sq_brack.idx}, got `{l_sq_brack.val}`"
                    )

                self.consume()

                if not (dim_size_tok := self.peek()).type in (
                    XTokenType.NUMBER,
                    XTokenType.IDENT,
                ):
                    raise ParseError(
                        f"`{dim_size_tok.val}` at index {dim_size_tok.idx} is not a valid array dimension size"
                    )

                dim_size = self.consume().val

                if dim_size_tok.type == XTokenType.NUMBER and "-." in dim_size:
                    raise ParseError(
                        f"`{dim_size}` at index {dim_size_tok.idx} is not a valid array dimension size"
                    )

                if not (r_sq_brack := self.peek()).type == XTokenType.R_SQ_BRACKET:
                    raise ParseError(
                        f"expected '[' during member def at {r_sq_brack.idx}, got `{r_sq_brack.val}`"
                    )

                self.consume()
                dim_sizes.append(dim_size_tok)

            if (semi := self.peek()).type == XTokenType.EOF:
                raise ParseError(f"unexpected EOF during member def at {semi.idx}")

            self.consume()

            if self.peek().type == XTokenType.EOL:
                self.consume()

            return XTemplateMemberDefinition(
                True, getattr(XDataType, typ), name, dim_sizes
            )
        else:
            if not (name_tok := self.peek()).type in (
                XTokenType.IDENT,
                XTokenType.SEMI,
            ):
                raise ParseError(
                    f"`{name_tok}` at index {name_tok.idx} is not a valid member name"
                )

            name = ""
            if name_tok.type == XTokenType.IDENT:
                name = self.consume().val

                if not self.peek().type == XTokenType.SEMI:
                    raise ParseError(f"expected ';' after member name")

            # when semi colon
            self.consume()

            if self.peek().type == XTokenType.EOL:
                self.consume()

            return XTemplateMemberDefinition(False, getattr(XDataType, typ), name)

    def try_parse_template_def(self):
        tok = self.peek()
        if tok.type == XTokenType.IDENT and tok.val == "template":
            self.consume()

            if not (name_tok := self.peek()).type == XTokenType.IDENT:
                raise ParseError(
                    f"`{name_tok.val}` at index {name_tok.idx} is not a valid template name"
                )

            name = self.consume().val

            if name in self.templates:
                raise ParseError(
                    f"reinstantiation of template `{name}` at {name_tok.idx} is not allowed"
                )

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

            if not (newline := self.peek()).type == XTokenType.EOL:
                raise ParseError(
                    f"expected newline during template def at {newline.idx}, got `{newline.val}`"
                )

            self.consume()

            members: list[XTemplateMemberDefinition] = []
            while not self.peek().type in (
                XTokenType.EOF,
                XTokenType.L_SQ_BRACKET,
                XTokenType.R_BRACKET,
            ):
                members.append(self.parse_template_def_member())

            if (eof := self.peek()).type == XTokenType.EOF:
                raise ParseError(f"unexpected EOF during template def at {eof.idx}")

            if self.peek().type == XTokenType.R_BRACKET:
                self.consume()

                self.templates[name] = XTemplateDefinition(
                    XRestrictionType.CLOSED, name, UUID(uuid), members
                )
            else:
                raise ParseError("TODO: open/restricted templates")

        while not self.peek().type in (XTokenType.EOL, XTokenType.EOF):
            self.consume()

        if self.peek().type == XTokenType.EOL:
            self.consume()

    def parse(self, tokens: list[XToken]) -> XFile:
        self.index = 0
        self.tokens = tokens
        self.file = XFile()
        self.templates: dict[str, XTemplateDefinition] = {}

        while not self.peek().type == XTokenType.EOF:
            self.try_parse_template_def()
