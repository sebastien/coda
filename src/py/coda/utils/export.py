from typing import NamedTuple, cast
from enum import Enum
from pathlib import Path


def asPrimitive(value):
    """Exports the given value to be JSON-serializable."""
    if isinstance(value, Enum):
        return value.name
    elif isinstance(value, tuple) and hasattr(value, "_asdict"):  # NamedTuple
        return asPrimitive(cast(NamedTuple, value)._asdict())
    elif isinstance(value, Path):
        return str(value)
    elif isinstance(value, list):
        return [asPrimitive(_) for _ in value]
    elif isinstance(value, tuple):
        return tuple(*(asPrimitive(_) for _ in value))
    elif isinstance(value, dict):
        return {k: asPrimitive(v) for k, v in value.items()}
    else:
        return value


# EOF
