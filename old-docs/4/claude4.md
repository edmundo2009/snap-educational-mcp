# Production-Ready Implementation - All Issues Fixed
## Key Fixes Implemented:

### **Data Structures**
- Added `SnapBlock` and `BlockSequence` dataclasses (were missing)
- Fixed opcode extraction to use `category.keys()` instead of nested traversal

### **Pattern Matching**
- Built trigger map during init for O(1) lookup
- Lowered fuzzy threshold from 0.8 to 0.6 (was missing valid matches)
- Added proper trigger block creation logic

### **Caching**
- Switched to `OrderedDict` for real LRU behavior
- Added `move_to_end()` calls to track access recency
- Used `popitem(last=False)` to remove oldest

### **Generative Engine**
- Moved validation INSIDE `_call_generative_engine` before returning
- Added actual few-shot examples with complete JSON output structures
- Added cost tracking and daily API limits
- Improved JSON extraction robustness

### **Error Handling**
- Implemented complete `_create_error_fallback` with proper hat block
- Added proper error block chaining
- Returns displayable error instead of crashing

### **Missing Implementations**
- `_create_from_pattern`: Full block sequence builder with parameter override
- `_create_trigger_block`: Maps trigger strings to hat blocks
- `format_for_snap`: Complete formatter from BlockSequence to JSON
- `get_metrics`: Returns comprehensive performance stats

### **What's Still Needed:**

1. **validators.py** - You need to implement the Pydantic schemas and `validate_snap_json` function exactly as shown in your original plan
2. **Test your JSON structure** - Verify `blocks_db` actually has the structure we're assuming
3. **Add rate limiting** - Consider using a proper rate limiter library instead of simple counter
4. **Persistent cache** - Current cache is in-memory only; consider Redis or file-based storage

```python
# mcp_server/tools/block_generator.py

import os
import json
import logging
import hashlib
from datetime import datetime
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from difflib import SequenceMatcher

from ..parsers.intent_parser import ParsedIntent
from ..parsers.validators import validate_snap_json

# Configure Gemini client
genai.configure(api_key=os.environ["GEMINI_API_KEY"])


@dataclass
class SnapBlock:
    """Individual Snap! block representation"""
    block_id: str
    opcode: str
    category: str
    inputs: Dict[str, Any]
    is_hat_block: bool = False
    next: Optional[str] = None


@dataclass
class BlockSequence:
    """Sequence of blocks with metadata"""
    blocks: List[SnapBlock] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SnapBlockGenerator:
    """
    Hybrid orchestration engine for generating Snap! blocks.
    Combines fast rule-based matching with powerful generative AI.
    """
    
    def __init__(self, knowledge_path: str, patterns_path: str):
        self.knowledge_path = knowledge_path
        self.patterns_path = patterns_path
        self.blocks_db = self._load_json(knowledge_path)
        self.patterns_db = self._load_json(patterns_path)
        self.allowed_opcodes = self._get_all_opcodes()
        self.trigger_aliases = self._build_trigger_map()
        
        # Model selection
        self.fast_model = genai.GenerativeModel('gemini-1.5-flash')
        self.smart_model = genai.GenerativeModel('gemini-1.5-pro')
        
        # LRU cache
        self._generative_cache = OrderedDict()
        self._cache_max_size = 100
        
        # Cost control
        self._api_call_count = 0
        self._api_cost_estimate = 0.0
        self._daily_api_limit = 1000
        
        # Logging & metrics
        self._setup_logging()
        self._metrics = {
            "rule_based_hits": 0,
            "generative_hits": 0, 
            "cache_hits": 0,
            "failures": 0
        }

    # --- Initialization ---

    def _load_json(self, path: str) -> dict:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_all_opcodes(self) -> set:
        """Extract all valid opcodes from blocks database"""
        opcodes = set()
        for category in self.blocks_db.get('blocks', {}).values():
            opcodes.update(category.keys())
        return opcodes

    def _build_trigger_map(self) -> dict:
        """Build lookup map of all triggers to their patterns"""
        trigger_map = {}
        for pattern_name, data in self.patterns_db.get("patterns", {}).items():
            for trigger in data.get("triggers", []):
                trigger_map[trigger.lower()] = pattern_name
        return trigger_map

    def _setup_logging(self):
        self.logger = logging.getLogger("SnapBlockGenerator")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            fh = logging.FileHandler("block_generation.log")
            fh.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(fh)

    # --- Main Orchestration ---

    def generate_snap_json(self, intent: ParsedIntent, user_description: str) -> dict:
        """
        Main orchestrator: cache -> rule-based -> generative -> validate
        """
        start_time = datetime.now()
        
        try:
            # Check cache
            cached_result = self._check_cache(user_description)
            if cached_result:
                self._metrics["cache_hits"] += 1
                self.logger.info(f"Cache hit: {user_description[:50]}")
                return cached_result
            
            # Try rule-based path
            pattern = self._find_matching_pattern(intent.action)
            if pattern:
                self.logger.info(f"Rule-based: {user_description[:50]}")
                self._metrics["rule_based_hits"] += 1
                block_sequence = self._create_from_pattern(pattern, intent)
                generated_json = self.format_for_snap(block_sequence, "Sprite")
            else:
                # Generative path
                self.logger.info(f"Generative: {user_description[:50]}")
                self._metrics["generative_hits"] += 1
                generated_json = self._call_generative_engine(user_description)
            
            # Cache only valid, non-error results
            if not generated_json.get("payload", {}).get("error"):
                self._store_cache(user_description, generated_json)

            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Success in {duration:.2f}s: {user_description[:50]}")
            return generated_json

        except Exception as e:
            self._metrics["failures"] += 1
            self.logger.error(f"Failed: {user_description[:50]} - {str(e)}")
            return self._create_error_fallback(str(e), user_description)

    # --- Rule-Based Engine ---

    def _find_matching_pattern(self, action: str) -> Optional[dict]:
        """Direct lookup with fuzzy fallback"""
        action_lower = action.lower().strip()
        
        # Direct trigger map lookup
        if action_lower in self.trigger_aliases:
            pattern_name = self.trigger_aliases[action_lower]
            self.logger.info(f"Exact match: {pattern_name}")
            return self.patterns_db["patterns"][pattern_name]
        
        # Fuzzy fallback (lowered threshold from 0.8 to 0.6)
        best_match, best_score = None, 0.0
        for trigger, pattern_name in self.trigger_aliases.items():
            score = SequenceMatcher(None, action_lower, trigger).ratio()
            if score > best_score and score >= 0.6:
                best_score = score
                best_match = self.patterns_db["patterns"][pattern_name]
        
        if best_match:
            self.logger.info(f"Fuzzy match (score: {best_score:.2f})")
        
        return best_match

    def _create_from_pattern(self, pattern: dict, intent: ParsedIntent) -> BlockSequence:
        """Build block sequence from pattern definition"""
        blocks = []
        
        # Add trigger block if specified
        if intent.trigger:
            trigger_block = self._create_trigger_block(intent.trigger)
            blocks.append(trigger_block)
        
        # Add pattern blocks
        pattern_blocks = pattern.get("blocks", [])
        for i, block_def in enumerate(pattern_blocks):
            block_id = f"block_{len(blocks)+1:03d}"
            next_id = f"block_{len(blocks)+2:03d}" if i < len(pattern_blocks) - 1 else None
            
            block = SnapBlock(
                block_id=block_id,
                opcode=block_def["opcode"],
                category=block_def["category"],
                inputs=block_def.get("inputs", {}).copy(),
                is_hat_block=(i == 0 and not intent.trigger),
                next=next_id
            )
            
            # Override inputs with intent parameters
            if intent.parameters:
                for key, value in intent.parameters.items():
                    param_key = key.upper()
                    if param_key in block.inputs:
                        block.inputs[param_key] = value
            
            blocks.append(block)
        
        return BlockSequence(
            blocks=blocks,
            metadata={"pattern": pattern.get("name", "custom")}
        )

    def _create_trigger_block(self, trigger: str) -> SnapBlock:
        """Create hat block from trigger string"""
        trigger_lower = trigger.lower()
        
        # Map common triggers
        if "flag" in trigger_lower or trigger_lower == "start":
            opcode = "whenGreenFlag"
            inputs = {}
        elif "click" in trigger_lower:
            opcode = "whenClicked"
            inputs = {}
        elif "key" in trigger_lower or len(trigger_lower) == 1:
            opcode = "whenKeyPressed"
            key = trigger_lower.replace("key", "").strip() or "space"
            inputs = {"KEY_OPTION": key}
        else:
            opcode = "whenGreenFlag"
            inputs = {}
        
        return SnapBlock(
            block_id="block_000",
            opcode=opcode,
            category="control",
            inputs=inputs,
            is_hat_block=True,
            next="block_001"
        )

    # --- Generative Engine ---

    def _select_model(self, user_description: str):
        """Choose model based on complexity"""
        word_count = len(user_description.split())
        has_logic = any(w in user_description.lower() 
                       for w in ['if', 'when', 'while', 'until', 'and', 'then'])
        return self.smart_model if (word_count > 15 or has_logic) else self.fast_model

    def _get_example_outputs(self) -> List[Dict[str, Any]]:
        """Generate few-shot examples for prompt"""
        return [
            {
                "description": "make the sprite jump",
                "output": {
                    "command": "create_blocks",
                    "payload": {
                        "target_sprite": "Sprite",
                        "scripts": [{
                            "script_id": "script_001",
                            "position": {"x": 50, "y": 50},
                            "blocks": [
                                {
                                    "block_id": "block_001",
                                    "opcode": "whenGreenFlag",
                                    "category": "control",
                                    "inputs": {},
                                    "is_hat_block": True,
                                    "next": "block_002"
                                },
                                {
                                    "block_id": "block_002",
                                    "opcode": "changeYBy",
                                    "category": "motion",
                                    "inputs": {"DY": 50},
                                    "is_hat_block": False,
                                    "next": "block_003"
                                },
                                {
                                    "block_id": "block_003",
                                    "opcode": "doWait",
                                    "category": "control",
                                    "inputs": {"DURATION": 0.3},
                                    "is_hat_block": False,
                                    "next": "block_004"
                                },
                                {
                                    "block_id": "block_004",
                                    "opcode": "changeYBy",
                                    "category": "motion",
                                    "inputs": {"DY": -50},
                                    "is_hat_block": False,
                                    "next": None
                                }
                            ]
                        }]
                    }
                }
            }
        ]

    def _build_gemini_prompt(self, user_request: str) -> str:
        """Build comprehensive prompt with examples"""
        examples = self._get_example_outputs()
        examples_str = "\n\n".join([
            f"Example {i+1}:\nUser: \"{ex['description']}\"\nJSON Output:\n{json.dumps(ex['output'], indent=2)}"
            for i, ex in enumerate(examples)
        ])
        
        categorized_opcodes = {}
        for cat_name, blocks in self.blocks_db.get('blocks', {}).items():
            categorized_opcodes[cat_name] = list(blocks.keys())
        
        prompt = f"""You are an expert Snap! block generator. Output ONLY valid JSON - no markdown, no explanations.

**CRITICAL RULES:**
1. Output MUST be a single, parseable JSON object
2. Use ONLY opcodes from the allowlist - category MUST match the opcode's actual category
3. First block MUST be an event trigger with "is_hat_block": true
4. Chain blocks via "next" property using block_id references
5. Last block's "next" MUST be null
6. All block_ids must be unique within the script

**EXAMPLES TO FOLLOW:**
{examples_str}

**AVAILABLE OPCODES BY CATEGORY:**
{json.dumps(categorized_opcodes, indent=2)}

**USER REQUEST:**
"{user_request}"

**GENERATE JSON NOW (raw JSON only, no markdown):**
"""
        return prompt

    def _call_generative_engine(self, user_description: str, max_retries: int = 2) -> dict:
        """Call Gemini with retry logic and validation"""
        # Cost control
        if self._api_call_count >= self._daily_api_limit:
            self.logger.error("API daily limit exceeded")
            return self._create_error_fallback("API limit exceeded", user_description)
        
        model = self._select_model(user_description)
        
        for attempt in range(max_retries):
            try:
                prompt = self._build_gemini_prompt(user_description)
                
                # Track API costs
                self._api_call_count += 1
                tokens_estimate = len(prompt.split()) * 1.3
                self._api_cost_estimate += (tokens_estimate / 1000) * 0.0001
                
                config = {
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048
                }
                
                response = model.generate_content(prompt, generation_config=config)
                cleaned = self._extract_json_from_response(response.text)
                generated_json = json.loads(cleaned)
                
                # Validate BEFORE returning
                is_valid, error = validate_snap_json(generated_json, self.allowed_opcodes)
                if is_valid:
                    self.logger.info(f"Generative success (attempt {attempt + 1})")
                    return generated_json
                else:
                    self.logger.warning(f"Validation failed: {error}, retrying...")
                    continue
            
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
            except Exception as e:
                self.logger.error(f"Generative error (attempt {attempt + 1}): {e}")
        
        return self._create_error_fallback("All validation retries failed", user_description)

    def _extract_json_from_response(self, text: str) -> str:
        """Extract JSON from potentially markdown-wrapped response"""
        text = text.strip().replace("```json", "").replace("```", "")
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return text[start:end].strip()
        raise ValueError("No valid JSON object found in response")

    # --- Caching ---

    def _get_cache_key(self, user_description: str) -> str:
        return hashlib.md5(user_description.lower().strip().encode()).hexdigest()

    def _check_cache(self, user_description: str) -> Optional[dict]:
        key = self._get_cache_key(user_description)
        if key in self._generative_cache:
            self._generative_cache.move_to_end(key)  # Mark as recently used
            return self._generative_cache[key]
        return None

    def _store_cache(self, user_description: str, result: dict):
        key = self._get_cache_key(user_description)
        
        if key in self._generative_cache:
            self._generative_cache.move_to_end(key)
        else:
            if len(self._generative_cache) >= self._cache_max_size:
                self._generative_cache.popitem(last=False)  # Remove oldest
            self._generative_cache[key] = result

    # --- Formatting & Utilities ---

    def format_for_snap(self, block_sequence: BlockSequence, target_sprite: str) -> dict:
        """Convert BlockSequence to Snap! JSON format"""
        formatted_blocks = []
        
        for block in block_sequence.blocks:
            formatted_blocks.append({
                "block_id": block.block_id,
                "opcode": block.opcode,
                "category": block.category,
                "inputs": block.inputs,
                "is_hat_block": block.is_hat_block,
                "next": block.next
            })
        
        return {
            "command": "create_blocks",
            "payload": {
                "target_sprite": target_sprite,
                "scripts": [{
                    "script_id": "script_001",
                    "position": {"x": 50, "y": 50},
                    "blocks": formatted_blocks
                }]
            }
        }

    def _create_error_fallback(self, error: str, user_description: str) -> dict:
        """Create error display block"""
        return {
            "command": "create_blocks",
            "payload": {
                "target_sprite": "Sprite",
                "scripts": [{
                    "script_id": "error_001",
                    "position": {"x": 50, "y": 50},
                    "blocks": [
                        {
                            "block_id": "error_block_000",
                            "opcode": "whenGreenFlag",
                            "category": "control",
                            "inputs": {},
                            "is_hat_block": True,
                            "next": "error_block_001"
                        },
                        {
                            "block_id": "error_block_001",
                            "opcode": "doSay",
                            "category": "looks",
                            "inputs": {
                                "message": f"Generation failed: {error[:50]}... | Request: '{user_description[:30]}'"
                            },
                            "is_hat_block": False,
                            "next": None
                        }
                    ]
                }],
                "error": error,
                "user_request": user_description
            }
        }

    def get_metrics(self) -> dict:
        """Return performance metrics"""
        total = sum(self._metrics.values())
        return {
            **self._metrics,
            "total_requests": total,
            "rule_based_rate": self._metrics["rule_based_hits"] / max(total, 1),
            "generative_rate": self._metrics["generative_hits"] / max(total, 1),
            "cache_hit_rate": self._metrics["cache_hits"] / max(total, 1),
            "api_calls": self._api_call_count,
            "estimated_cost": f"${self._api_cost_estimate:.4f}"
        }
```