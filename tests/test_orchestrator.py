
from pathlib import Path

from core.orchestrator import TestAutomationOrchestrator


def test_complete_automation_pipeline(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    requirements_file = project_root / "user_stories" / "requirements.xlsx"

    orchestrator = TestAutomationOrchestrator(
        output_dir=str(tmp_path / "generated_tests")
    )

    result = orchestrator.run_pipeline(str(requirements_file))

    # Verify the complete pipeline.
    assert result["requirements_count"] == 3
    assert result["scenarios_count"] == 9
    assert len(result["generated_files"]) == 9

    # Verify all generated files exist.
    for file_path in result["generated_files"]:
        assert file_path.exists()
        assert file_path.suffix == ".py"

    # Verify generated test code is readable.
    first_file = result["generated_files"][0]
    content = first_file.read_text(encoding="utf-8")

    assert "def test_us001_tc001(page: Page):" in content
