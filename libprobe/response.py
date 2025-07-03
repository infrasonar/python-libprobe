from enum import Enum
from typing import NamedTuple


class FileType(Enum):
    UNKNOWN = 0
    IMAGE = 1
    XML = 2
    JSON = 3
    XLSX = 4
    CSV = 5
    DOCX = 6
    PDF = 7
    TEXT = 8
    MARKDOWN = 9
    COMPRESSED = 10
    PYTHON = 11

    @classmethod
    def get(cls, num: int):
        try:
            return cls(int)
        except Exception:
            return cls(0)


class UploadFile(NamedTuple):
    id: int
    size: int
    name: str
    type: FileType
    created: int  # UNIX Timestamp
