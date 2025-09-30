
# mcp_server/parsers/intent_parser.py - Lightweight Pattern Matching

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ParsedIntent:
    """Structured intent representation"""
    action: str                          # "move", "jump", "turn", etc.
    trigger: Optional[str] = None        # "key_press", "flag_click", etc.
    subject: str = "sprite"              # What performs the action
    parameters: Dict[str, Any] = field(default_factory=dict)
    # "forever", "repeat", etc.
    modifiers: List[str] = field(default_factory=list)
    confidence: float = 1.0
    raw_text: str = ""


class SnapIntentParser:
    """
    LIGHTWEIGHT intent parser using pattern matching.
    
    Philosophy:
    - Claude/LLM does the heavy NLP lifting
    - This parser handles structured extraction from well-formed descriptions
    - Focuses on Snap! programming domain knowledge
    - No external NLP libraries needed
    """

    def __init__(self):
        # Domain-specific patterns (Snap! programming vocabulary)
        self.patterns = self._load_patterns()

    def _load_patterns(self) -> Dict[str, Any]:
        """
        Load Snap! programming patterns.
        These are domain-specific, not general-purpose NLP.
        """
        return {
            # ACTION PATTERNS - What should happen
            "actions": {
                # Motion
                "move": [r"move|walk|go|step|advance"],
                "turn": [r"turn|rotate|spin|twist|pivot"],
                "jump": [r"jump|hop|leap|bounce"],
                "glide": [r"glide|slide|float"],
                "goto": [r"go to|goto|teleport|warp"],

                # Looks
                "say": [r"say|speak|talk|announce"],
                "think": [r"think|ponder|wonder"],
                "change_costume": [r"costume|outfit|look|appearance"],
                "change_size": [r"size|grow|shrink|scale"],
                "show": [r"show|appear|visible"],
                "hide": [r"hide|disappear|invisible"],

                # Sound
                "play_sound": [r"play sound|sound|beep|noise"],
                "change_volume": [r"volume|loud|quiet"],

                # Control
                "wait": [r"wait|pause|delay"],
                "repeat": [r"repeat|loop"],
                "forever": [r"forever|always|continuously"],

                # Sensing
                "follow": [r"follow|chase|track"],
                "detect": [r"detect|sense|check"]
            },

            # TRIGGER PATTERNS - When should it happen
            "triggers": {
                "flag_click": [
                    r"when (?:green )?flag (?:is )?clicked",
                    r"when (?:program )?starts?",
                    r"at (?:the )?start"
                ],
                "key_press": [
                    r"when (?:the )?(\w+)(?: key)? (?:is )?pressed",
                    r"(?:on )?press(?:ing)? (?:the )?(\w+)(?: key)?",
                    r"(?:when )?(\w+) key"
                ],
                "sprite_click": [
                    r"when (?:this )?sprite (?:is )?clicked",
                    r"(?:on )?click(?:ing)? (?:the )?sprite"
                ],
                "forever": [
                    r"forever",
                    r"continuously",
                    r"always"
                ]
            },

            # PARAMETER PATTERNS - Extract values
            "parameters": {
                "number": r"(-?\d+(?:\.\d+)?)",
                "direction": r"(left|right|up|down|forward|backward|north|south|east|west)",
                "color": r"(red|blue|green|yellow|orange|purple|pink|black|white|brown|gray)",
                "key": r"(space|enter|up arrow|down arrow|left arrow|right arrow|[a-z])",
                "steps": r"(\d+)\s*steps?",
                "degrees": r"(\d+)\s*degrees?",
                "seconds": r"(\d+(?:\.\d+)?)\s*(?:second|sec)s?",
                "times": r"(\d+)\s*times?"
            },

            # MODIFIER PATTERNS - How should it happen
            "modifiers": {
                "forever": [r"forever", r"continuously", r"always"],
                "repeat": [r"repeat", r"loop"],
                "until": [r"until", r"till"],
                "fast": [r"fast|quick(?:ly)?|rapid(?:ly)?"],
                "slow": [r"slow(?:ly)?|gradual(?:ly)?"]
            }
        }

    def parse(self, text: str) -> List[ParsedIntent]:
        """
        Parse structured description into intents.
        
        Expected input format (from Claude):
        - "when space key pressed, move sprite up 50 pixels"
        - "make sprite turn right 90 degrees forever"
        - "play sound pop and say hello"
        
        Returns list of intents (one per action)
        """
        text = text.lower().strip()

        # Split compound sentences
        sentences = self._split_sentences(text)

        intents = []
        for sentence in sentences:
            intent = self._parse_sentence(sentence)
            if intent:
                intents.append(intent)

        return intents

    def _split_sentences(self, text: str) -> List[str]:
        """Split on common conjunctions"""
        # Split on: "and", "then", comma+and, semicolon
        parts = re.split(
            r'\s+(?:and|then)\s+|\s*,\s*(?:and\s+)?|\s*;\s*', text)
        return [p.strip() for p in parts if p.strip()]

    def _parse_sentence(self, text: str) -> Optional[ParsedIntent]:
        """Parse single sentence into intent"""

        # Extract components
        trigger = self._extract_trigger(text)
        action = self._extract_action(text)
        subject = self._extract_subject(text)
        parameters = self._extract_parameters(text)
        modifiers = self._extract_modifiers(text)

        if not action:
            # No clear action found
            return None

        return ParsedIntent(
            action=action,
            trigger=trigger,
            subject=subject,
            parameters=parameters,
            modifiers=modifiers,
            confidence=self._calculate_confidence(action, trigger, parameters),
            raw_text=text
        )

    def _extract_trigger(self, text: str) -> Optional[str]:
        """Extract event trigger"""
        for trigger_type, patterns in self.patterns["triggers"].items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Store key if it's a key press
                    if trigger_type == "key_press" and match.groups():
                        # This will be added to parameters
                        return trigger_type
                    return trigger_type
        return None

    def _extract_action(self, text: str) -> Optional[str]:
        """Extract primary action"""
        for action_type, patterns in self.patterns["actions"].items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return action_type
        return None

    def _extract_subject(self, text: str) -> str:
        """Extract subject (sprite, stage, etc.)"""
        if re.search(r"sprite|character|player", text, re.IGNORECASE):
            return "sprite"
        elif re.search(r"stage|background|backdrop", text, re.IGNORECASE):
            return "stage"
        return "sprite"  # Default

    def _extract_parameters(self, text: str) -> Dict[str, Any]:
        """Extract numerical and named parameters"""
        params = {}

        for param_type, pattern in self.patterns["parameters"].items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if param_type == "number":
                    # Convert to numeric
                    params[param_type] = [
                        float(m) if '.' in m else int(m) for m in matches]
                elif param_type in ["steps", "degrees", "seconds", "times"]:
                    # Extract numeric value
                    params[param_type] = int(matches[0]) if matches else None
                else:
                    # Store string value
                    params[param_type] = matches[0] if len(
                        matches) == 1 else matches

        # Special handling for key presses
        key_match = re.search(
            r"(?:when |press )?(\w+)(?: key)?", text, re.IGNORECASE)
        if key_match and key_match.group(1) in ["space", "enter", "up", "down", "left", "right"]:
            params["key"] = key_match.group(1)

        return params

    def _extract_modifiers(self, text: str) -> List[str]:
        """Extract modifiers (forever, repeat, etc.)"""
        modifiers = []
        for modifier_type, patterns in self.patterns["modifiers"].items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    modifiers.append(modifier_type)
                    break
        return modifiers

    def _calculate_confidence(self, action: str, trigger: Optional[str], params: Dict) -> float:
        """Simple confidence score"""
        score = 0.5  # Base score

        if action:
            score += 0.3  # Have clear action
        if trigger:
            score += 0.1  # Have trigger
        if params:
            score += 0.1  # Have parameters

        return min(score, 1.0)

    def validate_intent(self, intent: ParsedIntent) -> Tuple[bool, Optional[str]]:
        """
        Validate that intent can be converted to Snap! blocks.
        Returns (is_valid, error_message)
        """
        # Check if action is supported
        if intent.action not in self.patterns["actions"]:
            return False, f"Unknown action: {intent.action}"

        # Check if trigger is supported (if present)
        if intent.trigger and intent.trigger not in self.patterns["triggers"]:
            return False, f"Unknown trigger: {intent.trigger}"

        # Action-specific validation
        if intent.action == "move" and "steps" not in intent.parameters and "direction" not in intent.parameters:
            return False, "Move action needs steps or direction"

        if intent.action == "turn" and "degrees" not in intent.parameters:
            return False, "Turn action needs degrees"

        return True, None


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_usage():
    """Show how the lightweight parser works"""
    parser = SnapIntentParser()

    test_cases = [
        # Simple cases (what Claude would send)
        "when space key pressed, move sprite up 50 steps",
        "turn right 90 degrees",
        "play sound pop and say hello",
        "repeat 10 times, move forward 5 steps",

        # Complex cases
        "when flag clicked, forever move right 10 steps and if on edge bounce",
        "make sprite follow mouse pointer",
        "change costume to costume2 and wait 1 second"
    ]

    for test in test_cases:
        print(f"\n📝 Input: {test}")
        intents = parser.parse(test)

        for i, intent in enumerate(intents, 1):
            print(f"   Intent {i}:")
            print(f"   - Action: {intent.action}")
            print(f"   - Trigger: {intent.trigger}")
            print(f"   - Parameters: {intent.parameters}")
            print(f"   - Modifiers: {intent.modifiers}")
            print(f"   - Confidence: {intent.confidence:.2f}")

            is_valid, error = parser.validate_intent(intent)
            if not is_valid:
                print(f"   ⚠️  Validation error: {error}")


if __name__ == "__main__":
    example_usage()
