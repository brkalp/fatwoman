"""Auto-loaded by the python interpreter when the project root is on
PYTHONPATH (the run_*.sh scripts export it). This makes logging configuration
part of the python installation itself: any script started under the project
gets the project logger without a single setup call in the script.
"""
try:
    import core  # noqa: F401
except Exception:
    pass
