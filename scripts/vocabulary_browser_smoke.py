"""Compatibility entry point: the word and reading UIs now share the topic curriculum.

The full current public flow is checked by topic_browser_smoke.py.
"""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("topic_browser_smoke.py")),run_name="__main__")
