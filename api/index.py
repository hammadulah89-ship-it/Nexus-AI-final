import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

for path in [parent_dir, current_dir, os.getcwd()]:
    if path and path not in sys.path:
        sys.path.insert(0, path)

from main import app
