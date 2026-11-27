
from core.orchestrator import TestAutomationOrchestrator

from config.settings import (
    REQUIREMENTS_FILE,
    GENERATED_TESTS_DIR,
)


def main():
    orchestrator = TestAutomationOrchestrator(
        output_dir=str(GENERATED_TESTS_DIR)
    )

    result = orchestrator.run_pipeline(str(REQUIREMENTS_FILE))

    execution = result["execution_result"]

    print("\n========== AI AUTOMATION PIPELINE ==========")
    print(f"Requirements processed : {result['requirements_count']}")
    print(f"AI scenarios generated : {result['scenarios_count']}")
    print(f"Test files generated   : {len(result['generated_files'])}")
    print("--------------------------------------------")
    print(f"Test files discovered  : {execution['total_test_files']}")
    print(f"Total tests executed   : {execution['total_tests']}")
    print(f"Tests passed           : {execution['passed_count']}")
    print(f"Tests failed           : {execution['failed_count']}")
    print(f"Tests skipped          : {execution['skipped_count']}")
    print(f"Execution duration     : {execution['duration_seconds']} seconds")
    print("--------------------------------------------")

    status = "PASSED" if execution["passed"] else "FAILED"
    print(f"Execution status       : {status}")
    print(f"JSON report saved      : {result['report_path']}")

    print("--------------------------------------------")
    print("PYTEST OUTPUT:")
    print(execution["stdout"])

    if execution["stderr"]:
        print("PYTEST ERRORS:")
        print(execution["stderr"])

    print("============================================")

    if not execution["passed"]:
        raise SystemExit(execution["return_code"])


if __name__ == "__main__":
    main()
