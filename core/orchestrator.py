
import json
from datetime import datetime
from pathlib import Path

from agents.requirement_reader import RequirementReaderAgent
from agents.test_design_agent import TestDesignAgent
from agents.test_generation_agent import TestGenerationAgent
from agents.test_execution_agent import TestExecutionAgent

from config.settings import (
    BASE_URL,
    GENERATED_TESTS_DIR,
    REPORTS_DIR,
)


class TestAutomationOrchestrator:
    """Coordinates all agents in the test automation pipeline."""

    __test__ = False

    def __init__(
        self,
        output_dir: str = str(GENERATED_TESTS_DIR),
        base_url: str = BASE_URL,
        reports_dir: str = str(REPORTS_DIR),
    ):
        self.reports_dir = Path(reports_dir)

        self.requirement_reader = RequirementReaderAgent()

        self.test_design_agent = TestDesignAgent()

        self.test_generation_agent = TestGenerationAgent(
            output_dir=output_dir,
            base_url=base_url
        )

        self.test_execution_agent = TestExecutionAgent(
            tests_dir=output_dir
        )

    def run_pipeline(self, requirements_file: str) -> dict:
        # Step 1: Read requirements.
        requirements = self.requirement_reader.read_requirements(
            requirements_file
        )

        # Step 2: Generate AI-powered test scenarios.
        scenarios = self.test_design_agent.generate_test_scenarios(
            requirements
        )

        # Step 3: Generate Playwright test files.
        generated_files = self.test_generation_agent.generate_tests(
            scenarios
        )

        # Step 4: Execute generated tests.
        execution_result = self.test_execution_agent.execute_tests()

        # Step 5: Save execution report.
        report_path = self._save_execution_report(
            requirements,
            scenarios,
            generated_files,
            execution_result
        )

        return {
            "requirements_count": len(requirements),
            "scenarios_count": len(scenarios),
            "generated_files": generated_files,
            "execution_result": execution_result,
            "report_path": report_path,
        }

    def _save_execution_report(
        self,
        requirements: list[dict],
        scenarios: list[dict],
        generated_files: list[Path],
        execution_result: dict,
    ) -> Path:
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().astimezone()

        report = {
            "execution_timestamp": timestamp.isoformat(),
            "status": (
                "PASSED" if execution_result["passed"] else "FAILED"
            ),
            "summary": {
    "requirements_processed": len(requirements),
    "scenarios_generated": len(scenarios),
    "test_files_generated": len(generated_files),
    "test_files_discovered": execution_result["total_test_files"],
    "total_tests": execution_result["total_tests"],
    "passed_tests": execution_result["passed_count"],
    "failed_tests": execution_result["failed_count"],
    "skipped_tests": execution_result["skipped_count"],
    "execution_duration_seconds": execution_result["duration_seconds"],
    "return_code": execution_result["return_code"],
},
            "generated_scenarios": scenarios,
            "generated_test_files": [
                file.name for file in generated_files
            ],
            "execution_output": execution_result["stdout"],
            "execution_errors": execution_result["stderr"],
        }

        report_filename = (
            f"execution_report_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
        )

        report_path = self.reports_dir / report_filename

        report_path.write_text(
            json.dumps(report, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

        return report_path
