#!/usr/bin/env python3
"""
Test suite for intent parsing in the Snap! Educational System
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

# Import the modules we're testing
import sys
sys.path.append(str(Path(__file__).parent.parent))

from mcp_server.parsers.intent_parser import SnapIntentParser, ParsedIntent


class TestSnapIntentParser:
    """Comprehensive tests for the SnapIntentParser class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parser = SnapIntentParser()
    
    def test_initialization(self):
        """Test parser initialization"""
        assert self.parser is not None
        assert hasattr(self.parser, 'action_patterns')
        assert hasattr(self.parser, 'trigger_patterns')
        assert hasattr(self.parser, 'parameter_patterns')
        assert len(self.parser.action_patterns) > 0
        assert len(self.parser.trigger_patterns) > 0
    
    # Basic movement parsing tests
    def test_parse_simple_movement(self):
        """Test parsing simple movement commands"""
        test_cases = [
            ("move forward 10 steps", "move", {"steps": 10}),
            ("go right 5 steps", "move", {"steps": 5, "direction": "right"}),
            ("walk backward 15 steps", "move", {"steps": 15, "direction": "backward"}),
            ("move left", "move", {"direction": "left"}),
        ]
        
        for text, expected_action, expected_params in test_cases:
            results = self.parser.parse(text)
            assert len(results) > 0
            result = results[0]  # Take first intent
            assert isinstance(result, ParsedIntent)
            assert result.action == expected_action
            for key, value in expected_params.items():
                assert key in result.parameters
                assert result.parameters[key] == value
    
    def test_parse_rotation(self):
        """Test parsing rotation commands"""
        test_cases = [
            ("turn right 90 degrees", "turn", {"degrees": 90, "direction": "right"}),
            ("rotate left 45 degrees", "turn", {"degrees": 45, "direction": "left"}),
            ("spin around", "turn", {"degrees": 360}),
            ("turn clockwise", "turn", {"direction": "clockwise"}),
        ]
        
        for text, expected_action, expected_params in test_cases:
            results = self.parser.parse(text)
            assert len(results) > 0
            result = results[0]  # Take first intent
            assert result.action == expected_action
            for key, value in expected_params.items():
                assert result.parameters[key] == value
    
    def test_parse_appearance_changes(self):
        """Test parsing appearance change commands"""
        test_cases = [
            ("change color to red", "change_color", {"color": "red"}),
            ("make sprite bigger", "change_size", {"change": "bigger"}),
            ("shrink the sprite", "change_size", {"change": "smaller"}),
            ("hide the sprite", "hide", {}),
            ("show the sprite", "show", {}),
        ]
        
        for text, expected_action, expected_params in test_cases:
            results = self.parser.parse(text)
            assert len(results) > 0
            result = results[0]  # Take first intent
            assert result.action == expected_action
            for key, value in expected_params.items():
                assert result.parameters[key] == value
    
    def test_parse_sound_commands(self):
        """Test parsing sound-related commands"""
        test_cases = [
            ("play sound meow", "play_sound", {"sound": "meow"}),
            ("make a beep sound", "play_sound", {"sound": "beep"}),
            ("say hello", "say", {"text": "hello"}),
            ("say hello for 2 seconds", "say", {"text": "hello", "seconds": 2}),
        ]

        for text, expected_action, expected_params in test_cases:
            results = self.parser.parse(text)
            assert len(results) > 0
            result = results[0]  # Take first intent
            assert result.action == expected_action
            for key, value in expected_params.items():
                assert result.parameters.get(key) == value
    
    # Event trigger parsing tests
    def test_parse_key_triggers(self):
        """Test parsing keyboard event triggers"""
        test_cases = [
            ("when space key is pressed", "key_press", {"key": "space"}),
            ("when up key is pressed", "key_press", {"key": "up"}),
            ("when a key is pressed", "key_press", {"key": "a"}),
            ("press space to jump", "key_press", {"key": "space"}),
        ]

        for text, expected_trigger, expected_params in test_cases:
            results = self.parser.parse(text)
            assert len(results) > 0
            result = results[0]  # Take first intent
            assert result.trigger == expected_trigger
            for key, value in expected_params.items():
                assert result.parameters.get(key) == value
    
    def test_parse_mouse_triggers(self):
        """Test parsing mouse event triggers"""
        test_cases = [
            ("when sprite is clicked", "sprite_click", {}),
            ("when mouse is clicked", "sprite_click", {}),
            ("click on sprite to start", "sprite_click", {}),
        ]

        for text, expected_trigger, expected_params in test_cases:
            results = self.parser.parse(text)
            assert len(results) > 0
            result = results[0]  # Take first intent
            assert result.trigger == expected_trigger
    
    def test_parse_flag_trigger(self):
        """Test parsing green flag trigger"""
        test_cases = [
            ("when green flag is clicked", "flag_clicked", {}),
            ("when flag clicked", "flag_clicked", {}),
            ("start when flag is pressed", "flag_clicked", {}),
        ]
        
        for text, expected_trigger, expected_params in test_cases:
            result = self.parser.parse(text)
            assert result.trigger == expected_trigger
    
    # Complex parsing tests
    def test_parse_compound_commands(self):
        """Test parsing compound commands with multiple actions"""
        text = "when space is pressed, move forward 10 steps and turn right 90 degrees"
        result = self.parser.parse(text)
        
        assert result.trigger == "key_pressed"
        assert result.parameters["key"] == "space"
        # For compound commands, we expect the primary action
        assert result.action in ["move", "compound"]
    
    def test_parse_conditional_commands(self):
        """Test parsing conditional commands"""
        test_cases = [
            ("if touching edge then bounce", "bounce", {"condition": "touching_edge"}),
            ("when touching sprite then change color", "change_color", {"condition": "touching_sprite"}),
        ]
        
        for text, expected_action, expected_params in test_cases:
            result = self.parser.parse(text)
            assert result.action == expected_action
            for key, value in expected_params.items():
                assert result.parameters.get(key) == value
    
    def test_parse_loop_commands(self):
        """Test parsing loop-related commands"""
        test_cases = [
            ("repeat 5 times", "repeat", {"times": 5}),
            ("forever loop", "forever", {}),
            ("do 10 times", "repeat", {"times": 10}),
        ]
        
        for text, expected_action, expected_params in test_cases:
            result = self.parser.parse(text)
            assert result.action == expected_action
            for key, value in expected_params.items():
                assert result.parameters[key] == value
    
    # Parameter extraction tests
    def test_extract_numbers(self):
        """Test number extraction from text"""
        test_cases = [
            ("move 10 steps", [10]),
            ("turn 90 degrees and wait 2 seconds", [90, 2]),
            ("repeat five times", [5]),  # word to number conversion
            ("go twenty-five steps", [25]),
        ]
        
        for text, expected_numbers in test_cases:
            numbers = self.parser._extract_numbers(text)
            for num in expected_numbers:
                assert num in numbers
    
    def test_extract_colors(self):
        """Test color extraction from text"""
        test_cases = [
            ("change to red color", ["red"]),
            ("make it blue and green", ["blue", "green"]),
            ("purple sprite with yellow background", ["purple", "yellow"]),
        ]
        
        for text, expected_colors in test_cases:
            colors = self.parser._extract_colors(text)
            for color in expected_colors:
                assert color in colors
    
    def test_extract_directions(self):
        """Test direction extraction from text"""
        test_cases = [
            ("move left and right", ["left", "right"]),
            ("go up then down", ["up", "down"]),
            ("turn clockwise", ["clockwise"]),
        ]
        
        for text, expected_directions in test_cases:
            directions = self.parser._extract_directions(text)
            for direction in expected_directions:
                assert direction in directions
    
    # Edge cases and error handling
    def test_parse_empty_input(self):
        """Test parsing empty or whitespace input"""
        test_cases = ["", "   ", "\n\t", None]
        
        for text in test_cases:
            if text is None:
                with pytest.raises((TypeError, AttributeError)):
                    self.parser.parse(text)
            else:
                result = self.parser.parse(text)
                assert result.action == "unknown"
    
    def test_parse_nonsensical_input(self):
        """Test parsing nonsensical input"""
        test_cases = [
            "asdfghjkl qwerty",
            "123 456 789",
            "!@#$%^&*()",
        ]
        
        for text in test_cases:
            result = self.parser.parse(text)
            # Should return some result, even if action is "unknown"
            assert isinstance(result, Intent)
    
    def test_parse_very_long_input(self):
        """Test parsing very long input"""
        long_text = "move forward " * 100 + "10 steps"
        result = self.parser.parse(long_text)
        
        assert isinstance(result, Intent)
        assert result.action == "move"
        assert result.parameters["steps"] == 10
    
    # Confidence scoring tests
    def test_confidence_scoring(self):
        """Test confidence scoring for parsed intents"""
        high_confidence_cases = [
            "move forward 10 steps",
            "when space key pressed jump",
            "change color to red",
        ]
        
        low_confidence_cases = [
            "maybe do something",
            "kind of move around",
            "possibly change color",
        ]
        
        for text in high_confidence_cases:
            result = self.parser.parse(text)
            if hasattr(result, 'confidence'):
                assert result.confidence > 0.7
        
        for text in low_confidence_cases:
            result = self.parser.parse(text)
            if hasattr(result, 'confidence'):
                assert result.confidence < 0.5
    
    # Subject identification tests
    def test_subject_identification(self):
        """Test identifying the subject of commands"""
        test_cases = [
            ("make the cat move", "cat"),
            ("sprite should jump", "sprite"),
            ("move the ball forward", "ball"),
            ("make player character run", "player"),
        ]
        
        for text, expected_subject in test_cases:
            result = self.parser.parse(text)
            assert result.subject == expected_subject
    
    # Complexity assessment tests
    def test_complexity_assessment(self):
        """Test complexity level assessment"""
        beginner_cases = [
            "move forward",
            "change color to red",
            "say hello",
        ]
        
        intermediate_cases = [
            "when space pressed, move forward and turn right",
            "repeat 5 times: move and change color",
            "if touching edge then bounce",
        ]
        
        advanced_cases = [
            "create custom block that takes parameters",
            "use first-class functions with map operation",
            "implement recursive algorithm",
        ]
        
        for text in beginner_cases:
            result = self.parser.parse(text)
            assert result.complexity == "beginner"
        
        for text in intermediate_cases:
            result = self.parser.parse(text)
            assert result.complexity in ["intermediate", "beginner"]
        
        for text in advanced_cases:
            result = self.parser.parse(text)
            assert result.complexity in ["advanced", "intermediate"]
    
    # Pattern matching tests
    def test_action_pattern_matching(self):
        """Test action pattern matching"""
        # Test that patterns are properly loaded and matched
        assert len(self.parser.action_patterns) > 0
        
        # Test specific pattern matching
        move_patterns = [p for p in self.parser.action_patterns if "move" in p.lower()]
        assert len(move_patterns) > 0
        
        jump_patterns = [p for p in self.parser.action_patterns if "jump" in p.lower()]
        assert len(jump_patterns) > 0
    
    def test_trigger_pattern_matching(self):
        """Test trigger pattern matching"""
        assert len(self.parser.trigger_patterns) > 0
        
        # Test key press patterns
        key_patterns = [p for p in self.parser.trigger_patterns if "key" in p.lower()]
        assert len(key_patterns) > 0
        
        # Test click patterns
        click_patterns = [p for p in self.parser.trigger_patterns if "click" in p.lower()]
        assert len(click_patterns) > 0


class TestIntentDataclass:
    """Test the Intent dataclass functionality"""
    
    def test_intent_creation(self):
        """Test creating Intent objects"""
        intent = Intent(
            action="move",
            trigger="key_pressed",
            subject="sprite",
            parameters={"steps": 10, "key": "space"},
            complexity="beginner"
        )
        
        assert intent.action == "move"
        assert intent.trigger == "key_pressed"
        assert intent.subject == "sprite"
        assert intent.parameters["steps"] == 10
        assert intent.complexity == "beginner"
    
    def test_intent_defaults(self):
        """Test Intent default values"""
        intent = Intent(action="move")
        
        assert intent.action == "move"
        assert intent.trigger is None
        assert intent.subject == "sprite"
        assert intent.parameters is not None
        assert intent.complexity == "beginner"
    
    def test_intent_serialization(self):
        """Test Intent serialization/deserialization"""
        intent = Intent(
            action="jump",
            parameters={"height": 50}
        )
        
        # Test that we can convert to dict-like structure
        assert hasattr(intent, 'action')
        assert hasattr(intent, 'parameters')
        assert intent.parameters["height"] == 50


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
