# Vercel entrypoint shim: Vercel's Python runtime looks for a top-level
# `app` in app.py (see vercel.com/docs/functions/runtimes/python).
# The real FastAPI app lives in src/api/main.py and is imported unchanged.
from src.api.main import app  # noqa: F401

# Preview deployment trigger for branch vercel-preview (no functional change).
