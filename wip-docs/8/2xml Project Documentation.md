
### Final Project Documentation & Handover

Here is the high-level documentation of the system we have built and the path forward.

#### Project Structure & Overview

The system is a three-tier architecture designed to allow a Python-based AI agent to programmatically control a Snap! IDE instance running in a user's browser.

1.  **Python Backend (MCP Server):**
    *   **`main.py`:** The main server application. It defines the AI tools (`@mcp.tool`), manages the server lifecycle, and contains the core business logic (e.g., parsing math problems).
    *   **`snap_communicator.py`:** A dedicated class (`SnapBridgeCommunicator`) that manages the WebSocket server, connection states, and provides high-level async methods for sending commands to the browser (e.g., `load_project_from_xml`).
    *   **`templates/project_template.xml`:** A Jinja2 template file that serves as a blueprint for a complete Snap! project.

2.  **WebSocket Bridge:**
    *   This is the communication layer, handled by the `websockets` library in Python and the native `WebSocket` API in the browser. It passes JSON messages between the server and the browser extension.

3.  **Browser Extension (Client):**
    *   **`bridge.js`:** The central nervous system of the client. The `SnapBridge` class listens for WebSocket messages, manages the connection lifecycle, and acts as a command router, dispatching tasks to other components.
    *   **`block_creator.js`:** A specialized class (`SnapBlockCreator`) that contains the functions which directly interact with the Snap! IDE's internal JavaScript API. Its primary job is now to handle the `loadProject` command.
    *   **`snap_api_wrapper.js`:** A utility class (`SnapAPIWrapper`) that provides safe, high-level access to the core Snap! objects like the `IDE_Morph` and the `Stage`, handling timing and initialization issues.

#### Dataflow of the XML Workflow

1.  **Agent Call (Python):** The LLM agent calls the `generate_math_blocks` tool in `main.py` with a word problem.
2.  **Parsing (Python):** `main.py` parses the problem to extract key numbers and identifies the problem type.
3.  **XML Generation (Python):** It populates a data dictionary and uses Jinja2 to render the `project_template.xml` into a complete XML string.
4.  **WebSocket Send (Python):** `main.py` calls the `load_project_from_xml` method in `snap_communicator.py`, which packages the XML string into a JSON command (`{'command': 'load_project', ...}`) and sends it over the WebSocket.
5.  **Command Reception (JS):** The `WebSocketClient` receives the message and passes it to `bridge.js`.
6.  **Command Routing (JS):** `bridge.js`'s `executeCommand` function sees the `load_project` command and calls the corresponding method in `block_creator.js`.
7.  **Snap! API Call (JS):** `block_creator.js`'s `loadProject` function calls the single, powerful internal Snap! function: `ide.openProjectString(xml)`.
8.  **Project Render (Snap!):** The Snap! IDE's native importer takes over, destroying the old project and flawlessly rendering the new one from the XML.
9.  **Success Response:** `block_creator.js` immediately returns a success message, which travels back up the chain to the Python server.

#### Summary of Changes for the XML Workflow

*   **`main.py`:**
    *   The `generate_math_blocks` tool was completely rewritten. It no longer uses the `SnapBlockGenerator`.
    *   It now directly calls a new helper function, `create_project_xml`, and uses a new communicator method, `load_project_from_xml`.
*   **`snap_communicator.py`:**
    *   Added the `jinja2` dependency.
    *   Added the `create_project_xml` helper function to render the template.
    *   Added the new `async def load_project_from_xml(...)` method to send the `load_project` command.
*   **`templates/project_template.xml` (New File):**
    *   This file was created to hold the structure of a complete Snap! project, with Jinja2 placeholders for dynamic content.
*   **`bridge.js`:**
    *   In the `executeCommand` switch statement, the `case 'create_blocks':` was removed.
    *   A new `case 'load_project':` was added to route the command to `this.blockCreator.loadProject`.
*   **`block_creator.js`:**
    *   This file was radically simplified. All old methods (`createBlocks`, `createScript`, `createSingleBlock`, etc.) were removed.
    *   It now contains a single primary method: `async loadProject(payload)`.

#### Redundant Code Going Forward

*   **`SnapBlockGenerator` Class (Python):** The logic within this class that converts math patterns into block-by-block JSON specifications is now entirely bypassed by the XML workflow for this tool. It may be useful for other tools, but it is not needed for generating full projects.
*   **Old `createBlocks`, `createScript`, etc. (JavaScript):** As noted, these functions in `block_creator.js` are obsolete and have been removed.

#### Next Steps: Generalizing from the POC

The current system is a highly successful POC. To evolve it into a true, general-purpose MCP tool, here are the key areas to focus on.

**1. Generalizing the Math Parser:**
*   The current `parse_math_problem` is hardcoded for a specific "unit rate" sentence structure.
*   **Next Step:** Evolve this into a more powerful parser. It should not just find numbers, but identify the core **mathematical concept** (e.g., proportions, area of a circle, solving for a variable). The output should be a structured object, like `{'concept': 'ratio', 'data': {'a1': 2, 'b1': 3, 'a2': 8}}`.

**2. Generalizing the XML Templates:**
*   You are correct: a single template will not work for all math problems.
*   **Next Step:** Create a library of XML templates in your `templates` folder, one for each major math concept you want to support (e.g., `ratio_problem.xml`, `geometry_area.xml`, `percent_change.xml`).
*   The `generate_math_blocks` tool will use the output from the generalized parser to select the correct template.
    ```python
    # Example of generalized logic
    parsed_problem = generalized_math_parser(problem_text)
    concept = parsed_problem['concept'] # e.g., 'ratio'
    data = parsed_problem['data']

    # This selects 'ratio_problem.xml' and passes the specific data it needs
    project_xml = create_project_xml_from_template(f"{concept}_problem.xml", data)
    ```

**3. Making Templates More General with Jinja2:**
*   Your templates can be made smarter. Instead of just filling in variables, you can use Jinja2's control structures.
*   **Example (Comparing Players):** Imagine a problem comparing stats for 2, 3, or 4 players. Your Python can pass a list of players, and the template can loop over them.

    **Python Data:**
    ```python
    problem_data = {
        'project_name': 'Player Stats',
        'players': [
            {'name': 'LeBron', 'points': 25},
            {'name': 'Curry', 'points': 30},
            {'name': 'Durant', 'points': 28}
        ]
    }
    ```
    **Template Snippet (`player_stats.xml`):**
    ```xml
    <variables>
        {% for player in players %}
        <variable name="{{ player.name }}"><l>{{ player.points }}</l></variable>
        {% endfor %}
    </variables>
    ...
    <scripts>
        <script x="50" y="50">
            <!-- This script could build a list or find the max score -->
        </script>
    </scripts>
    ```
This approach allows you to handle variations in problem structure without needing dozens of nearly identical templates.
