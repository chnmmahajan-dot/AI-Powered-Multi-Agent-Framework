
from pathlib import Path
import pandas as pd


class RequirementReaderAgent:
    """Reads and validates user stories from Excel or CSV files."""

    REQUIRED_COLUMNS = ["story_id", "title", "description"]

    def read_requirements(self, file_path: str) -> list[dict]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Requirements file not found: {path}")

        if path.suffix.lower() == ".xlsx":
            dataframe = pd.read_excel(path)
        elif path.suffix.lower() == ".csv":
            dataframe = pd.read_csv(path)
        else:
            raise ValueError("Only Excel (.xlsx) and CSV (.csv) files are supported.")

        dataframe.columns = [
            str(column).strip().lower() for column in dataframe.columns
        ]

        missing_columns = [
            column for column in self.REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}"
            )

        dataframe = dataframe.fillna("")

        requirements = dataframe.to_dict(orient="records")

        return [
            requirement
            for requirement in requirements
            if all(str(requirement[column]).strip()
                   for column in self.REQUIRED_COLUMNS)
        ]
