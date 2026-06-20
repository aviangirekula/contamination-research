"""Make the repo root importable so `import detectors`/`eval`/`extraction` work in tests."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
