from dataclasses import dataclass, field
from typing import TypedDict
from enum import Enum, auto
from uuid import UUID


class ParseError(Exception): ...


class XHeader(TypedDict):
    version: str
    encoding: str
    float_size: str


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
class XTemplateMemberDef:
    is_arr: bool
    type: XDataType | str
    name: str = ""
    dimensions: list[int | str] = field(default_factory=list)


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
    members: list[XTemplateMemberDef]
    restrictions: list[XTemplateRestriction]


type XDataField = float | str | list[float] | list[str] | XNestedMember


@dataclass
class XTemplateMember:
    name: str
    val: XDataField


@dataclass
class XData:
    template: str
    name: str
    uuid: UUID | None
    fields: list[XTemplateMember]
    nested_objects: list[XData]


@dataclass
class XNestedMember:
    template: str
    fields: list[XTemplateMember]


@dataclass
class XFile:
    templates: dict[str, XTemplate]
    data: list[XData]


def parse_header(header: str) -> XHeader:
    if not header[0:4] == "xof ":
        raise ParseError("expected 'xof ' at position 0")

    version = header[4:8]
    encoding = header[8:12]
    float_size = header[8:16]

    return {"version": version, "encoding": encoding, "float_size": float_size}
