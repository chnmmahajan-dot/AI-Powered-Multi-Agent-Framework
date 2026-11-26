
class TestDesignAgent:
    """Generates basic test scenarios from software requirements."""

    def generate_test_scenarios(self, requirements: list[dict]) -> list[dict]:
        scenarios = []

        for requirement in requirements:
            story_id = requirement["story_id"]
            title = requirement["title"]
            description = requirement["description"]

            test_templates = [
                {
                    "type": "Positive",
                    "scenario": f"Verify successful {title}",
                    "steps": [
                        f"Open the application.",
                        f"Perform the valid action described in: {description}",
                        "Verify that the operation succeeds."
                    ],
                    "expected_result": (
                        f"The application should successfully complete "
                        f"the {title} operation."
                    )
                },
                {
                    "type": "Negative",
                    "scenario": f"Verify invalid input handling for {title}",
                    "steps": [
                        "Open the application.",
                        "Provide invalid or missing input relevant to the requirement.",
                        "Submit the operation."
                    ],
                    "expected_result": (
                        "The application should reject invalid input "
                        "and display an appropriate error."
                    )
                },
                {
                    "type": "Edge",
                    "scenario": f"Verify boundary conditions for {title}",
                    "steps": [
                        "Open the application.",
                        "Provide empty, minimum, maximum, or boundary values "
                        "where applicable.",
                        "Submit the operation."
                    ],
                    "expected_result": (
                        "The application should handle boundary conditions "
                        "without unexpected errors."
                    )
                }
            ]

            for index, template in enumerate(test_templates, start=1):
                scenarios.append({
                    "test_case_id": f"{story_id}_TC{index:03d}",
                    "story_id": story_id,
                    "requirement_title": title,
                    **template
                })

        return scenarios
