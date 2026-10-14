"""Compatibility import for the Juku monitor wire dialect in RAVI."""
import importlib
import sys
from ravi_bootstrap import require

require()
sys.modules[__name__] = importlib.import_module("ravi.backends.juku.protocol")
