# conftest.py — add project root to sys.path so tests can import project modules
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
