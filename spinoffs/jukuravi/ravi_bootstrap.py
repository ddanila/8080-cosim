"""Locate the repository-pinned RAVI library independently of the working directory."""
import sys
from pathlib import Path


def require():
    source = Path(__file__).resolve().parents[2] / "third_party/ravi/src"
    if not (source / "ravi/__init__.py").is_file():
        raise ImportError("RAVI submodule missing: run git submodule update --init third_party/ravi")
    sys.path.insert(0, str(source))
    import ravi
    if (source / "ravi/__init__.py").is_file() and not Path(ravi.__file__).resolve().is_relative_to(source):
        raise ImportError("Another RAVI source is already imported; start a fresh process using the pinned dependency")
    if ravi.__version__ != "0.1.0":
        raise ImportError(f"Jukuravi requires ravi-core 0.1.0, found {ravi.__version__}")
