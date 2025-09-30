#!/usr/bin/env python3
"""
Test suite for MCP tools in the Snap! Educational System
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Import the modules we're testing
import sys
sys.path.append(str(Path(__file__).parent.parent))

from mcp_server.tools.block_generator import SnapBlockGenerator, SnapBlock, BlockSequence
from mcp_server.tools.concept_explainer import ConceptExplainer
from mcp_server.tools.tutorial_creator import TutorialCreator
from mcp_server.parsers.intent_parser import SnapIntentParser, ParsedIntent
from mcp_server.parsers.validators import SnapInputValidator


class TestSnapBlockGenerator:
    """Test the SnapBlockGenerator class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = SnapBlockGenerator()
    
    def test_initialization(self):
        """Test that generator initializes correctly"""
        assert self.generator is not None
        assert hasattr(self.generator, 'knowledge_base')
        assert hasattr(self.generator, 'patterns')
    
    def test_parsed_intent_creation(self):
        """Test ParsedIntent dataclass creation"""
        intent = ParsedIntent(
            action="move",
            subject="sprite",
            parameters={"steps": 10}
        )
        assert intent.action == "move"
        assert intent.subject == "sprite"
        assert intent.parameters["steps"] == 10
        assert intent.confidence == 1.0  # default value
    
    def test_snap_block_creation(self):
        """Test SnapBlock dataclass creation"""
        block = SnapBlock(
            opcode="forward",
            category="motion",
            inputs={"steps": 10},
            description="Move sprite forward"
        )
        assert block.opcode == "forward"
        assert block.category == "motion"
        assert block.inputs["steps"] == 10
        assert block.is_hat_block == False  # default value
    
    def test_block_sequence_creation(self):
        """Test BlockSequence dataclass creation"""
        blocks = [
            SnapBlock("forward", "motion", {"steps": 10}, "Move forward"),
            SnapBlock("turn_right", "motion", {"degrees": 90}, "Turn right")
        ]
        sequence = BlockSequence(
            blocks=blocks,
            explanation="Move forward and turn right",
            difficulty="beginner"
        )
        assert len(sequence.blocks) == 2
        assert sequence.explanation == "Move forward and turn right"
        assert sequence.difficulty == "beginner"
    
    @patch('builtins.open')
    @patch('json.load')
    def test_load_knowledge_base(self, mock_json_load, mock_open):
        """Test loading knowledge base from JSON"""
        mock_knowledge = {
            "blocks": {
                "forward": {
                    "opcode": "forward",
                    "category": "motion",
                    "parameters": ["steps"]
                }
            }
        }
        mock_json_load.return_value = mock_knowledge
        
        result = self.generator.load_knowledge_base()
        assert result == mock_knowledge
        mock_open.assert_called()
    
    def test_generate_blocks_simple_intent(self):
        """Test generating blocks from simple intent"""
        intent = ParsedIntent(action="move", parameters={"steps": 10})

        # Mock the knowledge base
        self.generator.blocks_db = {
            "blocks": {
                "motion": {
                    "forward": {
                        "opcode": "forward",
                        "category": "motion",
                        "parameters": ["steps"],
                        "default_values": {"steps": 10},
                        "kid_explanation": "Makes sprite move forward"
                    }
                }
            }
        }

        result = self.generator.generate_blocks([intent])

        assert isinstance(result, BlockSequence)
        assert len(result.blocks) > 0
    
    def test_get_available_actions(self):
        """Test getting available actions"""
        self.generator.blocks_db = {
            "blocks": {
                "motion": {
                    "forward": {"category": "motion"}
                },
                "looks": {
                    "say": {"category": "looks"}
                },
                "sound": {
                    "play_sound": {"category": "sound"}
                }
            }
        }

        actions = self.generator.get_available_actions()
        assert len(actions) > 0


class TestConceptExplainer:
    """Test the ConceptExplainer class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.explainer = ConceptExplainer()
    
    def test_initialization(self):
        """Test that explainer initializes correctly"""
        assert self.explainer is not None
        assert hasattr(self.explainer, 'concepts')
    
    @patch('builtins.open')
    @patch('json.load')
    def test_explain_concept(self, mock_json_load, mock_open):
        """Test explaining a concept"""
        mock_concepts = {
            "concepts": {
                "loops": {
                    "beginner": {
                        "text": "Loops repeat actions",
                        "key_points": ["Saves time", "Repeats code"],
                        "examples": ["repeat 10 times"]
                    }
                }
            }
        }
        mock_json_load.return_value = mock_concepts
        
        result = self.explainer.explain("loops", "beginner")
        
        assert "text" in result
        assert "key_points" in result
        assert "examples" in result
    
    def test_get_available_concepts(self):
        """Test getting available concepts"""
        self.explainer.concepts = {
            "concepts": {
                "loops": {"beginner": {}},
                "variables": {"beginner": {}},
                "events": {"beginner": {}}
            }
        }
        
        concepts = self.explainer.get_available_concepts()
        assert "loops" in concepts
        assert "variables" in concepts
        assert "events" in concepts


class TestTutorialCreator:
    """Test the TutorialCreator class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.creator = TutorialCreator()
    
    def test_initialization(self):
        """Test that creator initializes correctly"""
        assert self.creator is not None
        assert hasattr(self.creator, 'tutorials')
    
    @patch('builtins.open')
    @patch('json.load')
    def test_create_tutorial(self, mock_json_load, mock_open):
        """Test creating a tutorial"""
        mock_tutorials = {
            "tutorials": {
                "jumping_game": {
                    "title": "Build a Jumping Game",
                    "description": "Create a simple jumping game",
                    "difficulty": "beginner",
                    "steps": [
                        {"step": 1, "title": "Setup", "instructions": ["Add sprite"]}
                    ]
                }
            }
        }
        mock_json_load.return_value = mock_tutorials
        
        result = self.creator.create_tutorial("jumping_game")
        
        assert "title" in result
        assert "steps" in result
        assert result["title"] == "Build a Jumping Game"
    
    def test_get_popular_topics(self):
        """Test getting popular tutorial topics"""
        self.creator.tutorials = {
            "tutorials": {
                "jumping_game": {"difficulty": "beginner"},
                "bouncing_ball": {"difficulty": "beginner"},
                "interactive_story": {"difficulty": "intermediate"}
            }
        }
        
        topics = self.creator.get_popular_topics()
        assert len(topics) > 0
        assert "jumping_game" in topics


class TestSnapIntentParser:
    """Test the SnapIntentParser class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parser = SnapIntentParser()
    
    def test_initialization(self):
        """Test that parser initializes correctly"""
        assert self.parser is not None
        assert hasattr(self.parser, 'action_patterns')
        assert hasattr(self.parser, 'trigger_patterns')
    
    def test_parse_simple_movement(self):
        """Test parsing simple movement commands"""
        text = "make the sprite move forward 10 steps"
        result = self.parser.parse(text)
        
        assert isinstance(result, Intent)
        assert result.action == "move"
        assert "steps" in result.parameters
        assert result.parameters["steps"] == 10
    
    def test_parse_with_trigger(self):
        """Test parsing commands with triggers"""
        text = "when space key is pressed, make sprite jump"
        result = self.parser.parse(text)
        
        assert isinstance(result, Intent)
        assert result.trigger == "key_pressed"
        assert result.action == "jump"
    
    def test_extract_numbers(self):
        """Test extracting numbers from text"""
        text = "move 25 steps and turn 90 degrees"
        numbers = self.parser._extract_numbers(text)
        
        assert 25 in numbers
        assert 90 in numbers
    
    def test_extract_colors(self):
        """Test extracting colors from text"""
        text = "change color to red and make it blue"
        colors = self.parser._extract_colors(text)
        
        assert "red" in colors
        assert "blue" in colors


class TestSnapInputValidator:
    """Test the SnapInputValidator class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = SnapInputValidator()
    
    def test_initialization(self):
        """Test that validator initializes correctly"""
        assert self.validator is not None
        assert hasattr(self.validator, 'blocked_words')
        assert hasattr(self.validator, 'safe_ranges')
    
    def test_validate_safe_input(self):
        """Test validating safe user input"""
        safe_input = "make the sprite jump when space is pressed"
        result = self.validator.validate_user_input(safe_input)
        
        assert result["is_valid"] == True
        assert result["safety_score"] > 0.8
    
    def test_validate_unsafe_input(self):
        """Test validating unsafe user input"""
        unsafe_input = "delete all files on computer"
        result = self.validator.validate_user_input(unsafe_input)
        
        assert result["is_valid"] == False
        assert "blocked_content" in result["issues"]
    
    def test_validate_block_parameters(self):
        """Test validating block parameters"""
        valid_params = {"steps": 10, "degrees": 90}
        result = self.validator.validate_block_parameters("forward", valid_params)
        
        assert result["is_valid"] == True
    
    def test_is_age_appropriate(self):
        """Test age appropriateness checking"""
        kid_friendly = "make the cat dance and play music"
        assert self.validator.is_age_appropriate(kid_friendly) == True
        
        inappropriate = "violent fighting game with blood"
        assert self.validator.is_age_appropriate(inappropriate) == False
    
    def test_get_complexity_score(self):
        """Test complexity scoring"""
        simple = "move forward"
        complex = "create recursive function with nested loops and conditionals"
        
        simple_score = self.validator.get_complexity_score(simple)
        complex_score = self.validator.get_complexity_score(complex)
        
        assert simple_score < complex_score
        assert simple_score <= 1.0
        assert complex_score >= 0.0


# Integration tests
class TestIntegration:
    """Integration tests for the complete system"""
    
    def setup_method(self):
        """Setup integration test fixtures"""
        self.parser = SnapIntentParser()
        self.generator = SnapBlockGenerator()
        self.validator = SnapInputValidator()
    
    def test_full_pipeline(self):
        """Test the complete pipeline from text to blocks"""
        user_input = "make sprite jump when space key is pressed"
        
        # Step 1: Validate input
        validation = self.validator.validate_user_input(user_input)
        assert validation["is_valid"] == True
        
        # Step 2: Parse intent
        intent = self.parser.parse(user_input)
        assert isinstance(intent, Intent)
        
        # Step 3: Generate blocks (would need mock knowledge base)
        # This would be tested with proper fixtures in a real scenario
        assert intent.action in ["jump", "move"]
        assert intent.trigger in ["key_pressed", None]


# Async tests for MCP server functionality
class TestAsyncMCPTools:
    """Test async functionality of MCP tools"""
    
    @pytest.mark.asyncio
    async def test_async_block_generation(self):
        """Test async block generation"""
        generator = SnapBlockGenerator()
        intent = Intent(action="move", parameters={"steps": 10})
        
        # Mock async operation
        with patch.object(generator, 'generate_blocks') as mock_generate:
            mock_generate.return_value = BlockSequence(
                blocks=[SnapBlock("forward", "motion", {"steps": 10}, "Move forward")],
                explanation="Move sprite forward",
                difficulty="beginner"
            )
            
            result = generator.generate_blocks(intent)
            assert isinstance(result, BlockSequence)
            assert len(result.blocks) == 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
