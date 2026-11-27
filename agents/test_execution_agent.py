
import re
import subprocess
import sys
import time
from pathlib import Path


class TestExecutionAgent:
    """Executes generated tests and collects reliable execution metrics."""

    __test__ = False

    TEST_STATUSES = (
        "passed",
        "failed",
        "error",
        "skipped",
        "xfailed",
        "xpassed",
    )

    def __init__(self, tests_dir: str = "generated_tests"):
        self.tests_dir = Path(tests_dir)

    def execute_tests(self) -> dict:
        if not self.tests_dir.exists():
            raise FileNotFoundError(
                f"Test directory not found: {self.tests_dir}"
            )

        test_files = sorted(self.tests_dir.glob("test_*.py"))

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
            "--tb=short",
            "--no-header",
        ]

        start_time = time.perf_counter()

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration = round(time.perf_counter() - start_time, 3)

            return {
                "total_test_files": len(test_files),
                "total_tests": 0,
                "passed_count": 0,
                "failed_count": 0,
                "error_count": 1,
                "skipped_count": 0,
                "xfailed_count": 0,
                "xpassed_count": 0,
                "duration_seconds": duration,
                "return_code": 124,
                "passed": False,
                "execution_error": (
                    "Pytest execution exceeded the 300-second timeout."
                ),
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
            }

        duration = round(time.perf_counter() - start_time, 3)

        output = result.stdout + "\n" + result.stderr

        counts = {
            status: 0 for status in self.TEST_STATUSES
        }

        summary_lines = [
            line for line in output.splitlines()
            if line.startswith("=") and " in " in line
        ]

        if summary_lines:
            summary = summary_lines[-1]

            for match in re.finditer(
                r"(\d+)\s+(passed|failed|error|skipped|xfailed|xpassed)",
                summary,
                re.IGNORECASE,
            ):
                count = int(match.group(1))
                status = match.group(2).lower()
                counts[status] = count

        total_tests = sum(counts.values())

        execution_error = None

        if result.returncode != 0 and total_tests == 0:
            execution_error = (
                "Pytest did not complete successfully. "
                "Check the execution output for collection or infrastructure errors."
            )

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
            "execution_error": execution_error,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
