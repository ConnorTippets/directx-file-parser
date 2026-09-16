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
        if (not (type_tok := self.peek()).type is XTokenType.IDENT) or (
            not type_tok.val in DATA_TYPES + ["array"] + list(self.templates.keys())
        ):
            raise ParseError(
                f"`{type_tok.val}` at index {type_tok.idx} is not a valid data type"
            )

        typ = self.consume().val
        is_template = typ in self.templates

        if typ == "array":
            if (not (type_tok := self.peek()).type is XTokenType.IDENT) or (
                not type_tok.val in DATA_TYPES + list(self.templates.keys())
            ):
                raise ParseError(
                    f"`{type_tok.val}` at index {type_tok.idx} is not a valid data type"
                )

            typ = self.consume().val
            is_template = typ in self.templates

            if not (name_or_size_tok := self.peek()).type in (
                XTokenType.IDENT,
                XTokenType.L_SQ_BRACKET,
            ):
                if name_or_size_tok.type is XTokenType.SEMI:
                    raise ParseError("arrays must have a size")
                raise ParseError(
                    f"`{name_or_size_tok.val}` at index {name_or_size_tok.idx} is not a valid array name/size"
                )

            name = ""
            if name_or_size_tok.type is XTokenType.IDENT:
                name = self.consume().val

                if (
                    not (name_or_size_tok := self.peek()).type
                    is XTokenType.L_SQ_BRACKET
                ):
                    if name_or_size_tok.type is XTokenType.SEMI:
                        raise ParseError("arrays must have a size")
                    raise ParseError(
                        f"`{name_or_size_tok.val}` at index {name_or_size_tok.idx} is not a valid array size"
                    )

            dim_sizes: list[XToken] = []
            while not self.peek().type in (XTokenType.EOF, XTokenType.SEMI):
                if not (l_sq_brack := self.peek()).type is XTokenType.L_SQ_BRACKET:
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

                if dim_size_tok.type is XTokenType.NUMBER and "-." in dim_size:
                    raise ParseError(
                        f"`{dim_size}` at index {dim_size_tok.idx} is not a valid array dimension size"
                    )

                if not (r_sq_brack := self.peek()).type is XTokenType.R_SQ_BRACKET:
                    raise ParseError(
                        f"expected '[' during member def at {r_sq_brack.idx}, got `{r_sq_brack.val}`"
                    )

                self.consume()
                dim_sizes.append(dim_size_tok)

            if (semi := self.peek()).type is XTokenType.EOF:
                raise ParseError(f"unexpected EOF during member def at {semi.idx}")

            self.consume()

            return XTemplateMemberDefinition(
                True, typ if is_template else getattr(XDataType, typ), name, dim_sizes
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
            if name_tok.type is XTokenType.IDENT:
                name = self.consume().val

                if not self.peek().type is XTokenType.SEMI:
                    raise ParseError(f"expected ';' at {self.peek().idx}")

            # when semi colon
            self.consume()

            return XTemplateMemberDefinition(
                False, typ if is_template else getattr(XDataType, typ), name
            )

    def try_parse_template_def(self):
        tok = self.peek()
        if tok.type is XTokenType.IDENT and tok.val == "template":
            self.consume()

            if not (name_tok := self.peek()).type is XTokenType.IDENT:
                raise ParseError(
                    f"`{name_tok.val}` at index {name_tok.idx} is not a valid template name"
                )

            name = self.consume().val

            if name in self.templates:
                raise ParseError(
                    f"reinstantiation of template `{name}` at {name_tok.idx} is not allowed"
                )

            if not (l_brack := self.peek()).type is XTokenType.L_BRACKET:
                raise ParseError(
                    f"expected '{{' during template def at {l_brack.idx}, got `{l_brack.val}`"
                )

            self.consume()

            if not (uuid_tok := self.peek()).type is XTokenType.UUID:
                raise ParseError(
                    f"expected UUID during template def at {uuid_tok.idx}, got `{uuid_tok.val}`"
                )

            uuid = self.consume().val

            members: list[XTemplateMemberDefinition] = []
            while not self.peek().type in (
                XTokenType.EOF,
                XTokenType.L_SQ_BRACKET,
                XTokenType.R_BRACKET,
            ):
                members.append(self.parse_template_def_member())

            if (tok := self.peek()).type is XTokenType.EOF:
                raise ParseError(f"unexpected EOF during template def at {tok.idx}")

            self.consume()
            if tok.type is XTokenType.R_BRACKET:
                self.templates[name] = XTemplateDefinition(
                    XRestrictionType.CLOSED, name, UUID(uuid), members
                )
            else:
                if self.peek().type is XTokenType.ELLIPSIS:
                    restrict_type = XRestrictionType.OPEN
                    self.consume()
                elif self.peek().type is XTokenType.IDENT:
                    restrict_type = XRestrictionType.RESTRICTED

                    print(self.peek())
                    breakpoint()
                    # while self.peek():
                    #     # TODO: finish this~!!
                else:
                    raise ParseError(
                        f"unexpected token `{self.peek().val}` during restriction def at {self.peek().idx}"
                    )

                if not self.peek().type is XTokenType.R_SQ_BRACKET:
                    raise ParseError(f"expected ']' at {self.peek().idx}")
                self.consume()

                if not (r_brack := self.peek()).type is XTokenType.R_BRACKET:
                    raise ParseError(f"expected '}}' at {r_brack.idx}")

                self.consume()

                self.templates[name] = XTemplateDefinition(
                    restrict_type, name, UUID(uuid), members
                )

    def parse(self, tokens: list[XToken]) -> XFile:
        self.index = 0
        self.tokens = tokens
        self.file = XFile()
        self.templates: dict[str, XTemplateDefinition] = {}

        while not self.peek().type is XTokenType.EOF:
            self.try_parse_template_def()
