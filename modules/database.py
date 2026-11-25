
import pandas as pd
from pathlib import Path


# Project folders
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# CSV files for each category
DATABASE_FILES = {
    "Food": "harmful_food_ingredients.csv",
    "Skincare": "harmful_skincare_ingredients.csv",
}


def load_database(category):
    """
    Load the selected ingredient database.

    Required CSV column:
        ingredient

    Optional columns:
        aliases, status, reason,
        diabetes_guidance, under5_guidance
    """

    if category not in DATABASE_FILES:
        raise ValueError(f"Unsupported category: {category}")

    file_path = DATA_DIR / DATABASE_FILES[category]

    if not file_path.exists():
        raise FileNotFoundError(
            f"Database file not found: {file_path}"
        )

    df = pd.read_csv(file_path, keep_default_na=False)

    # Normalize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    if "ingredient" not in df.columns:
        raise ValueError(
            f"{file_path.name} must contain an 'ingredient' column."
        )

    # Add optional columns if missing
    optional_columns = [
        "aliases",
        "status",
        "reason",
        "diabetes_guidance",
        "under5_guidance",
    ]

    for column in optional_columns:
        if column not in df.columns:
            df[column] = ""

    database = []

    for _, row in df.iterrows():
        ingredient = str(row["ingredient"]).strip()

        if not ingredient:
            continue

        database.append({
            "ingredient": ingredient,
            "aliases": str(row["aliases"]).strip(),
            "status": str(row["status"]).strip(),
            "reason": str(row["reason"]).strip(),
            "diabetes_guidance": str(
                row["diabetes_guidance"]
            ).strip(),
            "under5_guidance": str(
                row["under5_guidance"]
            ).strip(),
        })

    return database
