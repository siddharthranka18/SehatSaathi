import importlib
import sys
from pathlib import Path

# Ensure repo root is on sys.path when running this script
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

importlib.invalidate_caches()
try:
    m = importlib.import_module('backend.app.main')
    print('OK', hasattr(m, 'app'))
except Exception as e:
    print('ERROR', type(e).__name__, e)
