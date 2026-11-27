
from playwright.sync_api import sync_playwright

from agents.ai_test_plan_agent import AITestPlanAgent
from agents.website_inspection_agent import WebsiteInspectionAgent
from core.browser_executor import BrowserExecutor


def normalize(value):
    """Normalize text for comparing AI locators with discovered elements."""
    return "".join(
        character.lower()
        for character in str(value)
        if character.isalnum()
    )


def get_locator(page, target):
    """Build a Playwright locator from an AI-generated target."""

    by = target["by"]
    value = target["value"]

    if by == "role":
        return page.get_by_role(
            target["role"],
            name=value,
        )

    if by == "label":
        return page.get_by_label(value)

    if by == "placeholder":
        return page.get_by_placeholder(value)

    if by == "text":
        return page.get_by_text(value)

    if by == "test_id":
        return page.get_by_test_id(value)

    if by == "css":
        return page.locator(value)

    return None


def ground_ai_locators(test_plan, inspection, page):
    """
    Check AI-generated locators against the actual inspected page.

    If a locator does not exist, find a matching discovered element
    and replace the incorrect locator with a usable one.
    """

    elements = inspection["interactive_elements"]

    for step_number, step in enumerate(
        test_plan["steps"],
        start=1,
    ):
        target = step.get("target")

        if not target:
            continue

        locator = get_locator(page, target)

        if locator is not None and locator.count() > 0:
            continue

        requested_value = normalize(target.get("value", ""))

        matching_element = None

        for element in elements:
            if not element["visible"]:
                continue

            candidates = [
                element.get("id", ""),
                element.get("name", ""),
                element.get("placeholder", ""),
                element.get("aria_label", ""),
                element.get("text", ""),
            ]

            for candidate in candidates:
                candidate_value = normalize(candidate)

                if (
                    requested_value
                    and candidate_value
                    and (
                        requested_value == candidate_value
                        or requested_value in candidate_value
                    )
                ):
                    matching_element = element
                    break

            if matching_element:
                break

        if not matching_element:
            raise ValueError(
                f"Could not find a real website element matching "
                f"AI locator '{target.get('value')}' "
                f"at step {step_number}."
            )

        placeholder = matching_element.get("placeholder")
        element_id = matching_element.get("id")
        aria_label = matching_element.get("aria_label")
        text = matching_element.get("text")

        if placeholder:
            target["by"] = "placeholder"
            target["value"] = placeholder

        elif aria_label:
            target["by"] = "label"
            target["value"] = aria_label

        elif text:
            target["by"] = "text"
            target["value"] = text

        elif element_id:
            target["by"] = "css"
            target["value"] = f"#{element_id}"

        else:
            raise ValueError(
                f"Found a matching element but could not create "
                f"a reliable locator for step {step_number}."
            )

        print(
            f"LOCATOR CORRECTED at step {step_number}: "
            f"{matching_element['tag']} "
            f"-> {target['by']} = {target['value']}"
        )

    return test_plan


def main():
    application_url = "http://127.0.0.1:8000"

    print("\n========== AI TEST AUTOMATION ==========\n")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # STEP 1: Open application.
            print("STEP 1: Opening application...")

            page.goto(
                application_url,
                wait_until="domcontentloaded",
            )

            print(f"Website opened: {page.url}")

            # STEP 2: Inspect website.
            print("\nSTEP 2: Discovering website elements...")

            inspection_agent = WebsiteInspectionAgent(page)
            inspection = inspection_agent.inspect_page()

            inspection_text = (
                inspection_agent.format_inspection_for_ai(
                    inspection
                )
            )

            print(inspection_text)

            # STEP 3: Generate AI test plan.
            print("\nSTEP 3: Generating AI test plan...")

            requirement = {
                "requirement_id": "REQ_LOGIN_001",
                "description": (
                    "Verify that a user can log in with valid "
                    "credentials and see the welcome message."
                ),
                "application_url": application_url,
                "test_data": {
                    "username": "admin",
                    "password": "password123",
                },
                "actual_website_inspection": inspection_text,
                "instructions": (
                    "Use only actual discovered website elements. "
                    "For username and password fields, use their "
                    "exact discovered placeholders. "
                    "Do not invent labels."
                ),
            }

            plan_agent = AITestPlanAgent()
            test_plan = plan_agent.generate_test_plan(requirement)

            print(f"Generated test: {test_plan['title']}")
            print(f"Generated steps: {len(test_plan['steps'])}")
            print("Schema validation: PASSED")

            # STEP 4: Ground AI locators against real elements.
            print("\nSTEP 4: Checking AI-generated locators...")

            test_plan = ground_ai_locators(
                test_plan,
                inspection,
                page,
            )

            print("Locator grounding completed.")

            # STEP 5: Execute the test.
            print("\nSTEP 5: Executing AI-generated test...")

            executor = BrowserExecutor(page)
            result = executor.execute_test_plan(test_plan)

            print("\n========== EXECUTION RESULT ==========")
            print(result)

            if result["status"] != "passed":
                raise RuntimeError("AI-generated test failed.")

            print("\nAI-GENERATED TEST: PASSED")

        except Exception as error:
            print("\nAI TEST AUTOMATION FAILED")
            print(f"Error: {error}")
            raise

        finally:
            browser.close()

    print("\n========== AUTOMATION COMPLETE ==========\n")


if __name__ == "__main__":
    main()
