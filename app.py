# Vercel entrypoint shim: Vercel's Python runtime looks for a top-level
# `app` in app.py (see vercel.com/docs/functions/runtimes/python).
# The real FastAPI app lives in src/api/main.py and is imported unchanged.
import ctypes
import glob
import os
import re
import shutil


def _ensure_libgomp() -> None:
    """Vercel's Python runtime image has no system libgomp (OpenMP), which
    LightGBM's native library needs (lib_lightgbm.so has DT_NEEDED
    libgomp.so.1 and no RPATH). scikit-learn's wheel bundles a libgomp copy
    but under a mangled SONAME (e.g. libgomp-a34b3233.so.1.0.0), so a plain
    ctypes preload does not register the name the linker looks for. Make a
    copy in /tmp with its SONAME string rewritten to libgomp.so.1 and
    preload that with RTLD_GLOBAL; the linker then treats the dependency as
    already loaded. No-op where a system libgomp exists (local, Render)."""
    if os.environ.get("_GMF_FORCE_GOMP_PATCH") != "1":
        try:
            ctypes.CDLL("libgomp.so.1")
            return  # System libgomp present; nothing to do.
        except OSError:
            pass
    try:
        import sklearn  # noqa: F401

        site_packages = os.path.dirname(os.path.dirname(sklearn.__file__))
        hits = sorted(
            glob.glob(os.path.join(site_packages, "scikit_learn.libs", "libgomp*"))
            + glob.glob(os.path.join(site_packages, "sklearn.libs", "libgomp*"))
        )
        if not hits:
            return  # Let the LightGBM import raise its own clear error.
        data = bytearray(open(hits[0], "rb").read())
        sonames = set(re.findall(rb"libgomp-[\w.\-]+\.so[\w.]*", bytes(data)))
        if not sonames:
            # SONAME already plain (or unrecognised); try loading as-is.
            ctypes.CDLL(hits[0], mode=ctypes.RTLD_GLOBAL)
            return
        soname = sorted(sonames, key=len)[-1]
        patched = b"libgomp.so.1"
        pad = len(soname) - len(patched)
        if pad < 0:
            return
        count = data.count(soname)
        data = bytearray(bytes(data).replace(soname + b"\x00", patched + b"\x00" * (pad + 1)))
        target = "/tmp/_gmf_libgomp.so.1"
        with open(target, "wb") as f:
            f.write(bytes(data))
        ctypes.CDLL(target, mode=ctypes.RTLD_GLOBAL)
    except Exception:
        pass  # Fall through; LightGBM will raise its own clear error.


_ensure_libgomp()

from src.api.main import app  # noqa: F401,E402
