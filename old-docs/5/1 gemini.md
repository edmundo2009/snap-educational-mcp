# high-level workflow specifically designed for testing and hardening the **rule-based pipeline only**.

### **High-Level Workflow for Rule-Based System Hardening**

**Objective:** To ensure the path from user input -> intent parsing -> pattern matching -> JSON generation is flawless and covers the vast majority of common, beginner-level Snap! commands.

**Scope:** This workflow intentionally **ignores** the generative (`_call_generative_engine`) and caching (`_check_cache`, `_store_cache`) components. We will temporarily treat the rule-based engine as the *only* engine.

---

#### **Phase 1: Knowledge Base Audit & Expansion (The "Cookbook" Review)**

The strength of a rule-based system is its knowledge base. This is the most critical phase.

1.  **Review Existing Patterns (`patterns.json`):**
    *   **Trigger Audit:** For each pattern (e.g., `jump`), are the `triggers` comprehensive? Brainstorm all common synonyms a child might use ("leap", "hop", "bounce up and down").
    *   **Block Sequence Audit:** Is the sequence of blocks for each pattern correct and logical? Does `jump` have the correct `changeYBy`, `doWait`, `changeYBy` sequence?
    *   **Parameter Sanity Check:** Do the default input values (e.g., `DX: 10`) make sense for a beginner?

2.  **Identify and Define Core Beginner Patterns:**
    *   Brainstorm the top 20 actions a beginner would learn. Create a checklist.
    *   **Movement:** `move left`, `move right`, `move up`, `move down`, `go to center`, `turn 90 degrees`.
    *   **Looks:** `say hello`, `think hmm`, `grow`, `shrink`, `reset size`, `show`, `hide`, `next costume`.
    *   **Sound:** `play pop sound`.
    *   **Control:** `wait 1 second`, `repeat 4 times`.
    *   **Action:** For any missing actions on your checklist, create a new, well-defined pattern in `patterns.json`.

3.  **Cross-Reference with `snap_blocks.json`:**
    *   Ensure every single `opcode` used in `patterns.json` has a corresponding, correctly named entry in `snap_blocks.json`. This guarantees the "ingredients" for your "recipes" exist.

**Goal of Phase 1:** A comprehensive and accurate `patterns.json` that covers the vast majority of simple, single-concept actions.

---

#### **Phase 2: Intent Parser Unit Testing (The "Translator" Check)**

Now, ensure the user's language is correctly translated into a structured `ParsedIntent` that the generator can understand.

1.  **Isolate the Parser:** Write a dedicated test script that only calls `SnapIntentParser.parse()`.
2.  **Create Test Cases for Triggers:**
    *   `"when the green flag is clicked"` -> Should produce an intent with `trigger='flag_click'`.
    *   `"when the space key is pressed"` -> Should produce `trigger='key_press'` and `parameters={'key': 'space'}`.
    *   `"when I click the sprite"` -> Should produce `trigger='sprite_click'`.
3.  **Create Test Cases for Actions & Parameters:**
    *   `"move left 25 steps"` -> Should produce `action='move left'` and `parameters={'steps': 25}`.
    *   `"turn right 90 degrees"` -> Should produce `action='turn right'` and `parameters={'degrees': 90}`.
    *   `"say hello for 5 seconds"` -> Should produce `action='say hello'` and `parameters={'message': 'hello', 'seconds': 5}` (or similar, depending on your parser's detail).

**Goal of Phase 2:** High confidence that the parser can reliably extract the correct action, trigger, and parameters from user commands.

---

#### **Phase 3: End-to-End Rule-Based Pipeline Testing**

This phase tests the entire chain, from a sentence to a final, validated JSON object.

1.  **Temporarily Disable the Generative Fallback:** In `generate_snap_json`, comment out the `else` block containing the call to `_call_generative_engine`. If a pattern is not found, it should fail explicitly for this test.

    ```python
    # In block_generator.py
    def generate_snap_json(self, intent: ParsedIntent, user_description: str) -> dict:
        # ... (cache check can be ignored/commented)
        pattern = self._find_matching_pattern(intent.action)
        if pattern:
            # ... (proceed with rule-based generation)
            return generated_json
        else:
            # For this test, we want to know if the rule-based engine failed.
            raise ValueError(f"No rule-based pattern found for action: '{intent.action}'")
    ```

2.  **Create a Test Suite:** Build a simple test runner or spreadsheet with the following columns:
    *   **Input Sentence:** A natural language command.
    *   **Expected Pattern:** The pattern that *should* be matched (e.g., `jump`).
    *   **Expected Opcodes (in order):** The list of opcodes the final JSON should contain (e.g., `['receiveGo', 'changeYBy', 'doWait', 'changeYBy']`).
    *   **Test Result:** PASS / FAIL.

3.  **Execute Test Cases:** Run each sentence through the entire pipeline:
    *   `parser` -> `generator` -> `formatter` -> `validator`.
    *   The test **PASSES** only if a pattern is found AND the final JSON passes our robust `validate_snap_json` function.

4.  **Populate the Test Suite with Diverse Scenarios:**
    *   **Basic Actions:** "spin", "jump", "move right", "change colors".
    *   **Actions with Parameters:** "move left 50 steps", "turn 180 degrees", "wait 3 seconds".
    *   **Actions with Triggers:** "when space is pressed jump", "when the flag is clicked, say hello".
    *   **Synonym Tests:** "hop", "leap" (should both trigger the `jump` pattern).

#### **The Test-Driven Refinement Loop**

This workflow creates a powerful feedback loop for improving your rule-based system:

```
┌───────────────────────────────┐
│ 1. Run a Test Case from       │
│    the Suite (Phase 3)        │
└───────────────┬───────────────┘
                │
                ↓
┌───────────────┴───────────────┐
│ Did it FAIL?                  │
└───────────────┬───────────────┘
                │
     ┌──────────┴──────────┐
     │ YES                 │ NO
     ↓                     ↓
┌────┴─────────┐   ┌───────┴──────┐
│ 2. Diagnose  │   │ Great! Move  │
│    the Cause │   │ to next test.│
└────┬─────────┘   └──────────────┘
     │
┌────┴───────────────────────────────────────────┐
│ - Is the parser wrong? (Fix in Phase 2)        │
│ - Is the trigger missing? (Fix in Phase 1)     │
│ - Is the block sequence wrong? (Fix in Phase 1)│
└────────────────────────────────────────────────┘
```

By following this workflow, you will methodically build a highly reliable and comprehensive rule-based engine. When you are satisfied with its performance, you can confidently re-enable the generative fallback, knowing it will only be used for truly exceptional cases.