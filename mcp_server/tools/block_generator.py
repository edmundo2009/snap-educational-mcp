# mcp_server/tools/block_generator.py - Snap! Block Generation Engine

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Import the updated ParsedIntent from the parser
from ..parsers.intent_parser import ParsedIntent


class BlockCategory(Enum):
    MOTION = "motion"
    LOOKS = "looks"
    SOUND = "sound"
    EVENTS = "events"
    CONTROL = "control"
    SENSING = "sensing"
    OPERATORS = "operators"
    VARIABLES = "variables"
    CUSTOM = "custom"


@dataclass
class SnapBlock:
    """Represents a single Snap! block"""
    opcode: str
    category: BlockCategory
    inputs: Dict[str, Any]
    description: str
    position: Optional[Dict[str, int]] = None
    next_block: Optional[str] = None
    is_hat_block: bool = False


@dataclass
class BlockSequence:
    """Represents a sequence of blocks that form a complete script"""
    blocks: List[SnapBlock]
    explanation: str
    difficulty: str
    estimated_time: int = 0  # milliseconds


class SnapBlockGenerator:
    """
    Core engine for converting natural language intents into Snap! block sequences.
    
    Uses knowledge base of block definitions and common patterns to generate
    educationally appropriate block sequences.
    """

    def __init__(self, knowledge_path: str = "knowledge/snap_blocks.json", 
                 patterns_path: str = "knowledge/patterns.json"):
        self.knowledge_path = knowledge_path
        self.patterns_path = patterns_path
        self.blocks_db = {}
        self.patterns_db = {}
        self.load_knowledge_base()

    def load_knowledge_base(self):
        """Load block definitions and patterns from JSON files"""
        try:
            # Load block definitions
            if os.path.exists(self.knowledge_path):
                with open(self.knowledge_path, 'r') as f:
                    self.blocks_db = json.load(f)
                print(f"✓ Loaded {len(self.blocks_db.get('blocks', {}))} block definitions")
            else:
                print(f"⚠ Knowledge file not found: {self.knowledge_path}")
                self.blocks_db = self._create_default_blocks()

            # Load patterns
            if os.path.exists(self.patterns_path):
                with open(self.patterns_path, 'r') as f:
                    self.patterns_db = json.load(f)
                print(f"✓ Loaded {len(self.patterns_db.get('patterns', {}))} patterns")
            else:
                print(f"⚠ Patterns file not found: {self.patterns_path}")
                self.patterns_db = self._create_default_patterns()

        except Exception as e:
            print(f"✗ Error loading knowledge base: {e}")
            self.blocks_db = self._create_default_blocks()
            self.patterns_db = self._create_default_patterns()

    def _create_default_blocks(self) -> Dict[str, Any]:
        """Create minimal default block definitions"""
        return {
            "blocks": {
                "motion": {
                    "forward": {
                        "opcode": "forward",
                        "category": "motion",
                        "parameters": ["steps"],
                        "default_values": {"steps": 10},
                        "kid_explanation": "Makes sprite move forward!"
                    },
                    "changeYBy": {
                        "opcode": "changeYBy",
                        "category": "motion", 
                        "parameters": ["dy"],
                        "default_values": {"dy": 10},
                        "kid_explanation": "Moves sprite up or down!"
                    }
                },
                "events": {
                    "receiveKey": {
                        "opcode": "receiveKey",
                        "category": "events",
                        "parameters": ["key"],
                        "default_values": {"key": "space"},
                        "kid_explanation": "Starts when key is pressed!",
                        "is_hat_block": True
                    }
                },
                "control": {
                    "doWait": {
                        "opcode": "doWait",
                        "category": "control",
                        "parameters": ["duration"],
                        "default_values": {"duration": 1},
                        "kid_explanation": "Waits for some time!"
                    }
                }
            }
        }

    def _create_default_patterns(self) -> Dict[str, Any]:
        """Create minimal default patterns"""
        return {
            "patterns": {
                "jump": {
                    "blocks": [
                        {"opcode": "changeYBy", "inputs": {"DY": 50}},
                        {"opcode": "doWait", "inputs": {"DURATION": 0.3}},
                        {"opcode": "changeYBy", "inputs": {"DY": -50}}
                    ],
                    "explanation": "Makes sprite jump up and come back down!",
                    "difficulty": "beginner",
                    "triggers": ["jump", "hop", "bounce up"]
                },
                "move_right": {
                    "blocks": [
                        {"opcode": "changeXBy", "inputs": {"DX": 10}}
                    ],
                    "explanation": "Moves sprite to the right!",
                    "difficulty": "beginner",
                    "triggers": ["move right", "go right", "right"]
                }
            }
        }

    def generate_blocks(self, intents: List[ParsedIntent], complexity: str = "beginner") -> BlockSequence:
        """
        Generate a sequence of Snap! blocks from parsed intents.

        Args:
            intents: List of parsed user intents
            complexity: Difficulty level for educational appropriateness

        Returns:
            BlockSequence with blocks and educational explanation
        """
        if not intents:
            return BlockSequence([], "No actions to create", complexity)

        all_blocks = []
        explanations = []

        for intent in intents:
            blocks = self._generate_blocks_for_intent(intent, complexity)
            all_blocks.extend(blocks)
            explanations.append(self._get_explanation_for_intent(intent))

        # Connect blocks in sequence
        for i in range(len(all_blocks) - 1):
            all_blocks[i].next_block = f"block_{i+2:03d}"

        explanation = " ".join(explanations)

        return BlockSequence(
            blocks=all_blocks,
            explanation=explanation,
            difficulty=complexity,
            estimated_time=len(all_blocks) * 100
        )

    def _generate_blocks_for_intent(self, intent: ParsedIntent, complexity: str) -> List[SnapBlock]:
        """Generate blocks for a single intent"""
        blocks = []

        # CRITICAL: If intent has a trigger, create the appropriate hat block first
        if intent.trigger:
            hat_block = self._create_hat_block_for_trigger(intent.trigger, intent.parameters)
            if hat_block:
                blocks.append(hat_block)

        # Check if this matches a known pattern
        pattern = self._find_matching_pattern(intent.action)
        if pattern:
            action_blocks = self._create_blocks_from_pattern(pattern, intent)
            blocks.extend(action_blocks)
            return blocks

        # Try to create individual block
        block_def = self._find_block_definition(intent.action)
        if block_def:
            action_blocks = [self._create_block_from_definition(block_def, intent)]
            blocks.extend(action_blocks)
            return blocks

        # Fallback: create a simple say block
        fallback_block = SnapBlock(
            opcode="doSay",
            category=BlockCategory.LOOKS,
            inputs={"MESSAGE": f"I want to {intent.action}"},
            description=f"Says '{intent.action}'"
        )
        blocks.append(fallback_block)

        return blocks

    def _create_hat_block_for_trigger(self, trigger: str, parameters: Dict[str, Any]) -> Optional[SnapBlock]:
        """Create the appropriate hat block for a trigger"""
        trigger_lower = trigger.lower()

        # Map triggers to Snap! hat blocks
        if "key_press" in trigger_lower or "key" in trigger_lower:
            key = parameters.get("key", "space")
            return SnapBlock(
                opcode="receiveKey",
                category=BlockCategory.EVENTS,
                inputs={"KEY_OPTION": key},
                description=f"When {key} key pressed",
                is_hat_block=True
            )

        elif "sprite_click" in trigger_lower or "clicked" in trigger_lower:
            return SnapBlock(
                opcode="receiveClick",
                category=BlockCategory.EVENTS,
                inputs={},
                description="When this sprite clicked",
                is_hat_block=True
            )

        elif "flag_click" in trigger_lower or "flag" in trigger_lower:
            return SnapBlock(
                opcode="receiveGo",
                category=BlockCategory.EVENTS,
                inputs={},
                description="When green flag clicked",
                is_hat_block=True
            )

        elif "broadcast" in trigger_lower:
            message = parameters.get("message", "message1")
            return SnapBlock(
                opcode="receiveMessage",
                category=BlockCategory.EVENTS,
                inputs={"MSG": message},
                description=f"When I receive {message}",
                is_hat_block=True
            )

        # Default: green flag for unknown triggers
        return SnapBlock(
            opcode="receiveGo",
            category=BlockCategory.EVENTS,
            inputs={},
            description="When green flag clicked",
            is_hat_block=True
        )

    def _find_matching_pattern(self, action: str) -> Optional[Dict[str, Any]]:
        """Find a pattern that matches the action"""
        action_lower = action.lower()
        
        for pattern_name, pattern_data in self.patterns_db.get("patterns", {}).items():
            triggers = pattern_data.get("triggers", [pattern_name])
            if any(trigger in action_lower for trigger in triggers):
                return pattern_data
        
        return None

    def _create_blocks_from_pattern(self, pattern: Dict[str, Any], intent: ParsedIntent) -> List[SnapBlock]:
        """Create blocks from a pattern definition"""
        blocks = []

        for i, block_spec in enumerate(pattern.get("blocks", [])):
            block = SnapBlock(
                opcode=block_spec["opcode"],
                category=BlockCategory(block_spec.get("category", "motion")),
                inputs=block_spec.get("inputs", {}),
                description=f"Pattern block {i+1}"
            )
            blocks.append(block)

        return blocks

    def _find_block_definition(self, action: str) -> Optional[Dict[str, Any]]:
        """Find a block definition that matches the action"""
        action_lower = action.lower()

        for category, blocks in self.blocks_db.get("blocks", {}).items():
            for block_name, block_def in blocks.items():
                if block_name in action_lower or action_lower in block_name:
                    return block_def

        return None

    def _create_block_from_definition(self, block_def: Dict[str, Any], intent: ParsedIntent) -> SnapBlock:
        """Create a block from a definition"""
        inputs = {}

        # Apply default values and extract from intent parameters
        for param, default_val in block_def.get("default_values", {}).items():
            # Check various parameter formats from the new parser
            param_value = default_val
            if param in intent.parameters:
                param_value = intent.parameters[param]
            elif param.lower() in intent.parameters:
                param_value = intent.parameters[param.lower()]

            inputs[param.upper()] = param_value

        return SnapBlock(
            opcode=block_def["opcode"],
            category=BlockCategory(block_def["category"]),
            inputs=inputs,
            description=block_def.get("kid_explanation", "A Snap! block"),
            is_hat_block=block_def.get("is_hat_block", False)
        )

    def _get_explanation_for_intent(self, intent: ParsedIntent) -> str:
        """Generate kid-friendly explanation for an intent"""
        if intent.trigger:
            return f"When {intent.trigger}, the {intent.subject} will {intent.action}!"
        else:
            return f"The {intent.subject} will {intent.action}!"

    def format_for_snap(self, block_sequence: BlockSequence, target_sprite: str = "Sprite") -> Dict[str, Any]:
        """
        Format block sequence for Snap! bridge communication.
        
        Args:
            block_sequence: Generated block sequence
            target_sprite: Target sprite name
            
        Returns:
            Dictionary formatted for WebSocket communication
        """
        formatted_blocks = []
        
        for i, block in enumerate(block_sequence.blocks):
            formatted_block = {
                "block_id": f"block_{i+1:03d}",
                "opcode": block.opcode,
                "category": block.category.value,
                "inputs": block.inputs,
                "is_hat_block": block.is_hat_block,
                "next": block.next_block
            }
            formatted_blocks.append(formatted_block)
        
        return {
            "command": "create_blocks",
            "payload": {
                "target_sprite": target_sprite,
                "scripts": [{
                    "script_id": "script_001",
                    "position": {"x": 50, "y": 50},
                    "blocks": formatted_blocks
                }],
                "visual_feedback": {
                    "animate_creation": True,
                    "highlight_duration_ms": 2000,
                    "show_explanation": True,
                    "explanation_text": block_sequence.explanation
                }
            }
        }

    def get_available_actions(self) -> List[str]:
        """Get list of available actions/patterns"""
        actions = []
        
        # Add patterns
        for pattern_name, pattern_data in self.patterns_db.get("patterns", {}).items():
            actions.extend(pattern_data.get("triggers", [pattern_name]))
        
        # Add individual blocks
        for category, blocks in self.blocks_db.get("blocks", {}).items():
            actions.extend(blocks.keys())
        
        return sorted(list(set(actions)))
