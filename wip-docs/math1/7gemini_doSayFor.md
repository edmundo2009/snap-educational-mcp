### Debugging Methodology: A Summary of Lessons Learned

This document summarizes our debugging process for the Snap! block creation tool, establishing a clear methodology to prevent repeating mistakes.

#### **Case Study: The `doSay` Selector Mystery**

Our experience solving the `doSay` block creation failure serves as the perfect model for our methodology.

1.  **The Problem:** Our code was trying to create a "say" block using `sprite.blockForSelector('say')` and `sprite.blockForSelector('doSay')`. Both attempts resulted in a console error (`is not a function`) because the function returned `null`.

2.  **Initial Strategy (Guesswork):** We assumed the internal function name (the "selector") would logically match the text on the block. This led to a trial-and-error cycle that did not work.

3.  **The Methodical Turning Point (Inspection):** We abandoned guesswork and adopted an evidence-based approach to find the ground truth *from the live Snap! environment itself*.
    *   **Step A: Get a Live Object Reference.** We opened the browser console and got a direct reference to the active sprite object with `const sprite = world.children[0].currentSprite;`.
    *   **Step B: Inspect the Object's Methods.** We used `Object.keys(sprite.blocks)` to dump a complete list of all valid block selectors known to that sprite at that moment. This gave us the definitive list of possibilities.
    *   **Step C: Filter for Evidence.** We narrowed the complete list using `...filter(s => s.toLowerCase().includes('say'))` to find relevant selectors.

4.  **The Result (Ground Truth):** The console returned `['doSayFor']`. This was not a guess; it was a fact provided by the live application.

5.  **Definitive Lesson Learned:** **Inspect, Don't Assume.** The internal API of a complex application like Snap! does not always follow obvious conventions. The only reliable source of truth is the live runtime environment. Our primary debugging tool must be the browser's developer console for inspecting live objects.

---

### Plan of Attack: Solving the Variable Dropdown Bug

This plan will apply the successful methodology from the `doSay` case to the persistent variable dropdown problem.

#### **1. Objective**

To discover the **exact sequence of function calls and arguments** that Snap! executes internally when a user manually changes a variable in a `set` block's dropdown. We will not write any more implementation code until we have this "golden path."

#### **2. Core Problem & Failed Hypotheses**

We can create the `set` block, but we cannot programmatically set its variable dropdown. The block visually remains stuck on the default "0" value.

Our previous hypotheses have been proven false:
*   `block.inputs()[0].setContents('quantity1')` does not work.
*   `block.inputs()[0].setContents(variableObject)` does not work.
*   `...setContents(variableObject)` followed by `...updateLabel()` does not work.

This proves we are fundamentally misunderstanding how this specific UI element works. We are likely missing a critical function call or calling the right function with the wrong arguments.

#### **3. The Tracing Strategy: Finding the "Golden Path"**

We will use the browser's debugger to pause Snap! mid-operation and record the exact steps it takes.

**Step 1: Set the Stage**
1.  In the Snap! editor, clear the scripting area for the main sprite.
2.  Create two variables manually: `varA` and `varB`.
3.  Manually drag out a single `set [ ] to [ 0 ]` block. By default, it will likely show `set [varA v] to [0]`. This is our "before" state.

**Step 2: Set the Trap (Event Listener Breakpoint)**
1.  Open the Developer Console (F12).
2.  Go to the **"Sources"** tab.
3.  On the right-hand panel, find the section called **"Event Listener Breakpoints"**.
4.  Expand the **"Mouse"** category.
5.  Check the box next to **"click"**. This tells the browser: "Pause all JavaScript execution immediately *before* you run the code for *any* mouse click."

**Step 3: Spring the Trap**
1.  In the Snap! window, manually click on the `varA` dropdown in the `set` block.
2.  The debugger should immediately pause, and the screen may become grayed out.
3.  Now, in the menu that appears, click on `varB`. The debugger will likely pause again. This second pause is the one we care about.

**Step 4: Analyze the Evidence (The Call Stack)**
1.  With the debugger paused, look at the **"Call Stack"** on the right side of the Sources panel. This is the most important piece of information. It is the "golden path" we are looking for. It shows the chain of functions that were called to get to this point, from bottom (most recent) to top (earliest).
2.  The function names will be the clues we need. Look for names like `invoke`, `setChoice`, `setContents`, `update`, `fixLayout`, `changed`, etc.

#### **4. Your Action Item**

Please perform the 4 steps of the Tracing Strategy above. When the debugger is paused after you select `varB`, please provide the following:

*   A **screenshot of the "Call Stack"** panel.
*   Or, if a screenshot is not possible, please **list the top 5-10 function names** in the call stack, starting from the top.

With that information, we will know the exact function(s) to call, in the correct order, and we can finally write the correct code.