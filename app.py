# Vercel entrypoint shim: Vercel's Python runtime looks for a top-level
# `app` in app.py (see vercel.com/docs/functions/runtimes/python).
# The real FastAPI app lives in src/api/main.py and is imported unchanged.
import ctypes
import glob
import os


def _preload_libgomp() -> None:
    """Vercel's Python runtime image has no system libgomp (OpenMP), which
    LightGBM's native library needs. scikit-learn's wheel bundles a copy;
    load it globally before any LightGBM import so lib_lightgbm.so resolves.
    No-op on systems that already have libgomp (local dev, Render)."""
    try:
        import sklearn  # noqa: F401

        site_packages = os.path.dirname(os.path.dirname(sklearn.__file__))
        for pattern in ("scikit_learn.libs/libgomp*", "sklearn.libs/libgomp*"):
            hits = sorted(glob.glob(os.path.join(site_packages, pattern)))
            if hits:
                ctypes.CDLL(hits[0], mode=ctypes.RTLD_GLOBAL)
                return
    except Exception:
        pass  # Let a later LightGBM import raise its own clear error.


_preload_libgomp()

from src.api.main import app  # noqa: F401,E402
