
import json
import ollama


class OllamaClient:
    """Handles communication with the locally running Ollama model."""

    def __init__(self, model: str = "llama3.2"):
        self.model = model

    def generate_response(self, prompt: str) -> str:
        """Send a prompt to Ollama and return its response."""

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software test engineer. "
                        "Generate accurate, practical software test scenarios. "
                        "Follow the user's requested output format."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return response["message"]["content"]

    def generate_json(self, prompt: str) -> dict:
        """Generate and parse a JSON response from Ollama."""

        response = ollama.chat(
            model=self.model,
            format="json",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software test engineer. "
                        "Return only valid JSON. Do not include Markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return json.loads(response["message"]["content"])
