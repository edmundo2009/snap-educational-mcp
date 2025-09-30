# mcp_server/parsers/validators.py - Input Validation and Safety Checks

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_input: Optional[str] = None


class SnapInputValidator:
    """
    Validates and sanitizes user inputs for Snap! programming.
    
    Ensures inputs are safe, educational, and appropriate for children.
    """

    def __init__(self):
        self.max_input_length = 500
        self.blocked_words = self._load_blocked_words()
        self.safe_patterns = self._build_safe_patterns()

    def _load_blocked_words(self) -> List[str]:
        """Load list of inappropriate words/phrases"""
        # In production, this would load from a file
        return [
            # Placeholder - would contain inappropriate content filters
            "delete", "remove", "destroy", "hack", "break"
        ]

    def _build_safe_patterns(self) -> List[str]:
        """Build patterns for safe, educational content"""
        return [
            r"make.*move", r"when.*pressed", r"jump", r"dance", r"spin",
            r"change.*color", r"play.*sound", r"say", r"hide", r"show",
            r"follow.*mouse", r"bounce", r"grow", r"shrink", r"turn"
        ]

    def validate_user_input(self, text: str) -> ValidationResult:
        """
        Validate user input for safety and appropriateness.
        
        Args:
            text: User input to validate
            
        Returns:
            ValidationResult with validation status and any issues
        """
        errors = []
        warnings = []
        sanitized = text.strip()

        # Check length
        if len(text) > self.max_input_length:
            errors.append(f"Input too long (max {self.max_input_length} characters)")

        # Check for empty input
        if not text.strip():
            errors.append("Input cannot be empty")

        # Check for blocked content
        blocked_found = self._check_blocked_content(text.lower())
        if blocked_found:
            errors.append(f"Inappropriate content detected: {', '.join(blocked_found)}")

        # Check for potentially unsafe patterns
        unsafe_patterns = self._check_unsafe_patterns(text)
        if unsafe_patterns:
            warnings.extend([f"Potentially unsafe: {pattern}" for pattern in unsafe_patterns])

        # Sanitize input
        sanitized = self._sanitize_input(text)

        # Check if input seems educational
        if not self._is_educational_content(text):
            warnings.append("Input doesn't seem to be programming-related")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_input=sanitized
        )

    def _check_blocked_content(self, text: str) -> List[str]:
        """Check for blocked words/phrases"""
        found = []
        for word in self.blocked_words:
            if word in text:
                found.append(word)
        return found

    def _check_unsafe_patterns(self, text: str) -> List[str]:
        """Check for potentially unsafe patterns"""
        unsafe = []
        
        # Check for system-related commands
        system_patterns = [
            r"system", r"file", r"directory", r"folder", r"disk",
            r"network", r"internet", r"download", r"upload"
        ]
        
        for pattern in system_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                unsafe.append(f"System-related term: {pattern}")

        return unsafe

    def _sanitize_input(self, text: str) -> str:
        """Sanitize input by removing/replacing problematic content"""
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters that could be problematic
        sanitized = re.sub(r'[<>{}[\]\\]', '', sanitized)
        
        # Limit to reasonable character set
        sanitized = re.sub(r'[^\w\s.,!?-]', '', sanitized)
        
        return sanitized

    def _is_educational_content(self, text: str) -> bool:
        """Check if content seems educational/programming-related"""
        educational_keywords = [
            "sprite", "move", "jump", "turn", "color", "sound", "when", "if",
            "loop", "repeat", "forever", "click", "press", "key", "mouse",
            "dance", "spin", "bounce", "hide", "show", "say", "play"
        ]
        
        text_lower = text.lower()
        matches = sum(1 for keyword in educational_keywords if keyword in text_lower)
        
        # Consider it educational if it has at least one programming keyword
        return matches > 0

    def validate_block_parameters(self, parameters: Dict[str, Any]) -> ValidationResult:
        """
        Validate block parameters for safety and reasonableness.
        
        Args:
            parameters: Dictionary of block parameters
            
        Returns:
            ValidationResult for the parameters
        """
        errors = []
        warnings = []

        for param_name, param_value in parameters.items():
            param_errors, param_warnings = self._validate_single_parameter(param_name, param_value)
            errors.extend(param_errors)
            warnings.extend(param_warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_single_parameter(self, name: str, value: Any) -> Tuple[List[str], List[str]]:
        """Validate a single parameter"""
        errors = []
        warnings = []

        # Numeric parameter validation
        if isinstance(value, (int, float)):
            if name in ["steps", "distance"]:
                if abs(value) > 1000:
                    warnings.append(f"{name} value {value} is very large")
                if value == 0:
                    warnings.append(f"{name} value is zero - sprite won't move")
            
            elif name in ["degrees", "angle"]:
                if abs(value) > 360:
                    warnings.append(f"{name} value {value} is more than a full rotation")
            
            elif name in ["duration", "time"]:
                if value < 0:
                    errors.append(f"{name} cannot be negative")
                if value > 60:
                    warnings.append(f"{name} value {value} seconds is very long")
            
            elif name in ["size", "scale"]:
                if value <= 0:
                    errors.append(f"{name} must be positive")
                if value > 500:
                    warnings.append(f"{name} value {value}% is very large")

        # String parameter validation
        elif isinstance(value, str):
            if name in ["message", "text"]:
                if len(value) > 100:
                    warnings.append(f"{name} is very long ({len(value)} characters)")
                
                # Check for inappropriate content
                blocked = self._check_blocked_content(value.lower())
                if blocked:
                    errors.append(f"Inappropriate content in {name}: {', '.join(blocked)}")
            
            elif name in ["key"]:
                valid_keys = ["space", "up arrow", "down arrow", "left arrow", "right arrow", 
                             "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
                             "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
                if value.lower() not in valid_keys:
                    warnings.append(f"Unusual key: {value}")

        return errors, warnings

    def suggest_safe_alternatives(self, unsafe_input: str) -> List[str]:
        """Suggest safe alternatives for unsafe input"""
        suggestions = []
        
        # If input contains blocked words, suggest alternatives
        if any(word in unsafe_input.lower() for word in self.blocked_words):
            suggestions.extend([
                "Try describing what you want the sprite to do",
                "Focus on movement, colors, sounds, or animations",
                "Example: 'make sprite jump when space is pressed'"
            ])
        
        # If input is too long, suggest simplification
        if len(unsafe_input) > self.max_input_length:
            suggestions.append("Try breaking your request into smaller parts")
        
        # If input doesn't seem programming-related
        if not self._is_educational_content(unsafe_input):
            suggestions.extend([
                "Try using programming words like: move, jump, turn, color, sound",
                "Example: 'make sprite dance and change colors'",
                "Example: 'when mouse clicked, sprite follows mouse'"
            ])

        return suggestions

    def is_age_appropriate(self, text: str, age_group: str = "elementary") -> bool:
        """
        Check if content is appropriate for the target age group.
        
        Args:
            text: Content to check
            age_group: Target age group (elementary, middle, high)
            
        Returns:
            True if content is age-appropriate
        """
        # For now, just check against blocked words
        # In production, this would be more sophisticated
        blocked = self._check_blocked_content(text.lower())
        return len(blocked) == 0

    def get_complexity_score(self, text: str) -> int:
        """
        Get complexity score (1-10) for the input.
        
        Higher scores indicate more complex programming concepts.
        """
        complexity_indicators = {
            1: ["move", "turn", "say", "color"],
            3: ["when", "if", "repeat", "loop"],
            5: ["variable", "list", "function", "custom"],
            7: ["clone", "broadcast", "sensor"],
            9: ["first-class", "lambda", "recursion"]
        }
        
        max_complexity = 1
        text_lower = text.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                max_complexity = max(max_complexity, level)
        
        return max_complexity
