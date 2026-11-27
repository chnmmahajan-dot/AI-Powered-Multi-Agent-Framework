
import json

from agents.ai_test_plan_agent import AITestPlanAgent


def main():
    agent = AITestPlanAgent()

    requirement = {
        "requirement_id": "REQ_LOGIN_001",
        "description": (
            "A user should be able to log in using valid credentials. "
            "After successful login, a welcome message should appear."
        ),
        "application_url": "http://127.0.0.1:8000",
        "test_data": {
            "username": "admin",
            "password": "password123",
        },
    }

    print("\nGenerating a test plan using Llama 3.2...\n")

    try:
        plan = agent.generate_test_plan(requirement)

        print("AI GENERATED A VALID TEST PLAN")
        print("=" * 55)
        print(json.dumps(plan, indent=4, ensure_ascii=False))
        print("=" * 55)
        print(f"Test case: {plan['test_case_id']}")
        print(f"Steps generated: {len(plan['steps'])}")
        print("Schema validation: PASSED")

    except Exception as error:
        print("\nAI TEST PLAN GENERATION FAILED")
        print(f"Reason: {error}")


if __name__ == "__main__":
    main()
