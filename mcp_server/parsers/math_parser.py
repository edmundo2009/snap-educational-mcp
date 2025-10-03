import re
from typing import Dict, Any, List, Optional, Tuple


class MathPattern:
    """
    A class to encapsulate a math pattern's name and its associated regular expressions.
    This makes the parsing system cleaner and more scalable.
    """

    def __init__(self, name: str, regex_list: List[str]):
        self.name = name
        # Compile all regex strings for better performance
        self.regex_list = [re.compile(r, re.IGNORECASE) for r in regex_list]

    def match(self, text: str) -> Optional[Tuple[str, List[float]]]:
        """
        Tries to match the given text against any of its regular expressions.

        Returns:
            A tuple containing the pattern name and a list of extracted numbers if a match is found.
            Otherwise, returns None.
        """
        for regex in self.regex_list:
            match = regex.search(text)
            if match:
                # Extract all captured numbers from the match groups
                try:
                    numbers = [float(n)
                               for n in match.groups() if n is not None]
                    # A valid pattern should extract at least two numbers
                    if len(numbers) >= 2:
                        return self.name, numbers
                except (ValueError, TypeError):
                    # Ignore matches that don't produce valid numbers
                    continue
        return None


# --- Define the library of all known math patterns ---
PATTERNS_LIBRARY = [
    MathPattern(
        name="unit_rate",
        regex_list=[
            # A more specific and robust pattern for the user's exact problem.
            # "If [num1] hours to [action] [num2] lawns, how many in [num3] hours?"
            r"if\s+(\d+\.?\d*)\s+\w+\s+to\s+\w+\s+(\d+\.?\d*)\s+\w+,\s+how\s+many\s+in\s+(\d+\.?\d*)",
            # A slightly more generic version that is less dependent on specific words.
            r"(\d+\.?\d*)\s+.*?for\s+(\d+\.?\d*)\s+.*?\?\s+.*?(\d+\.?\d*)",
        ]
    ),
    MathPattern(
        name="ratio_equivalent",
        regex_list=[
            # "Ratio [num1]:[num2], scale by [num3]"
            r"ratio\s+(\d+\.?\d*):(\d+\.?\d*),\s+scale\s+by\s+(\d+\.?\d*)"
        ]
    ),
    MathPattern(
        name="simple_division",
        regex_list=[
            # "Divide [num1] cookies among [num2] kids"
            r"divide\s+(\d+\.?\d*)\s+\w+\s+among\s+(\d+\.?\d*)"
        ]
    )
]


def parse_math_problem(text: str) -> Dict[str, Any]:
    """
    Parses a math word problem to identify a known pattern and extract its numbers.

    It iterates through the PATTERNS_LIBRARY and returns the first successful match.
    """
    # Sanitize input text by replacing multiple spaces with a single space
    cleaned_text = re.sub(r'\s+', ' ', text).strip()

    for pattern in PATTERNS_LIBRARY:
        result = pattern.match(cleaned_text)
        if result:
            pattern_name, numbers = result
            print(
                f"✅ Math Parser matched pattern '{pattern_name}' with numbers: {numbers}")
            return {
                "text": text,
                "pattern": pattern_name,
                "numbers": numbers,
            }

    # If no pattern is found after checking all of them
    print(f"❌ Math Parser failed to find a match for: '{text}'")
    return {
        "text": text,
        "pattern": None,
        "numbers": [],
    }
