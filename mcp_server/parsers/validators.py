
# mcp_server/parsers/validators.py

from typing import Dict, Any, List, Optional, Tuple, Set
from pydantic import BaseModel, field_validator, ValidationError

# --- Type Aliases for Clarity ---
SnapJSON = Dict[str, Any]
ValidationResult = Tuple[bool, Optional[str]]
BlocksDB = Dict[str, Any]

# --- Pydantic Schemas for Structural Validation ---


class SnapBlockSchema(BaseModel):
    block_id: str
    opcode: str
    category: str
    inputs: Dict[str, Any]
    is_hat_block: bool
    next: Optional[str] = None


class ScriptSchema(BaseModel):
    script_id: str
    position: Dict[str, int]
    blocks: List[SnapBlockSchema]

    @field_validator('position')
    @classmethod
    def validate_position(cls, v):
        if 'x' not in v or 'y' not in v:
            raise ValueError("Position must contain 'x' and 'y' keys")
        return v


class PayloadSchema(BaseModel):
    target_sprite: str
    scripts: List[ScriptSchema]
    error: Optional[str] = None
    user_request: Optional[str] = None

    @field_validator('target_sprite')
    @classmethod
    def validate_sprite_name(cls, v):
        if not v or not v.strip():
            raise ValueError("target_sprite cannot be empty")
        return v


class SnapJSONSchema(BaseModel):
    command: str
    payload: PayloadSchema

    @field_validator('command')
    @classmethod
    def validate_command(cls, v: str) -> str:
        # Fix for Pydantic v2 pattern validation
        if v != "create_blocks":
            raise ValueError(f"command must be 'create_blocks', got '{v}'")
        return v

# --- Helper Function ---


def _get_opcode_category(opcode: str, blocks_db: BlocksDB) -> Optional[str]:
    """Finds the authoritative category for a given opcode from the knowledge base."""
    for category, blocks in blocks_db.get('blocks', {}).items():
        if opcode in blocks:
            return category
    return None

# --- Main Validator Function ---


def validate_snap_json(
    generated_json: SnapJSON,
    allowed_opcodes: Set[str],
    blocks_db: BlocksDB
) -> ValidationResult:
    """
    Comprehensive validation: Structure -> Opcodes -> Categories -> Connectivity -> Logic.
    """
    # Passthrough for trusted error blocks generated internally.
    if generated_json.get("payload", {}).get("error"):
        return True, None

    # 1. Structural Validation (Pydantic)
    try:
        SnapJSONSchema.model_validate(generated_json)
    except ValidationError as e:
        error = e.errors()[0]
        field = ".".join(map(str, error['loc']))
        return False, f"Schema error at '{field}': {error['msg']}"

    valid_hat_opcodes = {'whenGreenFlag', 'whenClicked', 'whenKeyPressed',
                         'receiveGo', 'receiveClick', 'receiveKey', 'whenIReceive'}
    script_ids = set()

    for script in generated_json['payload']['scripts']:
        if script['script_id'] in script_ids:
            return False, f"Duplicate script_id found: '{script['script_id']}'"
        script_ids.add(script['script_id'])

        if not script['blocks']:
            return False, f"Script '{script['script_id']}' cannot be empty."

        all_ids_in_script = set()
        next_refs = set()

        for i, block in enumerate(script['blocks']):
            # 2. Block-level ID and Logic Validation
            if block['block_id'] in all_ids_in_script:
                return False, f"Duplicate block_id '{block['block_id']}' in script '{script['script_id']}'"
            all_ids_in_script.add(block['block_id'])

            # 3. Hat Block Validation (Correctness)
            if i == 0:
                if not block['is_hat_block']:
                    return False, f"First block '{block['block_id']}' must be a hat block."
                if block['opcode'] not in valid_hat_opcodes:
                    return False, f"Invalid hat opcode '{block['opcode']}'. Must be an event block."
            elif block['is_hat_block']:
                return False, f"Block '{block['block_id']}' at position {i} cannot be a hat block."

            # 4. Opcode and Category Validation (Security & Correctness)
            if block['opcode'] not in allowed_opcodes:
                return False, f"Disallowed opcode '{block['opcode']}' in block '{block['block_id']}'."

            expected_category = _get_opcode_category(
                block['opcode'], blocks_db)
            if block['category'] != expected_category:
                return False, f"Opcode '{block['opcode']}' must have category '{expected_category}', but got '{block['category']}'."

            if block['next']:
                next_refs.add(block['next'])

        # 5. Connectivity Validation
        dangling_refs = next_refs - all_ids_in_script
        if dangling_refs:
            return False, f"Dangling 'next' references found in script '{script['script_id']}': {dangling_refs}"

        # Check for unreachable (orphaned) blocks
        first_block_id = script['blocks'][0]['block_id']
        reachable_blocks = {first_block_id}
        # Build the set of all blocks that are pointed to
        for b in script['blocks']:
            if b['next']:
                reachable_blocks.add(b['next'])

        unreachable = all_ids_in_script - reachable_blocks
        if unreachable:
            return False, f"Unreachable (orphaned) blocks in script '{script['script_id']}': {unreachable}"

    return True, None
