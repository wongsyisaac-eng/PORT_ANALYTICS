import sys
from pathlib import Path

# Let tests import backend modules the same way the scripts do (e.g. `import storage`).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
