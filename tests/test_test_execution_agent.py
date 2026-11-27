
from agents.test_execution_agent import TestExecutionAgent


def test_execution_agent_runs_pytest(tmp_path):
    test_file = tmp_path / "test_sample.py"

    test_file.write_text(
        "def test_sample():\n"
        "    assert 2 + 2 == 4\n",
        encoding="utf-8"
    )

    agent = TestExecutionAgent(tests_dir=str(tmp_path))
    result = agent.execute_tests()

    assert result["total_test_files"] == 1
    assert result["total_tests"] == 1
    assert result["passed_count"] == 1
    assert result["failed_count"] == 0
    assert result["skipped_count"] == 0
    assert result["duration_seconds"] >= 0
    assert result["return_code"] == 0
    assert result["passed"] is True
    assert "1 passed" in result["stdout"]
