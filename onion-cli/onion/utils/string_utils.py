import re
from dataclasses import dataclass

irregular_nouns = {
    "man": "men",
    "woman": "women",
    "child": "children",
    "tooth": "teeth",
    "foot": "feet",
    "mouse": "mice",
    "goose": "geese",
    "person": "people",
    "ox": "oxen",
    "louse": "lice",
    # Nouns that don't change in plural (or are the same for singular/plural)
    "sheep": "sheep",
    "fish": "fish",
    "deer": "deer",
    "species": "species",
    "series": "series",
    "moose": "moose",
    "aircraft": "aircraft",
    "hoof": "hooves",  # Can also be 'hoofs'
    "knife": "knives",
    "wife": "wives",
    "leaf": "leaves",
    "wolf": "wolves",
    "life": "lives",
    "self": "selves",
    "calf": "calves",
    "half": "halves",
    "elf": "elves",
    "loaf": "loaves",
    "thief": "thieves",
}

o_exceptions_s = {
    "photo",
    "piano",
    "halo",
    "solo",
    "soprano",
    "cello",
    "rhino",
    "auto",
    "logo",
    "motto",
    "lasso",
    "ego",
}


def singular_to_plural_english(word: str) -> str:
    """
    Converts an English word from singular to plural,
    applying common grammatical rules.

    Args:
        word (str): The word in singular to convert.

    Returns:
        str: The word in plural.
    """
    word = word.lower()

    # 1. Handle common irregular nouns
    if word in irregular_nouns:
        return irregular_nouns[word]

    # 2. Words ending in 's', 'ss', 'sh', 'ch', 'x', or 'z' add 'es'
    # Examples: bus -> buses, class -> classes, brush -> brushes, watch -> watches, fox -> foxes, buzz -> buzzes
    if word.endswith(("s", "ss", "sh", "ch", "x", "z")):
        return word + "es"

    # 3. Words ending in 'y' preceded by a consonant change 'y' to 'ies'
    # Examples: baby -> babies, city -> cities, army -> armies
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"

    # 4. Words ending in 'o' preceded by a consonant add 'es' (some exceptions exist)
    # Examples: potato -> potatoes, tomato -> tomatoes, hero -> heroes
    # Exceptions (add 's'): photo, piano, halo, zero, solo, soprano, cello, rhino, auto, logo, motto, lasso, ego, cello
    # For simplicity, we'll generally add 'es' for 'o' ending, but a more robust solution would list exceptions.
    if word.endswith("o") and len(word) > 1 and word[-2] not in "aeiou":
        # Simple check for common -o exceptions that take 's'
        if word in o_exceptions_s:
            return word + "s"
        return word + "es"

    # 5. Words ending in 'f' or 'fe' often change to 'ves' (handled in irregular, but some general cases)
    # This is partially covered by the 'irregular_nouns' map. For general cases not in map:
    # Example: calf -> calves (already handled), knife -> knives (already handled)
    # If not in irregular_nouns, most default to just adding 's' for 'f' or 'fe' (e.g., belief -> beliefs)
    # A more specific rule for general -f/-fe would be:
    # if word.endswith('f'): return word[:-1] + 'ves' # Not always true (e.g., roof -> roofs)
    # if word.endswith('fe'): return word[:-2] + 'ves' # Not always true (e.g., safe -> safes)
    # Given the complexity and overlap with irregulars, the default 's' is often the safest if not an exception.

    # 6. Default rule: Most other words simply add 's'
    # Examples: cat -> cats, dog -> dogs, table -> tables, book -> books
    return word + "s"


def get_mongo_collection_filename(singular_entity_name: str) -> str:
    if not singular_entity_name or not isinstance(singular_entity_name, str):
        raise ValueError("El nombre de la entidad debe ser una cadena no vacía.")

    plural_lower_name = singular_to_plural_english(singular_entity_name).lower()

    return f"{plural_lower_name}_collection.py"


def normalize_entity_name_to_pascal(raw_name: str) -> str:
    cleaned_name = re.sub(r"[-_ ]+", " ", raw_name).strip()

    pascal_case_name = "".join(word.capitalize() for word in cleaned_name.split())

    return pascal_case_name


@dataclass
class NameVariations:
    Name: str
    Name_plural: str
    single_name: str
    plural_name: str


def get_entity_name_variations(input_name: str) -> NameVariations:
    name = normalize_entity_name_to_pascal(input_name)

    single_name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

    plural_name = singular_to_plural_english(single_name).lower()

    name_plural = normalize_entity_name_to_pascal(plural_name)

    return NameVariations(
        name,
        name_plural,
        single_name,
        plural_name,
    )


def get_datasource_filename(singular_entity_name: str) -> str:
    if not singular_entity_name or not isinstance(singular_entity_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_entity_name)

    return f"{variations.plural_name}_datasource.py"


def get_model_filename(singular_entity_name: str) -> str:
    if not singular_entity_name or not isinstance(singular_entity_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_entity_name)

    return f"{variations.single_name}_model.py"


def get_repository_filename(singular_entity_name: str) -> str:
    if not singular_entity_name or not isinstance(singular_entity_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_entity_name)

    return f"{variations.plural_name}_repository.py"


def is_plural_english(word: str) -> bool:
    """
    Determines if an English word is likely plural.
    This function handles common cases and many irregularities.
    It's not 100% infallible due to the complexity of the English language.

    Args:
        word (str): The word (lowercase) to evaluate.

    Returns:
        bool: True if the word is likely plural, False if it's singular.
    """
    word_lower = word.lower()

    # --- Special cases (same singular and plural forms) ---
    # These words are singular, even if they might end in 's' or are the "plural" form of others.
    # We treat them as singular for this check, even if grammatically they can be both.
    same_singular_plural = {
        "sheep",
        "fish",
        "deer",
        "species",
        "series",
        "moose",
        "aircraft",
        "bison",
        "elk",
        "salmon",
        "trout",
        "bass",
        "gallows",
        "headquarters",
        "means",
        "offspring",
        "shrimp",
        "swine",
        "crossroads",
        "dynamics",
        "innings",
        "politics",
        "statistics",
        "works",
        "hovercraft",
        "spacecraft",
        "barracks",
        "athletics",
        "linguistics",
        "mathematics",
        "physics",
        "news",
        "measles",
        "mumps",
        "diabetes",
        "calculus",
        "circus",
    }
    if word_lower in same_singular_plural:
        return False

    # --- Specific irregular plurals ---
    # Mapping from singular to plural to check if the given word is an irregular plural form.
    irregular_singular_to_plural = {
        "man": "men",
        "woman": "women",
        "child": "children",
        "tooth": "teeth",
        "foot": "feet",
        "mouse": "mice",
        "goose": "geese",
        "person": "people",
        "ox": "oxen",
        "louse": "lice",
        "cactus": "cacti",
        "fungus": "fungi",
        "nucleus": "nuclei",
        "syllabus": "syllabi",
        "alumnus": "alumni",
        "criterion": "criteria",
        "phenomenon": "phenomena",
        "datum": "data",
        "medium": "media",
        "curriculum": "curricula",
        "analysis": "analyses",
        "ellipsis": "ellipses",
        "oasis": "oases",
        "thesis": "theses",
        "crisis": "crises",
        "die": "dice",
        "penny": "pence",
        "hero": "heroes",
        "potato": "potatoes",
        "tomato": "tomatoes",
        "echo": "echoes",
        "veto": "vetoes",
        "torpedo": "torpedoes",
        "calf": "calves",
        "half": "halves",
        "knife": "knives",
        "leaf": "leaves",
        "life": "lives",
        "loaf": "loaves",
        "self": "selves",
        "thief": "thieves",
        "wife": "wives",
        "wolf": "wolves",
    }
    # If the word is a value in our irregular plurals dictionary (an irregular plural form),
    # and it's not also a key (an irregular singular form), then it's plural.
    if (
        word_lower in irregular_singular_to_plural.values()
        and word_lower not in irregular_singular_to_plural.keys()
    ):
        return True

    # --- Common pluralization rules by ending ---

    # Ends with 'ies' (e.g., 'cities', from 'city')
    if (
        word_lower.endswith("ies") and len(word_lower) > 3
    ):  # Ensure it's not a short word like 'ties'
        return True

    # Ends with 'ves' (e.g., 'wolves', from 'wolf')
    if word_lower.endswith("ves") and len(word_lower) > 3:
        return True

    # Ends with 'es'
    if word_lower.endswith("es"):
        stem = word_lower[:-2]
        # Words ending in s, ss, sh, ch, x, z (e.g., passes, dishes, churches, foxes, buzzes)
        if stem.endswith(("s", "ss", "sh", "ch", "x", "z")):
            return True
        # Words ending in 'o' (e.g., potatoes, heroes)
        if (
            stem.endswith("o")
            and len(stem) > 1
            and stem
            not in {
                "photo",
                "piano",
                "halo",
                "solo",
                "soprano",
                "cello",
                "rhino",
                "auto",
                "logo",
                "motto",
                "lasso",
                "ego",
            }
        ):
            return True
        # Exceptions that are singular (e.g., 'yes', 'bus', 'gas', 'lens')
        if word_lower in {"yes", "bus", "gas", "lens"}:
            return False
        # Other 'es' cases implying plural (e.g., passes, foxes)
        return True

    # Ends with 's' (most common rule, but also most ambiguous)
    # Avoid singulars that end in 's' but are singular (e.g., 'bus', 'news')
    if word_lower.endswith("s") and word_lower not in {
        "bus",
        "gas",
        "lens",
        "news",
        "chaos",
    }:
        # This is a heuristic check, may fail with proper nouns or unusual words.
        return True

    # If it doesn't match any plural rule or irregular form, assume it's singular
    return False
