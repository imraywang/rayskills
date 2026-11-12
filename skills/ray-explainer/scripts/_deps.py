"""Keep the pipeline working when the python3 on PATH loses its packages.

A script calls `_deps.need("mlx_whisper", "PIL")` before importing them. If the current interpreter has them,
nothing happens. If not, and the pipeline venv exists (check_setup.sh builds it from requirements.txt), the script
is re-run with that venv's python. 2026-11-12: a new Mac came with Homebrew Python 3.15 and none of the packages;
qa_tts, host and cap_sheet each failed in turn, and check_setup did not test Pillow at all.
"""
import importlib.util, os, sys

ENV = os.path.expanduser(os.environ.get("RAY_EXPLAINER_PY", "~/.local/share/ray-explainer/py-env"))


def need(*mods):
    missing = [m for m in mods if importlib.util.find_spec(m) is None]
    if not missing: return
    py = os.path.join(ENV, "bin", "python")
    if os.path.exists(py) and not os.environ.get("RAY_EXPLAINER_REEXEC"):
        os.environ["RAY_EXPLAINER_REEXEC"] = "1"
        os.execv(py, [py, os.path.abspath(sys.argv[0]), *sys.argv[1:]])
    sys.exit(f"missing Python package(s): {', '.join(missing)} — run scripts/check_setup.sh (it builds {ENV})")
