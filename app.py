# Vercel entrypoint shim: Vercel's Python runtime looks for a top-level
# `app` in app.py (see vercel.com/docs/functions/runtimes/python).
# The real FastAPI app lives in src/api/main.py and is imported unchanged.
import ctypes
import glob
import os
import shutil
import sys


def _ensure_libgomp() -> None:
    """Vercel's Python runtime image has no system libgomp (OpenMP), which
    LightGBM's native library needs (lib_lightgbm.so has DT_NEEDED
    libgomp.so.1 and no RPATH). scikit-learn's wheel bundles a libgomp copy
    under a mangled SONAME, so preloading it does not satisfy the linker.
    Instead expose it under the exact name libgomp.so.1 via LD_LIBRARY_PATH.
    LD_LIBRARY_PATH is only read at process start, so the first boot re-execs
    itself once with the path set. No-op where libgomp already exists
    (local dev, Render)."""
    if os.environ.get("_GMF_FORCE_GOMP_PATCH") != "1":
        try:
            ctypes.CDLL("libgomp.so.1")
            return  # System libgomp present; nothing to do.
        except OSError:
            pass
    if os.environ.get("_GMF_GOMP_REEXEC"):
        return  # Already re-executed once; never loop.
    try:
        import sklearn  # noqa: F401

        site_packages = os.path.dirname(os.path.dirname(sklearn.__file__))
        hits = sorted(
            glob.glob(os.path.join(site_packages, "scikit_learn.libs", "libgomp*"))
            + glob.glob(os.path.join(site_packages, "sklearn.libs", "libgomp*"))
        )
        if not hits:
            return  # Let the LightGBM import raise its own clear error.
        target_dir = "/tmp/_gmf_libgomp"
        os.makedirs(target_dir, exist_ok=True)
        link = os.path.join(target_dir, "libgomp.so.1")
        if not os.path.exists(link):
            try:
                os.symlink(hits[0], link)
            except OSError:
                shutil.copyfile(hits[0], link)
        os.environ["LD_LIBRARY_PATH"] = (
            target_dir + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
        )
        os.environ["_GMF_GOMP_REEXEC"] = "1"
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception:
        pass  # Fall through; LightGBM will raise its own clear error.


_ensure_libgomp()

from src.api.main import app  # noqa: F401,E402
