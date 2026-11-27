
from agents.requirement_reader import RequirementReaderAgent
from agents.test_design_agent import TestDesignAgent
from agents.test_generation_agent import TestGenerationAgent
from agents.test_execution_agent import TestExecutionAgent


class TestAutomationOrchestrator:
    __test__ = False
    """Coordinates all agents in the test automation pipeline."""

    def __init__(self, output_dir: str = "generated_tests"):
        self.requirement_reader = RequirementReaderAgent()
        self.test_design_agent = TestDesignAgent()
        self.test_generation_agent = TestGenerationAgent(
            output_dir=output_dir
        )
        self.test_execution_agent = TestExecutionAgent(
            tests_dir=output_dir
        )

    def run_pipeline(self, requirements_file: str) -> dict:
        # Step 1: Read requirements
        requirements = self.requirement_reader.read_requirements(
            requirements_file
        )

        # Step 2: Generate test scenarios
        scenarios = self.test_design_agent.generate_test_scenarios(
            requirements
        )

        # Step 3: Generate Playwright test files
        generated_files = self.test_generation_agent.generate_tests(
            scenarios
        )

        # Step 4: Execute generated tests
        execution_result = self.test_execution_agent.execute_tests()

        return {
            "requirements_count": len(requirements),
            "scenarios_count": len(scenarios),
            "generated_files": generated_files,
            "execution_result": execution_result,
        }
