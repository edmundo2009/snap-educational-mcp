an updated, holistic summary of the architecture. It will serve as an excellent guide for your rule-based testing phase while keeping the overall project vision in view.

This condensed summary reflects the final, production-ready implementation. The primary focus is on the components crucial for the rule-based pipeline, with the generative/caching and communication layers summarized briefly to maintain the "grand picture."

---

### **Condensed Codebase Summary (Post-Implementation)**

This summary outlines the key components of the Snap! Educational MCP. The primary focus is on the **Rule-Based Pipeline** (highlighted), which is the target for immediate testing and hardening.

================================================
**FILE: mcp_server/main.py (Tool Entry Point)**
*   **Purpose**: The main entry point for the agent. The `generate_snap_blocks` tool orchestrates the entire server-side process. For our testing, it will initiate the rule-based workflow.
================================================
```python
# mcp_server/main.py

# ... (imports)

@mcp.tool()
async def generate_snap_blocks(
    description: str,
    # ... other args
) -> Dict[str, Any]:
    """
    Orchestrates the conversion of natural language to Snap! blocks.
    """
    try:
        # 1. Parse user's text into a structured intent
        intents = parser.parse(description)
        if not intents:
            # ... handle no intent found

        main_intent = intents[0]

        # 2. Call the Block Generator, which will use the rule-based path
        snap_spec = generator.generate_snap_json(main_intent, description)

        # 3. Send the final, validated JSON to the browser
        # ... (logic to call snap_communicator)

    except Exception as e:
        # ... handle errors
```

---
### **Primary Focus: The Rule-Based Pipeline**
---

================================================
**FILE: mcp_server/parsers/intent_parser.py (The Translator)**
*   **Purpose**: Translates raw user text (e.g., "when space is pressed, jump") into a structured `ParsedIntent` object. The accuracy of this component is critical for the rule-based engine to find the correct pattern.
================================================
```python
# mcp_server/parsers/intent_parser.py

@dataclass
class ParsedIntent:
    """The structured output of the parser."""
    action: str                  # e.g., "jump"
    trigger: Optional[str] = None  # e.g., "key_press"
    parameters: Dict[str, Any] = field(default_factory=dict) # e.g., {"key": "space"}
    # ...

class SnapIntentParser:
    """Uses pattern matching to extract intent from text."""
    def parse(self, text: str) -> List[ParsedIntent]:
        # ... implementation ...
        # Returns a list of ParsedIntent objects
        pass
```

================================================
**FILE: mcp_server/knowledge/patterns.json (The Recipe Book)**
*   **Purpose**: The heart of the rule-based system. It contains pre-defined "recipes" for common actions. Each pattern maps trigger phrases to a specific sequence of Snap! blocks. Hardening this file is a primary goal of our testing.
================================================
```json
// mcp_server/knowledge/patterns.json
{
  "patterns": {
    "jump": {
      "blocks": [
        { "opcode": "changeYBy", "inputs": {"DY": 50}, "category": "motion" },
        { "opcode": "doWait",    "inputs": {"DURATION": 0.3}, "category": "control" },
        { "opcode": "changeYBy", "inputs": {"DY": -50}, "category": "motion" }
      ],
      "triggers": ["jump", "hop", "bounce up", "leap"],
      "explanation": "Makes sprite jump up and come back down!"
    }
    // ... many other patterns
  }
}
```

================================================
**FILE: mcp_server/knowledge/snap_blocks.json (The Ingredient List)**
*   **Purpose**: Defines every valid "ingredient" (Snap! block) that can be used in a recipe. It's the ground truth for opcodes and their categories, used by both the generator and the validator.
================================================
```json
// mcp_server/knowledge/snap_blocks.json
{
  "blocks": {
    "motion": {
      "changeYBy": {
        "opcode": "changeYBy",
        "category": "motion",
        "parameters": ["dy"],
        "default_values": {"dy": 10}
      }
    },
    "control": {
       "doWait": {
        "opcode": "doWait",
        "category": "control",
        "parameters": ["duration"]
      }
    }
    // ... all other blocks
  }
}
```

================================================
**FILE: mcp_server/tools/block_generator.py (The Master Chef)**
*   **Purpose**: The central orchestrator. For our current focus, we will only be testing its rule-based capabilities (`_find_matching_pattern`, `_create_from_pattern`).
================================================
```python
# mcp_server/tools/block_generator.py

@dataclass
class SnapBlock: # ...
@dataclass
class BlockSequence: # ...

class SnapBlockGenerator:
    def __init__(self, knowledge_path: str, patterns_path: str):
        # Loads patterns.json and snap_blocks.json
        # Builds the trigger map for fast lookups
        # ...

    def generate_snap_json(self, intent: ParsedIntent, user_description: str) -> dict:
        """Main orchestrator. We will temporarily disable the generative path."""
        
        # --- Rule-Based Path (Our Focus) ---
        pattern = self._find_matching_pattern(intent.action)
        if pattern:
            block_sequence = self._create_from_pattern(pattern, intent)
            return self.format_for_snap(block_sequence, "Sprite")
        
        # --- Generative Path (Ignored for now) ---
        # else:
        #    generated_json = self._call_generative_engine(user_description)
        
        # For testing, we want an explicit failure if no pattern is found.
        return self._create_error_fallback("No rule-based pattern found", user_description)

    def _find_matching_pattern(self, action: str) -> Optional[dict]:
        """Finds a pattern using direct lookup and fuzzy matching."""
        # ... implementation ...
        pass

    def _create_from_pattern(self, pattern: dict, intent: ParsedIntent) -> BlockSequence:
        """Builds a BlockSequence object from a pattern recipe."""
        # ... implementation ...
        pass

    def format_for_snap(self, block_sequence: BlockSequence, target_sprite: str) -> dict:
        """Converts a BlockSequence into the final, validated JSON format."""
        # ... implementation ...
        pass

    # --- Other Methods (Ignored for now) ---
    # def _call_generative_engine(...)
    # def _check_cache(...)
```

================================================
**FILE: mcp_server/parsers/validators.py (The Quality Inspector)**
*   **Purpose**: The final gatekeeper. Before any JSON is sent, this component validates its structure, opcodes, categories, and connectivity. This ensures that the output of the rule-based engine is always safe and correct.
================================================
```python
# mcp_server/parsers/validators.py

# ... (Pydantic schemas: SnapJSONSchema, PayloadSchema, etc.)

def validate_snap_json(
    generated_json: Dict[str, Any],
    allowed_opcodes: Set[str],
    blocks_db: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Performs comprehensive validation on the generated JSON.
    1. Structural validation via Pydantic.
    2. Opcode allowlist check.
    3. Category cross-validation (opcode must match category).
    4. Hat block logic validation.
    5. Connectivity check (no dangling or orphaned blocks).
    """
    # ... implementation ...
    pass
```

---
### **Brief: Other Key Components (The Grand Picture)**
---

================================================
**FILE: mcp_server/tools/snap_communicator.py (The Delivery Service)**
*   **Purpose**: Manages the WebSocket server. It's responsible for handling connections from the browser extension and sending the final, validated JSON payload to Snap!. The `generate_snap_blocks` tool will ultimately hand its result to this component.
================================================

================================================
**FILES: browser_extension/snap_bridge/ (The Receiver)**
*   **Purpose**: This collection of JavaScript files runs inside the Snap! webpage.
    *   `bridge.js`: Manages the WebSocket connection on the client side.
    *   `block_creator.js`: Receives the JSON from `snap_communicator` and uses Snap!'s internal APIs to physically build the blocks on the user's screen.
================================================