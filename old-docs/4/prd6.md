# PRD Addendum: Next-Generation Block Generation - Updated to Reflect Implemented Architecture

**Document Version:** 2.0
**Date:** October 2, 2025
**Status:** Implemented

## 1. Executive Summary

This document details the architecture of the **MCP Server's block generation logic**. The initial prototype, which relied on a rigid, rule-based lookup, has been evolved into a sophisticated **hybrid orchestration engine**. This engine, nicknamed the "Master Chef," resides in `block_generator.py`.

The new architecture combines the speed and reliability of an enhanced rule-based system (for common requests) with the power and flexibility of a generative model (the Gemini API) for novel, complex commands. Key production-ready features such as an LRU cache, robust validation, retry logic, and cost controls have been implemented.

This evolution transforms the MCP Server from a simple translator into a resilient, intelligent, and secure abstraction layer, capable of converting a wide range of user intents into executable Snap! JSON.

## 2. Problem Statement: The Limits of a Rule-Based System

The initial implementation proved the viability of the end-to-end connection but was constrained by its logic, which faced three critical limitations:

1.  **Scalability Failure:** Manually defining every possible user command is impossible, leading to failures on synonyms and rephrasing.
2.  **Lack of Compositionality:** The system could not combine known concepts in new ways (e.g., "jump and change color") without a pre-defined pattern.
3.  **High Maintenance Overhead:** The knowledge base required constant manual updates.

## 3. Implemented Architecture: The Hybrid Orchestration Engine

The `block_generator.py` now functions as an intelligent orchestrator. It follows a multi-stage process designed for efficiency, robustness, and intelligence.

### 3.1. Detailed Logic Flow

The implemented workflow is a multi-step pipeline that prioritizes speed and accuracy, only escalating to the powerful generative model when necessary.

```
┌──────────────────────────────────────────┐
│ User Input:                              │
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
        │ Check LRU Cache for a    │
        │ direct match of the      │
        │      user description?   │
        └────────────┬─────────────┘
                     │
       ┌─────────────┴─────────────┐
       │                           │
       ↓ YES                       ↓ NO
┌──────────────┐         ┌───────────────────────────┐
│              │         │ Find pattern with Exact   │
│ Return       │         │ or Fuzzy Match            │
│ Cached JSON  │         │   (threshold >= 0.6)?     │
│ (Fastest)    │         └───────────┬───────────────┘
└──────────────┘                     |
       │                   ┌─────────┴─────────┐
       │                   |                   |
       |                   ↓ YES               ↓ NO
       │      ┌─────────────────┐ ┌───────────────────────────┐
       │      │ Rule-Based      │ │ Generative Engine         │
       │      │ Engine          │ │ (Powerful & Flexible)     │
       │      ├─────────────────┤ ├───────────────────────────┤
       │      │ - Build         │ │ 1. Select Model(Flash/Pro) │
       │      │  `BlockSequence`│ │    based on complexity.   │
       │      │   from pattern. │ │ 2. Construct Prompt with  │
       │      │ - Apply params  │ │    few-shot examples.     │
       │      │   from intent.  │ │ 3. Call Gemini API (with  │
       │      └─────────────────┘ │    retries & cost tracking) │
       │              │           │ 4. Extract & Parse JSON.    │
       │              │           └───────────┬───────────────┘
       │              │                       |
       │              │           ┌───────────┴───────────────┐
       │              │           │ Validation Loop           │
       │              │           ├───────────────────────────┤
       │              │           │ Pass Validation?          │
       │              │           │(Pydantic,Opcodes,Connect) │
       │              │           └───────────┬───────────────┘
       │              │           ┌───────────┴───────────────┐
       │              │           | YES                       | NO
       │              │           ↓                           ↓
       │              │      (Continue)          ┌──────────────────────┐
       │              │                          │ Retry? (if < max)    │
       │              │                          │  YES → Loop to Step 3│
       │              │                          │  NO  → Create Error  │
       │              │                          │        Fallback Block│
       │              └───────────┬──────────────└──────────────────────┘
       │                          |
       └──────────────┬───────────┘
                      │
                      ↓
       ┌─────────────────────────────────┐
       │ Format to Final Snap! JSON      │
       │ (If not already formatted)      │
       └─────────────────┬───────────────┘
                         │
                         ↓
┌──────────────────────────────────────────┐
│ Store in Cache (if generative & valid)   │
│ `move_to_end` or `popitem` in OrderedDict│
└────────────────────┬─────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────┐
│ Send final, robust JSON to               │
│ `snap_communicator.py` for delivery      │
└──────────────────────────────────────────┘
```

### 3.2. Component Modification: `block_generator.py`

The logic has been fully implemented, moving far beyond the initial proposal.

**Initial Proposal (Simplified):**
```python
def generate_blocks(intents):
    if pattern:
        # Rule-based
    else:
        # Generative
    # Validate
```

**Final Implemented Logic:**
```python
def generate_snap_json(intent, user_description):
    # Phase 1: Cache Check
    cached = _check_cache(user_description)
    if cached: return cached

    # Phase 2: Rule-Based Engine (with Fuzzy Matching)
    pattern = _find_matching_pattern(intent.action)
    if pattern:
        sequence = _create_from_pattern(pattern, intent)
        generated_json = format_for_snap(sequence, "Sprite")
    else:
        # Phase 3: Generative Engine (with Internal Validation Loop)
        generated_json = _call_generative_engine(user_description)

    # Phase 4: Caching
    if not generated_json.get("payload", {}).get("error"):
        _store_cache(user_description, generated_json)
        
    return generated_json
```

## 4. The Generative Engine: Production-Ready Prompting

The generative engine's core is a highly-engineered prompt that provides the LLM with clear rules, categorized opcode lists, and crucial few-shot examples of complete, valid JSON output. This significantly improves the reliability and correctness of the generated code.

## 5. The Validation Layer: The "Executive Chef's Inspection"

The validation layer, implemented in `validators.py`, is the critical security and stability gatekeeper. It is invoked **before any generated JSON is cached or returned**, preventing malformed or disallowed data from propagating.

**Implemented Validation Checks:**
1.  **Structural Integrity:** A full hierarchy of `Pydantic` models (`SnapJSONSchema`, `PayloadSchema`, `ScriptSchema`, `SnapBlockSchema`) enforces the correct JSON structure, types, and fields.
2.  **Opcode Allowlist:** Verifies every `opcode` against a master set derived directly from `snap_blocks.json`, ensuring only known, safe blocks are created.
3.  **Connectivity Check:** Ensures all `next` block references are valid and point to existing `block_id`s within the same script, preventing broken or orphaned chains.
4.  **Structural Rules:** Enforces that the first block in any script has `is_hat_block: true` and that all `block_id`s are unique.

## 6. Implementation Status & Next Steps

The architectural upgrade is **complete and implemented**. The system has been successfully evolved from a functional proof-of-concept to an intelligent, scalable, and safe educational tool.

### Key Implemented Features:
*   **Complete Hybrid Logic**: The full cache -> rule-based -> generative orchestration flow is implemented.
*   **Advanced Pattern Matching**: O(1) direct lookup is combined with a fuzzy matching fallback.
*   **Production-Grade Generative Engine**: Features model selection, advanced prompting, cost controls, and a validation-driven retry loop.
*   **Robust Caching**: A true LRU cache (`OrderedDict`) is in place to improve performance and reduce costs.
*   **Comprehensive Validation**: Pydantic schemas and logical checks secure the entire generation pipeline.
*   **Resilient Error Handling**: Generation failures now produce a user-visible error block in Snap! instead of failing silently.
*   **Full Observability**: The system logs key events and tracks performance metrics for hits, misses, and costs.

### Next Steps:
The core intelligence is stable. Future work should focus on hardening the surrounding infrastructure and expanding capabilities.
1.  **Implement Rate Limiting**: Replace the simple API call counter with a more robust library (e.g., `token-bucket`) to manage costs and prevent abuse in a multi-user environment.
2.  **Introduce a Persistent Cache**: The current LRU cache is in-memory and resets on restart. For production, this should be replaced with a persistent solution like **Redis** or a file-based cache to retain performance gains across server sessions.
3.  **Conduct Rigorous End-to-End Testing**: Create a test suite that explicitly targets the rule-based path, the generative path, the cache, and various failure modes to ensure long-term stability.
4.  **Expand the Knowledge Base**: Systematically add more high-quality patterns to `patterns.json` and blocks to `snap_blocks.json` to increase the hit rate of the faster, cheaper rule-based engine.