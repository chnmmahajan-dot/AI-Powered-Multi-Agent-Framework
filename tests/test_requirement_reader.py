from pathlib import Path
from agents.requirement_reader import RequirementReaderAgent


def test_read_requirements():
    project_root = Path(__file__).resolve().parents[1]
    file_path = project_root / "user_stories" / "requirements.xlsx"

    agent = RequirementReaderAgent()
    requirements = agent.read_requirements(str(file_path))

    assert len(requirements) == 3
    assert requirements[0]["story_id"] == "US001"
    assert requirements[0]["title"] == "Login"