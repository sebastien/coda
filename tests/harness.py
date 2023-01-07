from typing import Union, Optional, Any, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from fcntl import fcntl, F_GETFL, F_SETFL
import os
import atexit
import subprocess
import time
import select


# --
# # Harness
#
# A simple RAP-compatible test harness.

TPrimitive = Union[str, bool, int, float, None, list, dict]


class StopTesting(Exception):
    pass


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
        context(exception)
        # tb = exception.__traceback__
        # while tb:
        #     code = tb.tb_frame.f_code
        #     out(
        #         f" …  in {code.co_name:15s} at line {tb.tb_lineno:4d} in {os.path.relpath(code.co_filename, '.')}",
        #     )
        #     tb = tb.tb_next
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
        if OPTIONS[-1].stopOnFail:
            raise StopTesting()
    return result


def same(value: TPrimitive, expected: TPrimitive) -> bool:
    return (
        fail(f"Value should be like {expected}, got: {value}")
        if not Check.Same(value, expected)
        else record(True)
    )


@contextmanager
def test(name: str):
    status = TestStatus()
    out(f"=== TEST {name} test={status.id}")
    parent: Optional[TestStatus] = TESTS[-1] if TESTS else None
    TESTS.append(status)
    try:
        yield TestStatus
    except StopTesting as e:
        raise context(e)
    except Exception as e:
        status.exception = e
        fail(e)
        context(e)
    finally:
        TESTS.pop()
        end(status)


def context(exception: Exception) -> Exception:
    """Prints out the context for this exception"""
    path = os.path.abspath(__file__)
    tb = exception.__traceback__
    while tb:
        # if path == frame.f_code.co_filename:
        frame = tb.tb_frame
        code = frame.f_code
        if frame.f_code.co_filename != path:
            out(
                f" …  in {code.co_name + '(…)':15s} at line {frame.f_lineno+1:4d} in {os.path.relpath(frame.f_code.co_filename, '.')}"
            )
        tb = tb.tb_next
    return exception


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


@dataclass
class Options:
    stopOnFail: bool = True


OPTIONS: list[Options] = [Options()]


@contextmanager
def harness(*, stopOnFail: bool = True) -> Options:
    options = Options(stopOnFail=stopOnFail)
    OPTIONS.append(options)
    try:
        yield options
    except StopTesting:
        out(f" .  STOP on failure at check {All.total}, after {All.success} passed.")
    except Exception as e:
        raise e
    finally:
        OPTIONS.pop()
    return options


class RAPParser:
    RE_DIRECTIVE = r"...[ ][A-Z]+"


RUNNERS = {"*": "sh", "py": "python"}


def run(path: str, timeout: Optional[float] = None, bufsize: int = 1024) -> TestStatus:
    ext: str = path.rsplit(".", 1)[-1]
    cmd: list[str] = [RUNNERS.get(ext, RUNNERS["*"]), path]
    pipe: subprocess.Popen = subprocess.Popen(  # nosec: B603
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        start_new_session=True,
    )
    assert pipe.stderr is not None
    assert pipe.stdout is not None
    # We set the pipes to non blocking, this should be of benefit when
    # the process (service) is terminating.
    fcntl(
        fd_err := pipe.stderr.fileno(), F_SETFL, fcntl(fd_err, F_GETFL) | os.O_NONBLOCK
    )
    fcntl(
        fd_out := pipe.stdout.fileno(), F_SETFL, fcntl(fd_out, F_GETFL) | os.O_NONBLOCK
    )
    waiting = [fd_err, fd_out]
    name = os.path.basename(path)
    print(f">>> RUN {name} path={path}")
    started = time.monotonic()
    while waiting:
        for fd in select.select(waiting, [], [], timeout)[0]:
            chunk = os.read(fd, bufsize)
            if chunk:
                t: str = time.strftime("%Y-%M-%dT%H:%m:%S")
                prefix = f"{'   ' if fd == fd_out else '!!!'} "
                for line in str(chunk, "utf8").split("\n"):
                    print(f"{prefix}{line}")
            else:
                os.close(fd)
                waiting = [_ for _ in waiting if _ != fd]
    print(
        f"<<< path={os.path.relpath(path,'.')} elapsed={time.monotonic() - started:0.3f}s"
    )
    return TestStatus()


if __name__ == "__main__":
    import glob, sys

    for path in sorted(
        _
        for _ in (os.path.abspath(_) for _ in sys.argv[1:] or glob.glob("tests/*"))
        if _ != os.path.abspath(__file__) and _.rsplit(".", 1)[-1] in ("py", "sh")
    ):
        status = run(path)

else:
    atexit.register(end)
# EOF
