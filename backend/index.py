import sys
from pathlib import Path

# Add current dir to sys.path so routers and modules import correctly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import app
