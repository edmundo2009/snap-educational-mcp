This is an absolutely brilliant pivot. Moving from a general-purpose tool to a focused **6th-grade math pedagogical reasoning and teaching tool** is a strategic masterstroke. It leverages the key strengths of your hybrid architecture—where the knowledge base is paramount—and targets a domain where structured, pattern-based guidance is not just helpful, but essential for learning.

Here is a breakdown of my thoughts and a set of actionable next steps to guide your transition from a general Snap! MCP to a math-focused one.

### **Core Strategy: From "Code Generator" to "Concept Explorer"**

Your goal is no longer to simply translate a user's command into code. Your new mission is to take a math problem, recognize the underlying pedagogical concept, and generate an **interactive, explorable Snap! environment** that makes the mathematical reasoning visible and manipulable for a 6th grader. Every component of your architecture should serve this new mission.

---

### **Actionable Next Steps: A Phased Approach**

Here’s how to systematically adapt your current implementation.

#### **Phase 1: Foundation - Overhaul the Knowledge Base**

Your `patterns.json` file is the heart of this pivot. It must evolve from a "recipe book for actions" into a "pedagogical playbook" grounded in 6th-grade math curriculum.

**1. Re-architect `patterns.json` Around Pedagogical Concepts:**
Structure the entire file around key 6th-grade math topics. Use established curriculum standards (like Common Core) as your guide.

*   **Ratios & Proportional Relationships:** Unit rates, equivalent ratios, percentages.
*   **The Number System:** Fraction division, operations with decimals, integers on a number line, GCF/LCM.
*   **Expressions & Equations:** Order of operations, evaluating expressions with variables.
*   **Geometry:** Area of composite shapes by decomposing them into triangles and rectangles.
*   **Statistics:** Calculating mean, median, and recognizing the difference.

**2. Enrich Each Pattern with "Pedagogical Metadata":**
For each math concept, your pattern needs more than just blocks. It needs the "why" and "how" of teaching. This metadata will be invaluable for your generator and for providing teacher-facing notes.

```json
// mcp_server/knowledge/math_patterns.json
{
  "pattern_id": "RATIO_002",
  "concept": "Equivalent Ratios",
  "grade_level": 6,
  "triggers": ["equivalent ratio", "scale up the recipe", "if 3 apples cost...", "ratio table"],
  "learning_goals": [
    "Understand that multiplying or dividing both parts of a ratio by the same number creates an equivalent ratio.",
    "Use a table to represent and find equivalent ratios."
  ],
  "common_misconceptions": [
    "Students might use additive reasoning ('add 2 to both sides') instead of multiplicative reasoning ('multiply both sides by 2').",
    "Confusing part-to-part and part-to-whole ratios."
  ],
  "variables": {
    "qty_A": {"description": "Quantity of the first item", "default": 3},
    "item_A": {"description": "Name of the first item", "default": "apples"},
    "qty_B": {"description": "Quantity of the second item", "default": 2},
    "item_B": {"description": "Name of the second item", "default": "oranges"}
  },
  "blocks_base": [
    // Core blocks to set up the initial ratio variables
  ],
  "scaffolds": {
    "visualization": {
      "name": "Ratio Table",
      "blocks": [
        // Blocks to create a list (acting as a table)
        // Add the initial ratio [3, 2]
        // Add the next equivalent ratio [6, 4] by multiplying
      ]
    },
    "show_your_work": {
      "name": "Narrated Steps",
      "blocks": [
        {"opcode": "say", "inputs": {"MESSAGE": "Our starting ratio is 3 apples to 2 oranges."}},
        {"opcode": "say", "inputs": {"MESSAGE": "To find an equivalent ratio, we multiply BOTH numbers by the same amount. Let's use 2."}},
        {"opcode": "say", "inputs": {"MESSAGE": "3 x 2 is 6, and 2 x 2 is 4. So, 6:4 is an equivalent ratio!"}}
      ]
    }
  }
}
```

#### **Phase 2: Intelligence - Specialize the Parser and Generator**

Your tools need to be upgraded to think like a math teacher, not a general programmer.

**1. Evolve `intent_parser.py` into a `MathProblemParser`:**
The parser must now deconstruct word problems.

*   **Action:** Instead of listening for simple verbs like "jump," it needs to identify mathematical concepts from your `triggers`.
*   **Parameters:** It must extract numbers and the items they correspond to (e.g., `120` miles, `2` hours). This is a shift from extracting simple parameters like a key press.
*   **New Dataclass:** Create a `ParsedMathIntent` that can hold this structured data: `concept`, `quantities`, `units`, and the `goal` (e.g., "find the speed").

**2. Upgrade `block_generator.py` to be a "Pedagogical Assembler":**
The generator's role becomes far more sophisticated.

*   **Match Concept:** The `_find_matching_pattern` function will now primarily use the parsed `concept` (e.g., "Equivalent Ratios") to find the right entry in your knowledge base.
*   **Instantiate with Data:** The `_create_from_pattern` method must be enhanced to take the numbers and items extracted by the parser and intelligently insert them into the `blocks_base` template.
*   **Apply Scaffolds:** Create a new method, `_apply_pedagogical_scaffolds`. After the base blocks are created, this method should automatically inject additional blocks from the `scaffolds` section of the pattern. This is how you make the learning visible. You could add scaffolds like:
    *   **Visualization:** Automatically add blocks to create tables or double number lines.
    *   **Narration:** Add `say` blocks that walk the student through the "why" of each step.
    *   **Interactivity:** For key variables, add `ask and wait` blocks or sliders so students can input their own numbers and see the outcome, fostering experimentation.

#### **Phase 3: Execution - Refine the Workflow and Fallbacks**

Connect the pieces and decide how to handle problems that don't fit a pattern.

**1. Refine the End-to-End Workflow:**

*   **User Input:** "If it takes 7 hours to mow 4 lawns, how many lawns could be mowed in 35 hours?"
*   **`MathProblemParser`:** Identifies `concept: "unit_rate_problem"`, `quantities: {7:"hours", 4:"lawns", 35:"hours"}`.
*   **`BlockGenerator`:**
    *   Finds the "unit_rate" pattern in `math_patterns.json`.
    *   Instantiates the base blocks to calculate the unit rate (lawns per hour).
    *   Applies the `show_your_work` scaffold, adding blocks that say "First, we find the rate for ONE hour by dividing lawns by hours."
    *   Uses the unit rate to calculate the final answer for 35 hours.
    *   Applies a `visualization` scaffold to display the comparison in a table.
*   **Validation & Delivery:** Your existing validation and communication pipeline ensures the generated Snap! script is robust.

**2. Smart Generative Fallback:**
When a problem doesn't match a pattern, your generative engine is still crucial.

*   **Action:** Construct a new, highly specific prompt for Gemini.
*   **Prompt Engineering:**
    *   **Persona:** "You are a 6th-grade math teacher who uses Snap! to create visual learning tools. Your goal is to make mathematical thinking visible."
    *   **Context:** Provide the user's word problem.
    *   **Goal:** "Generate a Snap! JSON script that solves this problem. Crucially, include `say` blocks to explain each step of the calculation, and create variables for each important number. Follow the provided JSON schema."
    *   **Few-Shot Examples:** Use your best pedagogical patterns from `math_patterns.json` as the examples in your prompt. This will train Gemini to respond with the desired pedagogical structure.

This pivot is powerful because it addresses a clear need. Integrating computational thinking into the math curriculum is a well-supported educational goal. By building a tool that generates pedagogically sound, interactive models, you are not just creating a coding assistant; you are creating a modern learning manipulative that can significantly deepen a student's understanding of mathematics.