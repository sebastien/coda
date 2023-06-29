from typing import Union
from io import IOBase
import json as basejson
from time import struct_time
from datetime import date, datetime
from dataclasses import is_dataclass
from enum import Enum

TJSON = Union[None, int, float, bool, list, dict]


def asPrimitive(value, *, currentDepth: int = 0):
    """Converts the given value to a primitive value that can be converted
    to JSON"""
    if value in (True, False, None) or type(value) in (float, int, int, str, str):
        return value
    elif isinstance(value, tuple) and hasattr(value, "_fields"):  # check for namedtuple
        return {
            k: asPrimitive(getattr(value, k), currentDepth=currentDepth + 1)
            for k in value._fields
        }
    elif isinstance(value, list) or isinstance(value, tuple) or isinstance(value, set):
        return [asPrimitive(v, currentDepth=currentDepth + 1) for v in value]
    elif isinstance(value, Enum):
        return asPrimitive(value.value)
    elif is_dataclass(value):
        return {
            k: asPrimitive(getattr(value, k), currentDepth=currentDepth + 1)
            for k in value.__annotations__
        }

    elif type(value) == dict:
        return {
            k: asPrimitive(v, currentDepth=currentDepth + 1) for k, v in value.items()
        }
    elif isinstance(value, datetime) or isinstance(value, date):
        return tuple(value.timetuple())
    elif isinstance(value, struct_time):
        return tuple(value)
    else:
        return value


def asJSON(value) -> str:
    return basejson.dumps(asPrimitive(value))


def unjson(data: Union[str, bytes, IOBase]) -> TJSON:
    """Parses JSON from a variety of sources"""
    if isinstance(data, str):
        return basejson.loads(data)
    elif isinstance(data, bytes):
        return basejson.loads(str(data, "utf8"))
    elif isinstance(data, IOBase):
        return basejson.load(data)
    else:
        raise ValueError("Unsupported data type: {type(data)}")


# EOF
