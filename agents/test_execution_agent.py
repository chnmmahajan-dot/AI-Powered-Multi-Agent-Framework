
import re
import subprocess
import sys
import time
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

        start_time = time.perf_counter()

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        duration = round(time.perf_counter() - start_time, 3)

        output = result.stdout + "\n" + result.stderr

        # Extract test counts from the pytest summary.
        counts = {
            "passed": 0,
            "failed": 0,
            "error": 0,
            "skipped": 0,
            "xfailed": 0,
            "xpassed": 0,
        }

        for match in re.finditer(
            r"(\d+)\s+(passed|failed|error|skipped|xfailed|xpassed)",
            output,
            re.IGNORECASE
        ):
            count = int(match.group(1))
            status = match.group(2).lower()
            counts[status] += count

        total_tests = sum(counts.values())

        return {
            "total_test_files": len(test_files),
            "total_tests": total_tests,
            "passed_count": counts["passed"],
            "failed_count": counts["failed"] + counts["error"],
            "error_count": counts["error"],
            "skipped_count": counts["skipped"],
            "xfailed_count": counts["xfailed"],
            "xpassed_count": counts["xpassed"],
            "duration_seconds": duration,
            "return_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
