import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from azure_tools_api.main import app

