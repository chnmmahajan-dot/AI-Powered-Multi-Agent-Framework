
class WebsiteInspectionAgent:
    """Inspects a webpage and discovers its interactive elements."""

    def __init__(self, page):
        self.page = page

    def inspect_page(self) -> dict:
        """Discover interactive elements and basic page information."""

        elements = self.page.locator(
            "input, button, a, select, textarea, [role]"
        ).evaluate_all(
            """elements => elements.map(element => ({
                tag: element.tagName.toLowerCase(),
                id: element.id || "",
                type: element.getAttribute("type") || "",
                name: element.getAttribute("name") || "",
                placeholder: element.getAttribute("placeholder") || "",
                aria_label: element.getAttribute("aria-label") || "",
                role: element.getAttribute("role") || "",
                text: (element.innerText || element.value || "")
                    .trim()
                    .slice(0, 200),
                href: element.getAttribute("href") || "",
                visible: !!(
                    element.offsetWidth ||
                    element.offsetHeight ||
                    element.getClientRects().length
                )
            }))"""
        )

        headings = self.page.locator(
            "h1, h2, h3"
        ).evaluate_all(
            """elements => elements.map(element => ({
                tag: element.tagName.toLowerCase(),
                text: element.innerText.trim()
            }))"""
        )

        return {
            "url": self.page.url,
            "title": self.page.title(),
            "headings": headings,
            "interactive_elements": elements,
            "element_count": len(elements),
        }

    def format_inspection_for_ai(self, inspection: dict) -> str:
        """Convert discovered webpage information into readable text."""

        lines = [
            f"Website URL: {inspection['url']}",
            f"Website title: {inspection['title']}",
            "",
            "PAGE HEADINGS:",
        ]

        for heading in inspection["headings"]:
            lines.append(
                f"- {heading['tag']}: {heading['text']}"
            )

        lines.extend([
            "",
            "INTERACTIVE ELEMENTS:",
        ])

        for index, element in enumerate(
            inspection["interactive_elements"],
            start=1,
        ):
            details = [
                f"Element {index}",
                f"tag={element['tag']}",
            ]

            for field in (
                "id",
                "type",
                "name",
                "placeholder",
                "aria_label",
                "role",
                "text",
            ):
                if element[field]:
                    details.append(f"{field}={element[field]}")

            lines.append("- " + ", ".join(details))

        return "\n".join(lines)
