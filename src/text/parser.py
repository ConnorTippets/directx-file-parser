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
class XTemplateMember:
    is_arr: bool
    type: XDataType | str
    name: str = ""
    dimensions: list[XToken] = field(default_factory=list)


class XRestrictionType(Enum):
    OPEN = auto()
    CLOSED = auto()
    RESTRICTED = auto()


@dataclass
class XTemplateRestriction:
    template: str
    uuid: UUID | None = None


@dataclass
class XTemplate:
    type: XRestrictionType
    name: str
    uuid: UUID
    members: list[XTemplateMember]
    restrictions: list[XTemplateRestriction]


type XDataField = float | str | list[float] | list[str] | dict[str, XDataField]


@dataclass
class XData:
    template: str
    name: str
    uuid: UUID | None
    fields: dict[str, XDataField]
    nested_objects: list[XData]


@dataclass
class XNestedMember:
    template: str
    fields: dict[str, XDataField]


class XTextParser:
    def __init__(self):
        self.index = 0
        self.tokens: list[XToken] = []
        self.file: XFile = XFile()
        self.templates: dict[str, XTemplate] = {}
        self.data: list[XData] = []

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

    def parse_template_def_member(self) -> XTemplateMember:
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
                        f"expected '[' during member def at idx {l_sq_brack.idx}, got `{l_sq_brack.val}`"
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
                        f"expected '[' during member def at idx {r_sq_brack.idx}, got `{r_sq_brack.val}`"
                    )

                self.consume()
                dim_sizes.append(dim_size_tok)

            if (semi := self.peek()).type is XTokenType.EOF:
                raise ParseError(f"unexpected EOF during member def at idx {semi.idx}")

            self.consume()

            return XTemplateMember(
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
                    raise ParseError(f"expected ';' at idx {self.peek().idx}")

            # when semi colon
            self.consume()

            return XTemplateMember(
                False, typ if is_template else getattr(XDataType, typ), name
            )

    def try_parse_template_def(self) -> bool:
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
                    f"reinstantiation of template `{name}` at idx {name_tok.idx} is not allowed"
                )

            if not (l_brack := self.peek()).type is XTokenType.L_BRACKET:
                raise ParseError(
                    f"expected '{{' during template def at idx {l_brack.idx}, got `{l_brack.val}`"
                )

            self.consume()

            if not (uuid_tok := self.peek()).type is XTokenType.UUID:
                raise ParseError(
                    f"expected UUID during template def at idx {uuid_tok.idx}, got `{uuid_tok.val}`"
                )

            uuid = self.consume().val

            members: list[XTemplateMember] = []
            while not self.peek().type in (
                XTokenType.EOF,
                XTokenType.L_SQ_BRACKET,
                XTokenType.R_BRACKET,
            ):
                members.append(self.parse_template_def_member())

            if (tok := self.peek()).type is XTokenType.EOF:
                raise ParseError(f"unexpected EOF during template def at idx {tok.idx}")

            self.consume()
            if tok.type is XTokenType.R_BRACKET:
                self.templates[name] = XTemplate(
                    XRestrictionType.CLOSED, name, UUID(uuid), members, []
                )
            else:
                tok = self.peek()
                restrictions: list[XTemplateRestriction] = []

                if tok.type is XTokenType.ELLIPSIS:
                    restrict_type = XRestrictionType.OPEN
                    self.consume()
                elif tok.type is XTokenType.IDENT:
                    restrict_type = XRestrictionType.RESTRICTED

                    while not tok.type in (XTokenType.R_SQ_BRACKET, XTokenType.EOF):
                        templ_name = self.consume().val
                        next_tok = self.peek()

                        templ_uuid = ""
                        if next_tok.type is XTokenType.UUID:
                            templ_uuid = self.consume().val
                            next_tok = self.peek()

                        if next_tok.type is XTokenType.R_SQ_BRACKET:
                            if templ_uuid:
                                restrictions.append(
                                    XTemplateRestriction(templ_name, UUID(templ_uuid))
                                )
                            else:
                                restrictions.append(XTemplateRestriction(templ_name))

                            break
                        elif next_tok.type is XTokenType.COMMA:
                            self.consume()
                        else:
                            raise ParseError(
                                f"unexpected token `{next_tok.val}` during restriction def at idx {next_tok.idx}"
                            )

                        if templ_uuid:
                            restrictions.append(
                                XTemplateRestriction(templ_name, UUID(templ_uuid))
                            )
                        else:
                            restrictions.append(XTemplateRestriction(templ_name))

                        tok = self.peek()
                else:
                    raise ParseError(
                        f"unexpected token `{self.peek().val}` during restriction def at idx {self.peek().idx}"
                    )

                if not self.peek().type is XTokenType.R_SQ_BRACKET:
                    raise ParseError(f"expected ']' at idx {self.peek().idx}")
                self.consume()

                if not (r_brack := self.peek()).type is XTokenType.R_BRACKET:
                    raise ParseError(f"expected '}}' at idx {r_brack.idx}")

                self.consume()

                self.templates[name] = XTemplate(
                    restrict_type, name, UUID(uuid), members, restrictions
                )

            return True
        return False

    def parse_data_member_atom(self) -> float | str:
        tok = self.peek()
        if not tok.type in (
            XTokenType.NUMBER,
            XTokenType.STRING,
        ):
            raise ParseError(f"invalid data member at idx {tok.idx}")

        if tok.type is XTokenType.NUMBER:
            self.consume()
            return float(tok.val)
        elif tok.type is XTokenType.STRING:
            self.consume()
            return tok.val
        else:
            raise RuntimeError("unreachable")

    def parse_nested_data(self) -> XData:
        tok = self.peek()
        if not tok.type in (
            XTokenType.IDENT,
            XTokenType.L_BRACKET,
        ):
            raise ParseError(f"invalid nested data at idx {tok.idx}")

        if tok.type is XTokenType.IDENT:
            # nested data definition

            out = self.try_parse_data()

            if out is None:
                raise RuntimeError("unreachable")

            return out
        elif tok.type is XTokenType.L_BRACKET:
            # reference to previous data definition

            self.consume()
            if not (tok := self.peek()).type in (XTokenType.IDENT, XTokenType.UUID):
                raise ParseError(
                    f"unexpected token `{tok.val}` during data ref at idx {tok.idx}"
                )

            ref_name = ""
            if tok.type is XTokenType.IDENT:
                ref_name = self.consume().val
                tok = self.peek()

            if not tok.type in (XTokenType.UUID, XTokenType.R_BRACKET):
                raise ParseError(
                    f"unexpected token `{tok.val}` during data ref at idx {tok.idx}"
                )

            ref_uuid = ""
            if tok.type is XTokenType.UUID:
                ref_uuid = self.consume().val
                tok = self.peek()

            if tok.type is XTokenType.R_BRACKET:
                self.consume()
            else:
                raise ParseError(
                    f"unexpected token `{tok.val}` during data ref at idx {tok.idx}"
                )

            if ref_name and ref_uuid:
                try:
                    return next(
                        filter(
                            lambda x: x.name == ref_name and str(x.uuid) == ref_uuid,
                            self.data,
                        )
                    )
                except StopIteration:
                    raise ParseError(
                        f"undefined data object `{ref_name}` with uuid `{ref_uuid}` at idx {tok.idx}"
                    )
            elif ref_name:
                try:
                    return next(filter(lambda x: x.name == ref_name, self.data))
                except StopIteration:
                    raise ParseError(
                        f"undefined data object `{ref_name}` at idx {tok.idx}"
                    )
            elif ref_uuid:
                try:
                    return next(filter(lambda x: str(x.uuid) == ref_uuid, self.data))
                except StopIteration:
                    raise ParseError(
                        f"undefined data object `{ref_uuid}` at idx {tok.idx}"
                    )
            else:
                raise RuntimeError("unreachable")
        else:
            raise RuntimeError("unreachable")

    def parse_members_of(self, template: XTemplate) -> dict[str, XDataField]:
        parsed_members: dict[str, XDataField] = {}
        for member in template.members:
            elements = 1
            if member.is_arr:
                if not len(member.dimensions) == 1:
                    raise ParseError(
                        "arrays with more than one dimensions are not supported"
                    )

                dim = member.dimensions[0]
                if dim.type is XTokenType.NUMBER:
                    elements = dim.val

                    if "." in elements or "-" in elements:
                        raise ParseError(
                            f"array dim at `{dim.idx}` must be a positive integer"
                        )
                elif dim.type is XTokenType.IDENT:
                    try:
                        ref = parsed_members[dim.val]
                    except KeyError:
                        raise ParseError(f"undefined array dimension at idx {dim.idx}")

                    # i have to use type here and not isinstance because of type checking
                    # i've never seen it freak out over isinstance so hard... try it yourself
                    if (not type(ref) is float) or (not ref.is_integer() or ref < 0):
                        raise ParseError(
                            f"array dim at `{dim.idx}` must be a positive integer"
                        )

                    elements = ref
                else:
                    raise ParseError(
                        f"unexpected token `{dim.val}` during array def at idx {dim.idx}"
                    )

                elements = int(elements)

            parsed_elems = []
            for i in range(elements):
                if member.type in self.templates:
                    if not isinstance(member.type, str):
                        raise RuntimeError("unreachable")

                    parsed_elems.append(
                        XNestedMember(
                            member.type,
                            self.parse_members_of(self.templates[member.type]),
                        )
                    )
                else:
                    parsed_elems.append(self.parse_data_member_atom())

                if i < elements - 1:
                    if not (tok := self.peek()).type is XTokenType.COMMA:
                        raise ParseError(
                            f"expected comma during array at idx {tok.idx}"
                        )

                    self.consume()

            if not (tok := self.peek()).type is XTokenType.SEMI:
                raise ParseError(f"expected semicolon after member at idx {tok.idx}")

            self.consume()

            if member.is_arr:
                parsed_members[member.name] = parsed_elems
            else:
                parsed_members[member.name] = parsed_elems[0]

        return parsed_members

    def try_parse_data(self) -> XData | None:
        tok = self.peek()
        if tok.type is XTokenType.IDENT:
            if tok.val in self.templates:
                template = self.templates[tok.val]
                self.consume()

                if not (name_tok := self.peek()).type in (
                    XTokenType.IDENT,
                    XTokenType.L_BRACKET,
                ):
                    raise ParseError(
                        f"unexpected token `{name_tok.val}` during data def at idx {name_tok.idx}"
                    )

                name = ""
                if name_tok.type is XTokenType.IDENT:
                    name = self.consume().val

                if not self.peek().type is XTokenType.L_BRACKET:
                    raise ParseError(
                        f"expected '{{' during data def at idx {self.peek().idx}"
                    )

                self.consume()

                uuid = ""
                if self.peek().type is XTokenType.UUID:
                    uuid = self.consume().val

                members = self.parse_members_of(template)

                nested_data_objects = []
                if not template.type is XRestrictionType.CLOSED:
                    while not self.peek().type in (
                        XTokenType.R_BRACKET,
                        XTokenType.EOF,
                    ):
                        nested_data_object = self.parse_nested_data()

                        if template.type is XRestrictionType.RESTRICTED:
                            allowed = False
                            for restriction in template.restrictions:
                                if (
                                    not restriction.template
                                    == nested_data_object.template
                                ):
                                    continue

                                if not restriction.uuid is None:
                                    if (
                                        not restriction.uuid
                                        == self.templates[
                                            nested_data_object.template
                                        ].uuid
                                    ):
                                        continue

                                allowed = True

                            if not allowed:
                                raise ParseError(
                                    f"nesting template `{nested_data_object.template}` inside `{template.name}` is not allowed at idx {self.peek().idx}"
                                )

                        nested_data_objects.append(nested_data_object)

                if not self.peek().type is XTokenType.R_BRACKET:
                    raise ParseError(
                        f"unexpected token `{self.peek().val}` at idx {self.peek().idx}"
                    )

                self.consume()

                return XData(
                    tok.val,
                    name,
                    UUID(uuid) if uuid else None,
                    members,
                    nested_data_objects,
                )
            else:
                raise ParseError(f"undefined template `{tok.val}` at idx {tok.idx}")

    def parse(self, tokens: list[XToken]) -> XFile:
        self.index = 0
        self.tokens = tokens
        self.file = XFile()
        self.templates: dict[str, XTemplate] = {}
        self.data: list[XData] = []

        while not self.peek().type is XTokenType.EOF:
            if not self.try_parse_template_def():
                if (data := self.try_parse_data()) is None:
                    # not a template or data, it's probably invalid then
                    raise ParseError(f"unknown expression at idx {self.peek().idx}")
                else:
                    self.data.append(data)
