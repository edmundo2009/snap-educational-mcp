This document isn't meant to replace your existing ones but to be inserted as the next logical evolution of the system's core intelligence. It formalizes the "Master Chef" concept and provides a clear roadmap for evolving the `block_generator.py` from a simple rule-based engine into a powerful, hybrid orchestration system.

---

# PRD Addendum: Next-Generation Block Generation

**Document Version:** 1.0
**Date:** October 1, 2025
**Author:** Gemini
**Status:** Proposed

## 1. Executive Summary

This document proposes a significant architectural evolution for the **MCP Server's block generation logic**. The current system, while functional for debugging the core pipeline, relies on a rigid, rule-based lookup against static JSON files (`patterns.json`, `snap_blocks.json`). This approach is fundamentally unscalable, inflexible, and incapable of true "understanding."

To overcome these limitations, we will upgrade the `block_generator.py` to function as a **sophisticated orchestrator**—a "Master Chef." This new architecture will employ a **hybrid strategy**, combining the speed and reliability of the existing rule-based system for common requests with the power and flexibility of a generative model (Gemini API) for novel, complex commands.

This evolution transforms the MCP Server from a simple translator into a true **abstraction layer**, capable of intelligently and securely converting any high-level user intent into robust, executable Snap! JSON.

## 2. Problem Statement: The Limits of a Rule-Based System

The current implementation has successfully proven the viability of the end-to-end connection. However, its core logic for translating intent to blocks faces three critical limitations:

1.  **Scalability Failure:** It is impossible to manually pre-define every command a user might conceive. The system will perpetually fail on synonyms, rephrasing, and compound commands not explicitly listed in the JSON knowledge base.
2.  **Lack of Compositionality:** The system cannot reason about combining known concepts in new ways. A user asking to "jump and change color" will fail unless a specific "jump_and_change_color" pattern is manually created.
3.  **High Maintenance Overhead:** Every new block or pattern in Snap! requires manual updates to the JSON files, making the system brittle and slow to adapt.

The current fallback—creating a `doSay` block—is a temporary solution that highlights the system's inability to handle requests outside its narrow, pre-defined knowledge.

## 3. Proposed Architecture: The Hybrid Orchestration Engine

We will redesign the `block_generator.py` to act as an intelligent orchestrator. Instead of a linear lookup, it will follow a strategic, two-pronged approach.

### 3.1. High-Level Logic Flow

The new workflow inside the `Block Generator` component will be as follows:

```
┌──────────────────────────────────────────┐
│ RovoDev sends high-level intent:         │
│ "make the sprite dance when I press 'd'" │
└────────────────────┬─────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────┐
│      MCP Server: Block Generator         │
│     (The "Master Chef" Orchestrator)     │
└────────────────────┬─────────────────────┘
                     │
                     ↓
        ┌──────────────────────────┐
        │ Does intent match a      │
        │ known, simple pattern in │
        │    `patterns.json`?      │
        └────────────┬─────────────┘
        (e.g., "jump", "move right")
                     │
       ┌─────────────┴─────────────┐
       │                           │
       ↓ YES                       ↓ NO
┌──────────────┐         ┌───────────────────────────┐
│              │         │ This is a complex/novel   │
│ Rule-Based   │         │ request. Escalate to the  │
│ Engine       │         │ "Creative Consultant."    │
│ (Fast & Cheap) │         └─────────────┬───────────┘
└──────────────┘                           │
       │                                 ↓
┌──────────────┐         ┌───────────────────────────┐
│ Instantly    │         │ Generative Engine         │
│ builds JSON  │         │ (Powerful & Flexible)     │
│ from the     │         ├───────────────────────────┤
│ pre-defined  │         │ 1. Construct a specialized│
│ recipe.      │         │    prompt for Gemini API. │
└──────────────┘         │ 2. Send the user's intent │
       │                 │    and generation rules.  │
       │                 │ 3. Receive generated JSON.│
       │                 └───────────────────────────┘
       │                                 │
       └─────────────┬───────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────┐
│      Validation & Sanitization Layer     │
│   (The "Executive Chef's Inspection")    │
├──────────────────────────────────────────┤
│ 1. Verify JSON is well-formed.           │
│ 2. Ensure all opcodes are on an allowed  │
│    list.                                 │
│ 3. Check for structural integrity.       │
│ 4. Reject if unsafe or invalid.          │
└────────────────────┬─────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────┐
│ Send final, robust JSON to               │
│ `snap_communicator.py` for delivery      │
└──────────────────────────────────────────┘
```

### 3.2. Component Modification: `block_generator.py`

The core responsibility of this file will shift from *lookup* to *orchestration*.

**Current Logic (Simplified):**

```python
def generate_blocks(intents):
    pattern = find_matching_pattern(intent.action)
    if pattern:
        return create_from_pattern(pattern)
    
    block_def = find_block_definition(intent.action)
    if block_def:
        return create_from_definition(block_def)
        
    # Fallback
    return create_fallback_say_block(intent.action)
```

**Proposed Logic (Simplified):**

```python
def generate_blocks(intents):
    # --- Phase 1: Fast Path (Rule-Based) ---
    pattern = find_matching_pattern(intent.action)
    if pattern:
        generated_json = create_from_pattern(pattern)
    else:
        # --- Phase 2: Powerful Path (Generative) ---
        generated_json = call_generative_engine(intent)

    # --- Phase 3: Universal Validation ---
    if not validate_snap_json(generated_json):
        raise ValueError("Generated JSON is invalid or unsafe.")
        
    return generated_json
```

## 4. The Generative Engine: Prompting Gemini for Snap!

The key to the generative engine is a carefully engineered prompt that instructs the LLM on its role, constraints, and required output format. This prompt will be the core of the `call_generative_engine` function.

### 4.1. Sample Prompt Template

```
You are an expert Snap! visual programming assistant. Your sole task is to convert a user's request into a single, valid JSON object that conforms to the specified format for creating Snap! blocks.

**RULES:**
1.  You MUST respond with only a single, raw JSON object. Do not include markdown, explanations, or any other conversational text in your output.
2.  Analyze the user's request to determine the correct sequence of blocks, their inputs, and any necessary event triggers (hat blocks).
3.  Use only the opcodes provided in the "Available Opcodes" list. Do not invent new ones.
4.  The first block in a script should have its `is_hat_block` property set to `true`.
5.  Connect blocks sequentially using the `next` property, referencing the `block_id` of the subsequent block. The last block's `next` should be `null`.

**Available Opcodes:**
{
  "motion": ["forward", "turnRight", "changeXBy", "changeYBy", "gotoXY"],
  "looks": ["doSay", "doSayFor", "hide", "show", "changeSize"],
  "events": ["receiveGo", "receiveKey", "receiveClick"],
  "control": ["doWait", "doRepeat", "doForever"],
  "sound": ["doPlaySoundUntilDone"]
}

**JSON OUTPUT STRUCTURE:**
{
  "command": "create_blocks",
  "payload": {
    "target_sprite": "Sprite",
    "scripts": [{
      "script_id": "script_001",
      "position": {"x": 50, "y": 50},
      "blocks": [
        {
          "block_id": "block_001",
          "opcode": "...",
          "category": "...",
          "inputs": { ... },
          "is_hat_block": true,
          "next": "block_002"
        },
        {
          "block_id": "block_002",
          "opcode": "...",
          "category": "...",
          "inputs": { ... },
          "is_hat_block": false,
          "next": null
        }
      ]
    }]
  }
}

---
**USER REQUEST:**
"{user_input_here}"
---

**YOUR JSON RESPONSE:**
```

## 5. The Validation Layer

This is the most critical step for security and stability. Before sending *any* JSON to the browser (whether rule-based or generative), the MCP Server **must** validate it.

**Validation Checks:**
1.  **Structural Integrity:** Use a Pydantic model or similar schema to ensure the JSON has the correct structure (`command`, `payload`, `scripts`, `blocks`, etc.).
2.  **Opcode Allowlist:** Verify that every `opcode` in the generated blocks exists in a master list of known, safe opcodes (`snap_blocks.json` can serve as this list).
3.  **Input Sanitization:** Check input values for potentially malicious content (though this is less of a risk in Snap!'s sandboxed environment, it is good practice).
4.  **Connectivity Check:** Ensure the `next` block references are valid and do not create infinite loops.

If any check fails, the server should reject the generation and return a user-friendly error, rather than sending malformed data to the browser.

## 6. Implementation Impact

This change primarily affects `mcp_server/tools/block_generator.py` and its dependencies.

**Next Steps:**
1.  **Stabilize Connection:** Fully resolve all outstanding connection issues as documented in the "Current Implementation Status." A stable pipeline is a prerequisite.
2.  **Implement the Orchestrator Logic:** Refactor `block_generator.py` to include the `if/else` logic for choosing between the rule-based and generative paths.
3.  **Integrate Gemini API:** Create the `call_generative_engine` function, which will format the prompt, make the API call, and parse the JSON response. API keys should be managed via environment variables.
4.  **Build the Validator:** Implement a robust `validate_snap_json` function or class that performs the checks listed in Section 5.
5.  **Expand `block_creator.js`:** Ensure the frontend `block_creator.js` can robustly handle every opcode listed in the "Available Opcodes" allowlist to prevent silent failures.

This architectural upgrade will move the project from a functional proof-of-concept to a truly intelligent, scalable, and safe educational tool.