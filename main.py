
from pathlib import Path

from core.orchestrator import TestAutomationOrchestrator


def main():
    project_root = Path(__file__).resolve().parent

    requirements_file = project_root / "user_stories" / "requirements.xlsx"
    output_dir = project_root / "generated_tests"

    orchestrator = TestAutomationOrchestrator(
        output_dir=str(output_dir)
    )

    result = orchestrator.run_pipeline(str(requirements_file))

    execution = result["execution_result"]

    print("\n========== AUTOMATION PIPELINE ==========")
    print(f"Requirements processed : {result['requirements_count']}")
    print(f"Test scenarios         : {result['scenarios_count']}")
    print(f"Test files generated   : {len(result['generated_files'])}")
    print("-----------------------------------------")
    print(f"Test files discovered  : {execution['total_test_files']}")
    print(f"Execution status       : {'PASSED' if execution['passed'] else 'FAILED'}")
    print("-----------------------------------------")
    print("PYTEST OUTPUT:")
    print(execution["stdout"])

    if execution["stderr"]:
        print("PYTEST ERRORS:")
        print(execution["stderr"])

    print("=========================================")

    if not execution["passed"]:
        raise SystemExit(execution["return_code"])


if __name__ == "__main__":
    main()
