from typing import Union, Optional, Any, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
import os
import atexit


# --
# # Harness
#
# A simple RAP-compatible test harness.

TPrimitive = Union[str, bool, int, float, None, list, dict]


class Check:
    @staticmethod
    def Same(a: TPrimitive, b: TPrimitive, exact: bool = True) -> bool:
        """Tells if `a` and `b` are same (~equals)."""
        if isinstance(a, list) and isinstance(b, list):
            if (n := len(a) != len(b)) and exact:
                return False
            else:
                for i, v in enumerate(b):
                    if i >= n:
                        break
                    if not same(v, a[i]):
                        return False
            return True
        elif isinstance(a, dict) and isinstance(b, dict):
            if exact and len(a) != len(b):
                return False
            else:
                for k, v in b.items():
                    if k not in a or not same(v, a[k]):
                        return False
                return True
        else:
            return a == b


def Counter() -> Iterator[int]:
    i = 0
    while True:
        yield i
        i += 1


counter = Counter()


@dataclass
class TestStatus:
    id: int = field(default_factory=lambda: next(counter))
    success: int = 0
    errors: int = 0
    exception: Optional[Exception] = None

    @property
    def total(self) -> int:
        return self.success + self.errors


TESTS: list[TestStatus] = []
All = TestStatus()


def out(message: str):
    print(message)


def fail(message: Union[Exception, str], **data: Any):
    if isinstance(message, Exception):
        exception: Exception = message
        out(
            f"!!! EXCP {f'{message}: [{exception.__class__.__name__}] {exception}' if message else f'[{exception.__class__.__name__}] {exception}'}"
        )
        tb = exception.__traceback__
        while tb:
            code = tb.tb_frame.f_code
            out(
                f" …  in {code.co_name:15s} at line {tb.tb_lineno:4d} in {os.path.relpath(code.co_filename, '.')}",
            )
            tb = tb.tb_next
    else:
        out(f" !  FAIL {message}")
        for k, v in data.items():
            out(f"   {k}={v}")
    return record(False)


def record(result: bool) -> bool:
    status: Optional[TestStatus] = TESTS[-1] if TESTS else None
    if result:
        if status:
            status.success += 1
        All.success += 1
    else:
        if status:
            status.errors += 1
        All.errors += 1
    return result


def same(value: TPrimitive, expected: TPrimitive) -> bool:
    return record(
        fail(f"Value should be like {expected}, got: {value}")
        if not Check.Same(value, expected)
        else True
    )


@contextmanager
def test(name: str):
    status = TestStatus()
    out(f"=== TEST {name} test={status.id}")
    parent: Optional[TestStatus] = TESTS[-1] if TESTS else None
    TESTS.append(status)
    try:
        yield TestStatus
    except Exception as e:
        status.exception = e
        fail(e)
    finally:
        TESTS.pop()
        end(status)


def end(status: TestStatus = All) -> int:
    if status is All:
        out(
            f"EFAIL! passed={status.success}/{status.total}"
            if status.errors
            else f"EOK. success={status.success}"
        )
    elif status.errors:
        out(f"-!- FAIL test={status.id} failed={status.errors}/{status.total}")
    elif status.success:
        out(f"... OK passed={status.success} test={status.id}")
    else:
        out(f" -  NOP test={status.id}")

    return 1 if status.errors else 0


def hlo(message: str):
    out(f"\nHLO:{message}")


atexit.register(end)
# EOF
