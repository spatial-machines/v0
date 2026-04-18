"""Layer 1: Script Interface Tests.

Verify every Python script has a consistent, testable interface:
- Accepts --help (exit code 0)
- Has def main() -> int
- Has raise SystemExit(main()) guard
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from .conftest import SCRIPTS_DIR


def _all_scripts():
    return sorted(SCRIPTS_DIR.glob("*.py"))


@pytest.fixture(params=[p.name for p in _all_scripts()], ids=[p.stem for p in _all_scripts()])
def script_path(request):
    return SCRIPTS_DIR / request.param


def _run_script_help(script_path: Path):
    """Run a script with --help, returning the CompletedProcess.
    Skips the test if the script fails due to missing imports."""
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0 and "ModuleNotFoundError" in result.stderr:
        pytest.skip(f"Missing dependency: {result.stderr.splitlines()[-1]}")
    if result.returncode != 0 and "ImportError" in result.stderr:
        pytest.skip(f"Import error: {result.stderr.splitlines()[-1]}")
    return result


# Scripts that use sys.argv instead of argparse.
_KNOWN_NO_ARGPARSE = {"extract_archive.py"}

# Utility modules without a main() entry point (not standalone scripts).
_UTILITY_MODULES = {
    "format_utils.py",
    "handoff_utils.py",
    "postgis_utils.py",
    "style_utils.py",
    "aprx_scaffold.py",
    "qgis_env.py",
    "renderers.py",
}


class TestAllScriptsHaveHelp:
    """Every script should accept --help and exit 0."""

    def test_help_exits_zero(self, script_path):
        if script_path.name in _KNOWN_NO_ARGPARSE:
            pytest.skip(f"{script_path.name} uses sys.argv, not argparse (known gap)")
        result = _run_script_help(script_path)
        assert result.returncode == 0, (
            f"{script_path.name} --help returned {result.returncode}\n"
            f"stderr: {result.stderr[:500]}"
        )


class TestAllScriptsHaveMainGuard:
    """Every script should have raise SystemExit(main()) in its __main__ guard."""

    def test_has_raise_systemexit_main(self, script_path):
        if script_path.name in _UTILITY_MODULES:
            pytest.skip(f"{script_path.name} is a utility module, not a standalone script")
        source = script_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Find the if __name__ == "__main__" block
        found_guard = False
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Check for if __name__ == "__main__"
                test = node.test
                if (isinstance(test, ast.Compare)
                        and isinstance(test.left, ast.Name)
                        and test.left.id == "__name__"):
                    found_guard = True
                    # Look for raise SystemExit(main()) in the body
                    body_source = ast.get_source_segment(source, node)
                    assert "raise SystemExit(main())" in (body_source or ""), (
                        f"{script_path.name} has __main__ guard but missing "
                        f"'raise SystemExit(main())'"
                    )
                    break

        assert found_guard, f"{script_path.name} has no if __name__ == '__main__' guard"


class TestAllScriptsHaveMainFunction:
    """Every script should define def main() -> int."""

    def test_has_main_with_int_return(self, script_path):
        if script_path.name in _UTILITY_MODULES:
            pytest.skip(f"{script_path.name} is a utility module, not a standalone script")
        source = script_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        main_func = None
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                main_func = node
                break

        assert main_func is not None, f"{script_path.name} has no def main()"

        # Check return annotation is int
        assert main_func.returns is not None, (
            f"{script_path.name}: main() has no return type annotation"
        )
        assert isinstance(main_func.returns, ast.Name) and main_func.returns.id == "int", (
            f"{script_path.name}: main() return type is not 'int'"
        )


class TestRetrievalScriptsAcceptOutputDir:
    """Retrieval scripts should accept --output-dir."""

    @pytest.mark.parametrize("script_name", [
        "retrieve_tiger.py",
        "retrieve_local.py",
        "retrieve_remote.py",
    ])
    def test_output_dir_in_help(self, script_name):
        script = SCRIPTS_DIR / script_name
        result = _run_script_help(script)
        assert "--output-dir" in result.stdout, (
            f"{script_name} does not advertise --output-dir in its help text"
        )
