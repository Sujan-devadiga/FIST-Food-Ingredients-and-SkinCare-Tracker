
import re


def normalize_text(text):
    """Normalize text for ingredient matching."""
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_ingredients(text):
    """Split a label into individual ingredient entries."""
    text = str(text)

    text = re.sub(
        r"(?i)\bingredients?\s*:",
        "",
        text,
    )

    parts = re.split(r"[,;\n]+", text)

    return [
        part.strip(" .:-*")
        for part in parts
        if part.strip(" .:-*")
    ]


def get_status(item):
    """Convert database status into a standard FITS status."""
    status = (
        item.get("status")
        or item.get("severity")
        or ""
    )

    status = str(status).strip().lower()

    if status in {"harmful", "high", "danger", "red"}:
        return "Harmful"

    if status in {
        "caution",
        "moderate",
        "review",
        "use with caution",
        "orange",
    }:
        return "Use with Caution"

    if status in {"safe", "low", "green"}:
        return "Safe"

    return "Not Assessed"


def prepare_database(database):
    """Prepare ingredient names and aliases for matching."""
    prepared_database = []

    for item in database:
        name = str(item.get("ingredient", "")).strip()

        if not name:
            continue

        aliases = item.get("aliases", "")

        if isinstance(aliases, str):
            aliases = [
                alias.strip()
                for alias in re.split(r"[|;]", aliases)
                if alias.strip()
            ]

        elif not isinstance(aliases, list):
            aliases = []

        terms = [name] + aliases

        normalized_terms = []

        for term in terms:
            normalized_term = normalize_text(term)

            if normalized_term:
                normalized_terms.append(normalized_term)

        prepared_database.append({
            "item": item,
            "terms": normalized_terms,
        })

    return prepared_database


def find_ingredient(ingredient, prepared_database):
    """Find an ingredient in the database using names or aliases."""
    normalized_ingredient = normalize_text(ingredient)

    if not normalized_ingredient:
        return None

    # First try an exact match.
    for entry in prepared_database:
        if normalized_ingredient in entry["terms"]:
            return entry["item"]

    # Then try matching a database term within the ingredient text.
    for entry in prepared_database:
        for term in entry["terms"]:
            pattern = r"\b" + re.escape(term) + r"\b"

            if re.search(pattern, normalized_ingredient):
                return entry["item"]

    return None


def analyze_ingredients(text, database):
    """
    Analyze label ingredients against the FITS reference database.

    Recognized ingredients without a database assessment
    remain Not Assessed.
    """

    if not text or not str(text).strip():
        return {
            "total_ingredients": 0,
            "matches": [],
            "ingredients": [],
            "guidance": [],
        }

    ingredient_names = split_ingredients(text)
    prepared_database = prepare_database(database)

    results = []
    matches = []
    guidance = []

    for ingredient in ingredient_names:
        found_item = find_ingredient(
            ingredient,
            prepared_database,
        )

        if found_item:
            status = get_status(found_item)

            reason = str(
                found_item.get("reason") or ""
            ).strip()

            if not reason:
                if status == "Not Assessed":
                    reason = (
                        "This ingredient is recognized in the "
                        "FITS reference catalogue, but it has "
                        "not yet been assessed by this project."
                    )
                else:
                    reason = (
                        "No explanation is currently available "
                        "in the FITS assessment database."
                    )

            result = {
                "ingredient": ingredient,
                "status": status,
                "matched_name": found_item.get(
                    "ingredient",
                    ingredient,
                ),
                "reason": reason,
                "severity": status,
                "diabetes_guidance": str(
                    found_item.get("diabetes_guidance") or ""
                ).strip(),
                "under5_guidance": str(
                    found_item.get("under5_guidance") or ""
                ).strip(),
            }

            if status in {
                "Harmful",
                "Use with Caution",
            }:
                matches.append(result)

            if result["diabetes_guidance"]:
                guidance.append({
                    "ingredient": ingredient,
                    "group": "Diabetes",
                    "message": result["diabetes_guidance"],
                })

            if result["under5_guidance"]:
                guidance.append({
                    "ingredient": ingredient,
                    "group": "Under 5",
                    "message": result["under5_guidance"],
                })

        else:
            result = {
                "ingredient": ingredient,
                "status": "Not Assessed",
                "matched_name": "",
                "reason": (
                    "This ingredient is not currently listed "
                    "in the FITS reference database. Its safety "
                    "has not been assessed by this project."
                ),
                "severity": "Not Assessed",
                "diabetes_guidance": "",
                "under5_guidance": "",
            }

        results.append(result)

    return {
        "total_ingredients": len(results),
        "matches": matches,
        "ingredients": results,
        "guidance": guidance,
    }
