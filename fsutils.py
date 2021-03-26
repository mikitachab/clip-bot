import contextlib
import tempfile
import os


@contextlib.contextmanager
def mkstemp(suffix=""):
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    yield path
    os.remove(path)