

### Condensed Codebase Summary

This summary includes only the files and functions directly involved in the process of receiving a user's command and turning it into Snap! blocks, as outlined in your `prd3.md` document.

================================================
**FILE: mcp_server/main.py (Relevant Tool)**
*   **Purpose**: The entry point for an LLM agent. The `generate_snap_blocks` function orchestrates the process by taking the user's text, calling the parser, and then invoking the block generator. This is where the new hybrid logic will be called from.
================================================
```python
# mcp_server/main.py

# ... (imports and initializations)

@mcp.tool()
async def generate_snap_blocks(
	description: str,
	# ... other args
) -> Dict[str, Any]:
	"""
	Convert natural language to Snap! blocks and optionally execute in browser.
	"""
	try:
		# 1. Parse natural language into structured intent
		intents = parser.parse(description)

		if not intents:
			# ... (handle no intents found)

		# 2. Generate block sequence using the "Master Chef"
		#    THIS IS THE CORE LOGIC TO BE REPLACED/UPGRADED
		block_sequence = generator.generate_blocks(intents, complexity)

		# 3. Format for Snap! bridge
		snap_spec = generator.format_for_snap(block_sequence, target_sprite)

		# 4. Send to browser via communicator
		# ... (rest of the function)
# ...
```

================================================
**FILE: mcp_server/parsers/intent_parser.py**
*   **Purpose**: Converts raw text like "make the sprite jump" into a structured `ParsedIntent` object. The output of this parser is the input for the block generator.
================================================
```python
# mcp_server/parsers/intent_parser.py

@dataclass
class ParsedIntent:
    """Structured intent representation"""
    action: str
    trigger: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    # ...

class SnapIntentParser:
    # ... (patterns and logic)
    def parse(self, text: str) -> List[ParsedIntent]:
        # ... returns a list of ParsedIntent objects
        pass
```

================================================
**FILE: mcp_server/tools/block_generator.py**
*   **Purpose**: The "Master Chef." This is the primary file to be modified. Currently, it uses a rigid, rule-based lookup. It will be upgraded to a hybrid orchestrator that decides between its existing rules and calling the Gemini API.
================================================
```python
# mcp_server/tools/block_generator.py

from ..parsers.intent_parser import ParsedIntent

# ... (dataclasses)

class SnapBlockGenerator:
    def __init__(self, knowledge_path: str = "knowledge/snap_blocks.json",
                 patterns_path: str = "knowledge/patterns.json"):
        # ... (loads knowledge base)

    def generate_blocks(self, intents: List[ParsedIntent], complexity: str = "beginner") -> BlockSequence:
        """
        CURRENT LOGIC: Generate a sequence of Snap! blocks from parsed intents
        using only rule-based lookups.
        """
        # ... (iterates through intents)
        # Tries to find a matching pattern, then a matching block definition.
        # If both fail, it creates a fallback "doSay" block.
        pass # This function will be completely redesigned.

    def format_for_snap(self, block_sequence: BlockSequence, target_sprite: str = "Sprite") -> Dict[str, Any]:
        """
        Formats the generated blocks into the final JSON structure for the browser.
        THE OUTPUT OF THE NEW GENERATIVE ENGINE MUST MATCH THIS STRUCTURE.
        """
        # ...
        return {
            "command": "create_blocks",
            "payload": {
                "target_sprite": target_sprite,
                "scripts": [{
                    "script_id": "script_001",
                    "blocks": formatted_blocks
                }],
                # ...
            }
        }

    # ... (helper methods for rule-based lookups)
```

================================================
**FILES: mcp_server/knowledge/*.json**
**Purpose**: These files are the "cookbook" for the rule-based system. 
`patterns.json` contains multi-block recipes for commands like "jump." 
`snap_blocks.json` contains single-ingredient definitions for every available block. 
They will continue to be used for the "fast path" and for creating the opcode allowlist for the generative path.
================================================
```json
// mcp_server/knowledge/patterns.json
{
  "patterns": {
    "jump": {
      "blocks": [
        { "opcode": "changeYBy", "inputs": {"DY": 50}, "category": "motion" },
        { "opcode": "doWait", "inputs": {"DURATION": 0.3}, "category": "control" },
        { "opcode": "changeYBy", "inputs": {"DY": -50}, "category": "motion" }
      ],
      "triggers": ["jump", "hop", "bounce up", "leap"],
      // ...
    }
  }
}

// mcp_server/knowledge/snap_blocks.json
{
  "blocks": {
    "motion": {
      "forward": {
        "opcode": "forward",
        "category": "motion",
        // ...
      }
    }
  }
}
```

================================================
**FILE: mcp_server/parsers/validators.py**
**Purpose**: Currently provides input validation. 
This file is the ideal place to build the new "Executive Chef's Inspection" layer for validating the JSON output from both the rule-based and generative engines.
================================================
```python
# mcp_server/parsers/validators.py

# ... (current SnapInputValidator class)

# THIS IS WHERE THE NEW VALIDATION LOGIC WILL GO.
# For example:
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class BlockSchema(BaseModel):
    block_id: str
    opcode: str
    category: str
    inputs: Dict[str, Any]
    is_hat_block: bool
    next: Optional[str]

class ScriptSchema(BaseModel):
    script_id: str
    blocks: List[BlockSchema]

class PayloadSchema(BaseModel):
    target_sprite: str
    scripts: List[ScriptSchema]

class SnapJSONSchema(BaseModel):
    command: str = Field(..., pattern="^create_blocks$")
    payload: PayloadSchema

def validate_snap_json(generated_json: dict, allowed_opcodes: set) -> bool:
    """
    Validates the structure and content of the generated Snap! JSON.
    (This function needs to be implemented).
    """
    # 1. Pydantic schema validation
    # 2. Opcode allowlist check
    # 3. Connectivity check (next references are valid)
    pass
```
