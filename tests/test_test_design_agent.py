
from pathlib import Path

from agents.requirement_reader import RequirementReaderAgent
from agents.test_design_agent import TestDesignAgent


def test_generate_test_scenarios():
    project_root = Path(__file__).resolve().parents[1]
    requirements_file = project_root / "user_stories" / "requirements.xlsx"

    reader = RequirementReaderAgent()
    requirements = reader.read_requirements(str(requirements_file))

    agent = TestDesignAgent()
    scenarios = agent.generate_test_scenarios(requirements)

    # Three scenarios should be generated for each requirement.
    assert len(scenarios) == len(requirements) * 3

    # Verify the scenario categories.
    scenario_types = {scenario["type"] for scenario in scenarios}
    assert scenario_types == {"Positive", "Negative", "Edge"}

    # Verify the first generated test case.
    assert scenarios[0]["test_case_id"] == "US001_TC001"
    assert scenarios[0]["story_id"] == "US001"
    assert scenarios[0]["type"] == "Positive"
