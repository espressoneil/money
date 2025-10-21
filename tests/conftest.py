# This is black magic that allows pytest tests to import modules by adding
# the money source's parent to path to allow imports inside tests.
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))