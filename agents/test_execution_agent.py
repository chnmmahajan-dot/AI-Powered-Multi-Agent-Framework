
import subprocess
import sys
from pathlib import Path


class TestExecutionAgent:
    """Executes generated Playwright tests using Pytest."""

    __test__ = False

    def __init__(self, tests_dir: str = "generated_tests"):
        self.tests_dir = Path(tests_dir)

    def execute_tests(self) -> dict:
        if not self.tests_dir.exists():
            raise FileNotFoundError(
                f"Test directory not found: {self.tests_dir}"
            )

        test_files = list(self.tests_dir.glob("test_*.py"))

        if not test_files:
            raise ValueError(
                f"No generated test files found in: {self.tests_dir}"
            )

        command = [
            sys.executable,
            "-m",
            "pytest",
            str(self.tests_dir),
            "-v",
            "--tb=short"
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        return {
            "total_test_files": len(test_files),
            "return_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
