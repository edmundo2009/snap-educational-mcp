# Refined Snap! MCP Requirements & Parser Strategy

## Requirements.txt - Lightweight Version




# ============================================================================
# NLP LIBRARIES - NOT NEEDED!
# ============================================================================
# ❌ nltk>=3.8              # REMOVED - Claude handles this
# ❌ spacy>=3.7.0           # REMOVED - Overkill for our use case
# ❌ textblob>=0.17.1       # REMOVED - Unnecessary dependency
# ❌ transformers>=4.30.0   # REMOVED - Way too heavy
# ❌ torch>=2.0.0           # REMOVED - Not needed

# ============================================================================
# TOTAL SIZE: ~50MB instead of ~500MB
# ============================================================================


---

## Architecture Decision: Why No Heavy NLP?

### **When Using with Rovodev cli or Claude Code**

```
┌─────────────────────────────────────────────────┐
│  Human: "Make a jumping game"                   │
└────────────────┬────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────┐
│  Claude Code: (Does the NLP!)                   │
│  - Understands "jumping game" concept           │
│  - Breaks down into steps                       │
│  - Formats as structured MCP calls              │
└────────────────┬────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────┐
│  MCP Tool Call:                                 │
│  generate_snap_blocks(                          │
│    description="when space pressed,             │
│                 change y by 50,                 │
│                 wait 0.3 seconds,               │
│                 change y by -50",               │
│    complexity="beginner"                        │
│  )                                              │
└────────────────┬────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────┐
│  Lightweight Parser:                            │
│  - Extracts: trigger="key_press", key="space"   │
│  - Extracts: action="jump", height=50           │
│  - Pattern matching only (no NLP lib)           │
└────────────────┬────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────┐
│  Block Generator: Creates Snap! blocks          │
└─────────────────────────────────────────────────┘
```

### **Key Insight**

**Claude does the hard work:**
- Understanding ambiguous language
- Breaking down complex requests
- Inferring missing details
- Handling context and conversation

**MCP parser does simple work:**
- Pattern matching on structured input
- Extracting values (numbers, keys, colors)
- Validating domain-specific constraints
- No AI/ML needed!

---

## Comparison: Heavy vs Lightweight

| Aspect           | Heavy NLP (Draft)         | Lightweight (Recommended) |
|------------------|---------------------------|---------------------------|
| **Dependencies** | 500MB+ (spaCy models)     | 50MB (no NLP libs)        |
| **Startup Time** | 5-10 seconds              | <1 second                 |
| **RAM Usage**    | 500MB-1GB                 | <100MB                    |
| **Installation** | Complex (model downloads) | Simple (pip install)      |
| **Accuracy**     | 95% (but overkill)        | 90% (sufficient)          |
| **Maintenance**  | Update models             | Update patterns           |
| **With Claude**  | Redundant!                | Perfect fit               |

---

## When Would You Need Heavy NLP?

**Only if users type directly in terminal:**
```bash
# Ambiguous, conversational input
$ "I want the cat to do a little dance when I touch it"
```

**With Rovodev CLI/Claude, this becomes:**
```python
# Structured, clear input from Claude
generate_snap_blocks(
    description="when sprite clicked, repeat 4 times: next costume and wait 0.2 seconds",
    complexity="beginner"
)
```

---

## Recommendation

### ✅ **Use Lightweight Approach**

**Reasons:**
1. You're using Claude Code (it handles NLP)
2. 90% accuracy is sufficient (Claude fills gaps)
3. Fast, simple, maintainable
4. No giant dependencies
5. Works offline

### ❌ **Skip Heavy NLP Libraries**

**Unless:**
- You want standalone terminal app (no LLM)
- Users type freeform text directly
- Need to handle extremely ambiguous input

---

## Updated Requirements.txt

```txt
# MINIMAL DEPENDENCIES - Total ~50MB

# Core MCP
mcp>=1.0.0
fastmcp>=0.1.0

# WebSocket Bridge
websockets>=12.0
aiohttp>=3.9.0

# Data Validation
pydantic>=2.0.0
jsonschema>=4.0.0

# Security
cryptography>=41.0.0

# Utilities
python-dotenv>=1.0.0
rich>=13.0.0  # Nice terminal output (optional)

# Dev/Test (optional)
pytest>=7.4.0
black>=23.0.0
```

**Total installation time: <2 minutes instead of 10+ minutes**

---

## Summary

Your instinct was correct! Heavy NLP libraries are unnecessary because:

1. **Claude does the NLP** - It understands natural language and formats structured requests
2. **Parser is domain-specific** - Just needs Snap! programming vocabulary
3. **Pattern matching suffices** - Regex patterns cover 90% of cases
4. **Lightweight = Better UX** - Fast startup, small footprint

The refined parser is **domain-aware** (knows Snap! programming), not **language-aware** (doesn't need general NLP). This is the sweet spot for an MCP server working with an LLM.