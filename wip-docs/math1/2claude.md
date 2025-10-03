
# POC Plan (2-3 Days Max)

## **Goal:** One working end-to-end demo: "Word problem → Snap! blocks appear"

### **Phase 1: Minimal Math Patterns (4 hours)**

Create `math_patterns.json` with **3 patterns only**:

```json
{
  "patterns": {
    "unit_rate": {
      "triggers": ["per hour", "per lawn", "rate", "speed", "unit rate"],
      "variables": ["quantity1", "quantity2", "unit_rate", "target_quantity", "result"],
      "blocks": [
        {"opcode": "setVar", "var": "quantity1", "value": "{{num1}}"},
        {"opcode": "setVar", "var": "quantity2", "value": "{{num2}}"},
        {"opcode": "setVar", "var": "unit_rate", "value": "{{num1}} / {{num2}}"},
        {"opcode": "say", "message": "Unit rate is: {{unit_rate}}"},
        {"opcode": "setVar", "var": "target_quantity", "value": "{{num3}}"},
        {"opcode": "setVar", "var": "result", "value": "{{unit_rate}} * {{num3}}"},
        {"opcode": "say", "message": "Final answer: {{result}}"}
      ]
    },
    "ratio_equivalent": {
      "triggers": ["equivalent ratio", "scale", "multiply both"],
      "variables": ["ratio_a", "ratio_b", "scale_factor", "new_a", "new_b"],
      "blocks": [
        {"opcode": "setVar", "var": "ratio_a", "value": "{{num1}}"},
        {"opcode": "setVar", "var": "ratio_b", "value": "{{num2}}"},
        {"opcode": "setVar", "var": "scale_factor", "value": "{{num3}}"},
        {"opcode": "setVar", "var": "new_a", "value": "{{num1}} * {{num3}}"},
        {"opcode": "setVar", "var": "new_b", "value": "{{num2}} * {{num3}}"},
        {"opcode": "say", "message": "New ratio: {{new_a}}:{{new_b}}"}
      ]
    },
    "simple_division": {
      "triggers": ["divide", "split", "share equally"],
      "variables": ["total", "parts", "each_part"],
      "blocks": [
        {"opcode": "setVar", "var": "total", "value": "{{num1}}"},
        {"opcode": "setVar", "var": "parts", "value": "{{num2}}"},
        {"opcode": "setVar", "var": "each_part", "value": "{{num1}} / {{num2}}"},
        {"opcode": "say", "message": "Each part gets: {{each_part}}"}
      ]
    }
  }
}
```

**Why 3?** Enough to test pattern matching logic, not so many you waste time writing patterns.

---

### **Phase 2: Dumb Parser (2 hours)**

**Don't** create a sophisticated NLP parser. Use regex + keyword matching:

```python
# mcp_server/parsers/math_parser.py
import re

def parse_math_problem(text: str) -> dict:
    """Extract numbers and match to pattern triggers."""
    
    # Extract all numbers
    numbers = [float(n) for n in re.findall(r'\d+\.?\d*', text)]
    
    # Load patterns
    patterns = load_json("knowledge/math_patterns.json")
    
    # Find matching pattern by triggers
    text_lower = text.lower()
    for pattern_name, pattern_data in patterns["patterns"].items():
        for trigger in pattern_data["triggers"]:
            if trigger in text_lower:
                return {
                    "pattern": pattern_name,
                    "numbers": numbers,
                    "text": text
                }
    
    return {"pattern": None, "numbers": numbers, "text": text}
```

**That's it.** No fancy NLP. Just "does text contain trigger words?"

---

### **Phase 3: Template Substitution (2 hours)**

Modify `block_generator.py`:

```python
# mcp_server/tools/block_generator.py

def generate_from_math_pattern(self, parsed: dict) -> dict:
    """Replace {{num1}}, {{num2}} etc. with actual numbers."""
    
    if not parsed["pattern"]:
        return self._create_error_fallback("No pattern matched")
    
    # Load pattern
    pattern = self.math_patterns[parsed["pattern"]]
    blocks = pattern["blocks"]
    numbers = parsed["numbers"]
    
    # Simple substitution
    snap_blocks = []
    for block_template in blocks:
        block = block_template.copy()
        
        # Replace {{num1}} with numbers[0], etc.
        for key, value in block.items():
            if isinstance(value, str):
                for i, num in enumerate(numbers):
                    value = value.replace(f"{{{{num{i+1}}}}}", str(num))
                block[key] = value
        
        snap_blocks.append(block)
    
    return self.format_for_snap(snap_blocks, "Sprite")
```

---

### **Phase 4: Test Cases (1 hour)**

Create `test_math_poc.py`:

```python
# tests/test_math_poc.py

test_cases = [
    {
        "input": "If 7 hours to mow 4 lawns, how many in 35 hours?",
        "expected_pattern": "unit_rate",
        "expected_numbers": [7, 4, 35]
    },
    {
        "input": "Ratio 3:2, scale by 4",
        "expected_pattern": "ratio_equivalent",
        "expected_numbers": [3, 2, 4]
    },
    {
        "input": "Divide 20 cookies among 5 kids",
        "expected_pattern": "simple_division",
        "expected_numbers": [20, 5]
    }
]

def test_poc():
    for test in test_cases:
        parsed = parse_math_problem(test["input"])
        assert parsed["pattern"] == test["expected_pattern"]
        assert parsed["numbers"] == test["expected_numbers"]
        
        snap_json = generate_from_math_pattern(parsed)
        assert snap_json["status"] == "success"
        print(f"✓ {test['input']}")
```

---

### **Phase 5: Manual Snap! Test (1 hour)**

1. Run test case: `"If 7 hours to mow 4 lawns, how many in 35 hours?"`
2. Copy generated JSON
3. Paste into Snap! (via your browser extension)
4. **Manually verify blocks appear and work**

**Success criteria:**
- Blocks appear in correct order
- Variables have correct values
- Clicking blocks shows intermediate results
- No JavaScript errors

---

## What You're **NOT** Doing in POC

❌ "Common misconceptions" metadata  
❌ Sophisticated NLP parsing  
❌ Pedagogical scaffolds  
❌ Multiple grade levels  
❌ Visualization blocks  
❌ LLM fallback  
❌ Cache system  
❌ Teacher notes generation  

**All that comes AFTER POC proves the core pipeline works.**

---

## Success Metric

**POC is done when:**
1. 3 test problems generate valid Snap! JSON
2. JSON validates against your schema
3. Blocks appear in Snap! when you paste the JSON
4. You can click blocks and see variable values

**Time estimate:** 8-10 hours of focused work

**Then** you expand patterns, add LLM fallback, improve parser, etc.

---

## Actionable Tasks (In Order)

```bash
[ ] Create math_patterns.json with 3 patterns
[ ] Write parse_math_problem() function (regex + keyword matching)

[ ] Modify block_generator.py to handle template substitution
[ ] Write 3 test cases

[ ] Run tests, fix bugs until all pass
[ ] Manually test one example in actual Snap!

[ ] Document what worked/failed
[ ] Plan Phase 2 expansions
```
