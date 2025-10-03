# Comprehensive Code Review: `validators.py`

## Critical Issues (Must Fix)

### 1. **Broken Schema Validation Pattern** 🔴
```python
class SnapJSONSchema(BaseModel):
    command: str = Field(..., pattern="^create_blocks$")
```

**Problem**: Pydantic v2 changed regex validation. `pattern` parameter doesn't exist in Field().

**Fix**:
```python
from pydantic import field_validator

class SnapJSONSchema(BaseModel):
    command: str
    
    @field_validator('command')
    @classmethod
    def validate_command(cls, v):
        if v != "create_blocks":
            raise ValueError("command must be 'create_blocks'")
        return v
```

### 2. **Missing Category-Opcode Cross-Validation** 🔴
Your validation checks if opcodes exist, but **doesn't verify they're in the correct category**. This is explicitly required in your PRD:

> "category MUST match the opcode's actual category"

**Current Code**: Only checks `opcode in allowed_opcodes`
**Missing**: Verify `block['category']` matches the opcode's actual category in `blocks_db`

**Required Addition**:
```python
def validate_snap_json(
    generated_json: Dict[str, Any],
    allowed_opcodes: Set[str],
    blocks_db: Dict[str, Any]  # ADD THIS
) -> Tuple[bool, Optional[str]]:
    
    # Inside loop:
    expected_category = _get_opcode_category(block['opcode'], blocks_db)
    if block['category'] != expected_category:
        return False, f"Opcode '{block['opcode']}' must be in category '{expected_category}', not '{block['category']}'"
```

### 3. **Inadequate Hat Block Validation** 🟡
```python
if i == 0 and not block['is_hat_block']:
    return False, "First block must be a hat block."
```

**Problems**:
- Allows non-first blocks to be hat blocks (invalid)
- Doesn't validate hat blocks have correct opcodes

**Fix**:
```python
# Check first block
if i == 0:
    if not block['is_hat_block']:
        return False, f"First block must be a hat block"
    # Verify it's actually a valid event block
    valid_hat_opcodes = {'whenGreenFlag', 'whenClicked', 'whenKeyPressed', 'whenIReceive'}
    if block['opcode'] not in valid_hat_opcodes:
        return False, f"Hat block must use event opcode, got '{block['opcode']}'"
else:
    if block['is_hat_block']:
        return False, f"Only first block can be hat block, found at position {i}"
```

### 4. **Weak Input Validation** 🟡
You validate structure but **not input values**. The generative engine could produce:
```json
{"opcode": "changeYBy", "inputs": {"DY": "banana"}}  // Should be number
```

**Recommendation**: Add basic type checking for common input patterns:
```python
def _validate_inputs(opcode: str, inputs: Dict, blocks_db: Dict) -> Tuple[bool, Optional[str]]:
    """Validate input types match expected types for the opcode"""
    block_def = _get_block_definition(opcode, blocks_db)
    for key, value in inputs.items():
        expected_type = block_def.get('inputs', {}).get(key, {}).get('type')
        if expected_type == 'number' and not isinstance(value, (int, float)):
            return False, f"Input '{key}' for '{opcode}' must be number, got {type(value)}"
    return True, None
```

---

## Moderate Issues

### 5. **Inefficient Connectivity Check** 🟡
```python
unresolved_refs = next_block_references - all_block_ids_in_script
```

**Problem**: This only catches dangling forward references. Doesn't detect:
- Circular references (`block_002` → `block_001`)
- Multiple blocks pointing to same next block (merge conflicts)

**Enhanced Check**:
```python
# Check for blocks that are never referenced (orphans after first)
referenced_blocks = next_block_references
unreachable = all_block_ids_in_script - referenced_blocks - {script['blocks'][0]['block_id']}
if unreachable:
    return False, f"Unreachable blocks detected: {unreachable}"

# Check for multiple incoming edges (invalid chain structure)
if len(next_block_references) != len(all_block_ids_in_script) - 1:
    return False, "Invalid chain: blocks must form single linear sequence"
```

### 6. **Missing Script-Level Validation** 🟡
- No check for duplicate `script_id`s across scripts
- No validation of position coordinates (negative/extreme values)
- Empty `target_sprite` is allowed

---

## Minor Issues

### 7. **Incomplete Type Hints**
```python
from typing import List, Dict, Any, Optional, Tuple, Set
```
Good, but consider more specific types:
```python
from typing import Dict, Any, List, Optional, Tuple, Set

SnapJSON = Dict[str, Any]
ValidationResult = Tuple[bool, Optional[str]]
```

### 8. **Error Messages Could Be More Actionable**
```python
return False, f"Disallowed opcode used: '{block['opcode']}'"
```
Better:
```python
return False, f"Invalid opcode '{block['opcode']}' in block '{block['block_id']}'. Check snap_blocks.json for valid opcodes."
```

---

## Integration Issues with `block_generator.py`

### 9. **Signature Mismatch** 🔴
**Validator expects**:
```python
validate_snap_json(generated_json, allowed_opcodes)
```

**Generator needs**:
```python
validate_snap_json(generated_json, allowed_opcodes, blocks_db)  # For category validation
```

### 10. **Generator Doesn't Pass `blocks_db`**
In `block_generator.py`:
```python
is_valid, error = validate_snap_json(generated_json, self.allowed_opcodes)
```

Should be:
```python
is_valid, error = validate_snap_json(generated_json, self.allowed_opcodes, self.blocks_db)
```

---

## What You Got Right ✅

1. **Pydantic usage** - Good choice for structural validation
2. **Multi-stage validation** - Structure → Opcodes → Connectivity is correct flow
3. **Error passthrough** - Allowing error blocks to skip validation is smart
4. **Detailed error messages** - Using Pydantic's error details
5. **Set-based checks** - Efficient duplicate detection

---

## Production-Ready Template

```python
# mcp_server/parsers/validators.py
from typing import Dict, Any, List, Optional, Tuple, Set
from pydantic import BaseModel, field_validator, ValidationError

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
        if v.get('x', 0) < 0 or v.get('y', 0) < 0:
            raise ValueError("Position coordinates must be non-negative")
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
    def validate_command(cls, v):
        if v != "create_blocks":
            raise ValueError(f"command must be 'create_blocks', got '{v}'")
        return v


def _get_opcode_category(opcode: str, blocks_db: Dict) -> Optional[str]:
    """Find which category an opcode belongs to"""
    for category, blocks in blocks_db.get('blocks', {}).items():
        if opcode in blocks:
            return category
    return None


def validate_snap_json(
    generated_json: Dict[str, Any],
    allowed_opcodes: Set[str],
    blocks_db: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive validation: Structure → Opcodes → Categories → Connectivity
    """
    # Passthrough for trusted error blocks
    if generated_json.get("payload", {}).get("error"):
        return True, None
    
    # 1. Structural validation
    try:
        SnapJSONSchema.model_validate(generated_json)
    except ValidationError as e:
        error = e.errors()[0]
        field = ".".join(map(str, error['loc']))
        return False, f"Schema error at '{field}': {error['msg']}"
    
    valid_hat_opcodes = {'whenGreenFlag', 'whenClicked', 'whenKeyPressed', 'whenIReceive'}
    script_ids = set()
    
    for script in generated_json['payload']['scripts']:
        # Check duplicate script IDs
        if script['script_id'] in script_ids:
            return False, f"Duplicate script_id: '{script['script_id']}'"
        script_ids.add(script['script_id'])
        
        if not script['blocks']:
            return False, f"Script '{script['script_id']}' has no blocks"
        
        all_ids = set()
        next_refs = set()
        
        for i, block in enumerate(script['blocks']):
            # Duplicate ID check
            if block['block_id'] in all_ids:
                return False, f"Duplicate block_id: '{block['block_id']}'"
            all_ids.add(block['block_id'])
            
            # Hat block validation
            if i == 0:
                if not block['is_hat_block']:
                    return False, f"First block '{block['block_id']}' must be hat block"
                if block['opcode'] not in valid_hat_opcodes:
                    return False, f"Invalid hat opcode: '{block['opcode']}'"
            else:
                if block['is_hat_block']:
                    return False, f"Non-first block '{block['block_id']}' cannot be hat block"
            
            # Opcode allowlist check
            if block['opcode'] not in allowed_opcodes:
                return False, f"Disallowed opcode '{block['opcode']}' in '{block['block_id']}'"
            
            # Category validation (CRITICAL)
            expected_cat = _get_opcode_category(block['opcode'], blocks_db)
            if block['category'] != expected_cat:
                return False, f"Opcode '{block['opcode']}' must be in '{expected_cat}', not '{block['category']}'"
            
            # Track references
            if block['next']:
                next_refs.add(block['next'])
        
        # Connectivity checks
        dangling = next_refs - all_ids
        if dangling:
            return False, f"Invalid 'next' references in script '{script['script_id']}': {dangling}"
        
        # Check for unreachable blocks (orphans)
        first_block_id = script['blocks'][0]['block_id']
        reachable = {first_block_id}
        for block in script['blocks']:
            if block['next']:
                reachable.add(block['next'])
        
        unreachable = all_ids - reachable
        if unreachable:
            return False, f"Unreachable blocks in script '{script['script_id']}': {unreachable}"
    
    return True, None
```

---

## Bottom Line

good foundation, but missing critical validations that your PRD explicitly requires. The category-opcode mismatch check is non-negotiable for security. Fix the critical issues, and this becomes production-grade.

**Priority Order**:
1. Fix Pydantic pattern validation (breaks immediately)
2. Add category cross-validation (security hole)
3. Enhance hat block validation (correctness)
4. Add input type checking (robustness)