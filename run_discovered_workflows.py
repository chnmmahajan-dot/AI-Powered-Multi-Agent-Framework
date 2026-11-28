
from playwright.sync_api import sync_playwright

from agents.website_inspection_agent import WebsiteInspectionAgent
from agents.workflow_discovery_agent import WorkflowDiscoveryAgent
from agents.workflow_to_test_plan_agent import WorkflowToTestPlanAgent
from core.browser_executor import BrowserExecutor


def normalize(value):
    """Normalize text to make locator matching easier."""
    return "".join(
        character.lower()
        for character in str(value)
        if character.isalnum()
    )


def get_locator(page, target):
    """Create a Playwright locator from a test-plan target."""

    if not isinstance(target, dict):
        return None

    by = target.get("by")
    value = target.get("value", "")

    if by == "role":
        return page.get_by_role(
            target["role"],
            name=value,
            exact=target.get("exact", False)
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


def find_matching_element(target, elements):
    """Find the discovered website element matching an AI target."""

    requested_value = normalize(target.get("value", ""))

    if not requested_value:
        return None

    for element in elements:
        candidates = [
            element.get("id", ""),
            element.get("name", ""),
            element.get("placeholder", ""),
            element.get("aria_label", ""),
            element.get("text", "")
        ]

        for candidate in candidates:
            candidate_value = normalize(candidate)

            if (
                candidate_value
                and (
                    requested_value == candidate_value
                    or requested_value in candidate_value
                    or candidate_value in requested_value
                )
            ):
                return element

    return None


def ground_ai_locators(test_plan, inspection, page):
    """
    Verify AI locators and replace uncertain ones with
    unique locators based on the website inspection.
    """

    elements = inspection.get("interactive_elements", [])

    print("\nChecking AI-generated locators...")

    for step_number, step in enumerate(
        test_plan["steps"],
        start=1
    ):
        target = step.get("target")

        if not target:
            continue

        # Check whether the original AI locator works.
        locator = get_locator(page, target)

        if locator is not None:
            match_count = locator.count()

            if match_count == 1:
                print(
                    f"LOCATOR VERIFIED at step {step_number}: "
                    f"{target['by']} = {target['value']}"
                )
                continue

            print(
                f"AI locator matched {match_count} elements "
                f"at step {step_number}. Finding a better locator..."
            )

        # Find the corresponding element from website inspection.
        matching_element = find_matching_element(
            target,
            elements
        )

        if not matching_element:
            raise ValueError(
                f"Could not match AI locator "
                f"'{target.get('value')}' at step {step_number} "
                f"to a discovered website element."
            )

        # Prefer element ID because it is generally the most reliable.
        element_id = matching_element.get("id")

        if element_id:
            target["by"] = "css"
            target["value"] = f"#{element_id}"

        elif matching_element.get("placeholder"):
            target["by"] = "placeholder"
            target["value"] = matching_element["placeholder"]

        elif matching_element.get("aria_label"):
            target["by"] = "label"
            target["value"] = matching_element["aria_label"]

        else:
            raise ValueError(
                f"Matched element has no reliable locator "
                f"at step {step_number}."
            )

        # Verify the replacement locator against the loaded page.
        verified_locator = get_locator(page, target)

        if verified_locator is None:
            raise ValueError(
                f"Could not create replacement locator "
                f"at step {step_number}."
            )

        match_count = verified_locator.count()

        if match_count != 1:
            raise ValueError(
                f"Replacement locator '{target['value']}' "
                f"matched {match_count} elements at step "
                f"{step_number}. Expected exactly one."
            )

        print(
            f"LOCATOR GROUNDED at step {step_number}: "
            f"{target['by']} = {target['value']}"
        )

    return test_plan


def print_workflows(workflows):
    """Print the workflows discovered by the AI."""

    print(f"\nValid workflows discovered: {len(workflows)}")

    for workflow in workflows:
        print(
            f"\n{workflow['workflow_id']}: "
            f"{workflow['title']}"
        )

        for number, step in enumerate(
            workflow["steps"],
            start=1
        ):
            print(f"  {number}. {step}")


def execute_workflow(
    browser,
    workflow,
    inspection,
    conversion_agent,
    application_url,
    test_data
):
    """Convert, ground and execute one discovered workflow."""

    workflow_id = workflow["workflow_id"]
    workflow_title = workflow["title"]

    print("\n" + "=" * 60)
    print(f"WORKFLOW: {workflow_id} - {workflow_title}")
    print("=" * 60)

    page = browser.new_page()

    try:
        # Open the website BEFORE locator grounding.
        print("\nOpening application for workflow execution...")

        page.goto(
            application_url,
            wait_until="domcontentloaded"
        )

        print("Application loaded successfully.")

        # Convert the discovered workflow into a test plan.
        print("\nGenerating test plan...")

        test_plan = conversion_agent.generate_test_plan_for_workflow(
            workflow=workflow,
            inspection=inspection,
            test_data=test_data
        )

        print(f"Generated test plan: {test_plan['title']}")
        print(f"Generated steps: {len(test_plan['steps'])}")
        print("Test plan validation: PASSED")

        # Ground all AI-generated locators.
        print("\nSTEP 4: Grounding locators...")

        test_plan = ground_ai_locators(
            test_plan,
            inspection,
            page
        )

        print("Locator grounding: PASSED")

        # Execute the test plan.
        print("\nSTEP 5: Executing workflow...")

        executor = BrowserExecutor(page)

        result = executor.execute_test_plan(test_plan)

        if result.get("status") != "passed":
            raise RuntimeError(
                "Browser executor did not report a passed result."
            )

        print("\nWORKFLOW RESULT: PASSED")

        return {
            "workflow_id": workflow_id,
            "title": workflow_title,
            "status": "passed",
            "result": result
        }

    except Exception as error:
        print(f"\nWORKFLOW FAILED: {error}")

        return {
            "workflow_id": workflow_id,
            "title": workflow_title,
            "status": "failed",
            "error": str(error)
        }

    finally:
        page.close()


def main():
    """Run the complete AI-discovered workflow automation pipeline."""

    application_url = "http://127.0.0.1:8000/"

    test_data = {
        "username": "admin",
        "password": "password123"
    }

    print(
        "\n========== DISCOVERED WORKFLOW AUTOMATION ==========\n"
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)

        try:
            # STEP 1: Inspect the website.
            print("STEP 1: Inspecting the website...")

            inspection_page = browser.new_page()

            try:
                inspection_page.goto(
                    application_url,
                    wait_until="domcontentloaded"
                )

                inspection_agent = WebsiteInspectionAgent(
                    inspection_page
                )

                inspection = inspection_agent.inspect_page()

                print(
                    inspection_agent.format_inspection_for_ai(
                        inspection
                    )
                )

            finally:
                inspection_page.close()

            # STEP 2: Discover workflows.
            print("\nSTEP 2: Discovering user workflows...")

            discovery_agent = WorkflowDiscoveryAgent()

            discovered = discovery_agent.discover_workflows(
                inspection
            )

            workflows = discovered["workflows"]

            for rejected in discovery_agent.rejected_workflows:
                print(
                    f"\nWORKFLOW REJECTED: "
                    f"{rejected['workflow_id']} - "
                    f"{rejected['reason']}"
                )

            print_workflows(workflows)

            if not workflows:
                raise RuntimeError(
                    "No valid workflows were discovered."
                )

            # STEP 3: Prepare workflow conversion.
            print(
                "\nSTEP 3: Converting workflows into test plans..."
            )

            conversion_agent = WorkflowToTestPlanAgent()

            execution_results = []

            # Process each discovered workflow independently.
            for workflow in workflows:
                result = execute_workflow(
                    browser=browser,
                    workflow=workflow,
                    inspection=inspection,
                    conversion_agent=conversion_agent,
                    application_url=application_url,
                    test_data=test_data
                )

                execution_results.append(result)

            # STEP 6: Display final execution summary.
            print(
                "\n\n========== FINAL EXECUTION SUMMARY =========="
            )

            passed = sum(
                1
                for result in execution_results
                if result["status"] == "passed"
            )

            failed = sum(
                1
                for result in execution_results
                if result["status"] == "failed"
            )

            for result in execution_results:
                print(
                    f"\n{result['workflow_id']} - "
                    f"{result['title']}: "
                    f"{result['status'].upper()}"
                )

                if result["status"] == "failed":
                    print(
                        f"Reason: {result.get('error')}"
                    )

            print("\nTotal workflows:", len(execution_results))
            print("Passed:", passed)
            print("Failed:", failed)

            if failed:
                raise RuntimeError(
                    f"{failed} workflow(s) failed."
                )

            print(
                "\nALL VALID DISCOVERED WORKFLOWS PASSED"
            )

        finally:
            browser.close()

    print(
        "\n========== AUTOMATION COMPLETE ==========\n"
    )


if __name__ == "__main__":
    main()
