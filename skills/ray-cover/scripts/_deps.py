"""Run a script with the pipeline's own Python environment when the python3 on PATH lacks its packages.

A script calls `_deps.need("mlx_whisper", "PIL")` before importing them. If the current interpreter has them,
nothing happens. If not, and the pipeline venv exists (ray-explainer's check_setup.sh builds it from
requirements.txt), the script is re-run with that venv's python. `optional=True` re-runs when the venv is there and
carries on without the packages when it is not.
2026-11-12: a new Mac came with Homebrew Python 3.15 and none of the packages; qa_tts, host and cap_sheet each
failed in turn. Since then the packages live only in the venv, so a Homebrew Python upgrade cannot drop them.
"""
import importlib.util, os, sys

ENV = os.path.expanduser(os.environ.get("RAY_EXPLAINER_PY", "~/.local/share/ray-explainer/py-env"))


def need(*mods, optional=False):
    missing = [m for m in mods if importlib.util.find_spec(m) is None]
    if not missing: return
    py = os.path.join(ENV, "bin", "python")
    inside = os.path.realpath(sys.prefix) == os.path.realpath(ENV)   # not an env var: child scripts must switch too
    if os.path.exists(py) and not inside:
        flags = ["-I"] if sys.flags.isolated else []
        os.execv(py, [py, *flags, os.path.abspath(sys.argv[0]), *sys.argv[1:]])
    if optional: return
    sys.exit(f"missing Python package(s): {', '.join(missing)} — run ray-explainer/scripts/check_setup.sh "
             f"(it builds {ENV}), or pip install them")
