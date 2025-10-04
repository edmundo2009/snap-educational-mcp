
### High-Level Workflow: The XML Import Pipeline

This diagram illustrates the new, robust process from start to finish.

```
+---------------------------+       +----------------------------+       +-------------------------------+       +-------------------------+
|      1. Python Backend    |       |    2. WebSocket Server     |       | 3. Browser Extension (JS)     |       |      4. Snap! IDE       |
| (snap_communicator.py)    |------>|      (Your Framework)      |------>|      (snap_bridge.js)         |------>|      (Morphic Engine)   |
+---------------------------+       +----------------------------+       +-------------------------------+       +-------------------------+
| - Defines math problem    |       | - Receives JSON payload    |       | - Receives 'load_project'     |       | - Receives XML string   |
|   (e.g., numbers, vars)   |       |   containing the command   |       |   command from WebSocket      |       |   via openProjectString |
|                           |       |   and the final XML string |       |                               |       |                         |
| - Uses Jinja2 template    |       |                            |       | - Extracts XML string from    |       | - Clears the old project|
|   to generate a complete  |       | - Sends this payload over  |       |   the payload                 |       |                         |
|   project XML string      |       |   the WebSocket connection |       |                               |       | - Parses the XML        |
|                           |       |                            |       | - Calls the single function:  |       |                         |
| - Packages XML into a     |       |                            |       |   ide.openProjectString(xml)  |       | - Rebuilds the entire   |
|   JSON command            |       |                            |       |                               |       |   stage, sprites,       |
|   {'command': 'load...'}  |       |                            |       |                               |       |   scripts, and variables|
|                           |       |                            |       |                               |       |                         |
|                           |       |                            |       |                               |       | - Renders the final,    |
|                           |       |                            |       |                               |       |   correct state         |
+---------------------------+       +----------------------------+       +-------------------------------+       +-------------------------+
```

This pipeline is far more reliable because it delegates the most complex step (rendering and state management) entirely to the Snap! IDE's native, battle-tested import functionality.

---

### Phase 2: Detailed Python Backend Implementation

#### Step 1: Install Jinja2

First, ensure you have the Jinja2 library installed. If not, open your terminal or command prompt and run:

```bash
pip install Jinja2
```

#### Step 2: Create the Jinja2 Template File

It's best practice to separate your template from your Python code.

1.  Create a new folder named `templates` in the same directory as your `snap_communicator.py` script.
2.  Inside the `templates` folder, create a new file named `project_template.xml`.
3.  Paste the following XML into that file. This is your minimal XML, converted into a Jinja2 template with placeholders (`{{ ... }}` and `{% ... %}`).

**File: `templates/project_template.xml`**
```xml

<project app="Snap! 11.0.4, https://snap.berkeley.edu" name="{{ project_name }}" version="2">
	<scenes select="1">
		<scene name="{{ project_name }}">
			<stage>
				<variables/>
				<blocks/>
				<scripts/>
				<sprites select="1">
					<sprite color="80,80,80,1" costume="0" draggable="true" heading="90" id="13" idx="1" name="Sprite" pan="0" pen="tip" rotation="1" scale="1" volume="100" x="0" y="0">
						<blocks/>
						<variables/>
						<scripts>
							<script x="64" y="59">
								<block s="doSetVar">
									<l>{{ variables[0].name }}</l>
									<l>{{ variables[0].value }}</l>
								</block>
								<block s="doSetVar">
									<l>{{ variables[1].name }}</l>
									<l>{{ variables[1].value }}</l>
								</block>
							</script>
							<script x="63" y="136">
								<block s="doSetVar">
									<l>{{ variables[2].name }}</l>
									<block s="reportQuotient">
										<block var="{{ variables[0].name }}"/>
										<block var="{{ variables[1].name }}"/>
									</block>
								</block>
							</script>
						</scripts>
					</sprite>
                    {% for var in variables -%}
					<watcher color="243,118,29" style="normal" var="{{ var.name }}" x="{{ var.watcher_x }}" y="{{ var.watcher_y }}"/>
                    {% endfor -%}
				</sprites>
			</stage>
			<variables>
                {% for var in variables -%}
				<variable name="{{ var.name }}">
					<l>{{ var.value }}</l>
				</variable>
                {% endfor -%}
			</variables>
		</scene>
	</scenes>
</project>
```
*Notice the use of `{% for var in variables %}` to loop through and create the watchers and variable definitions automatically.*

#### Step 3: Write the Python `snap_communicator.py` Logic

Now, modify your Python script to use this template. The code will define the problem's data, load the template, render it with the data, and send it over the WebSocket.

**File: `snap_communicator.py`**
```python

```

### How to Use It
    
mcp_server/
└── tools/
    ├── snap_communicator.py
    └── templates/
        └── project_template.xml

  

Step 3: Modify snap_communicator.py

We will now add the necessary logic to your existing file. This involves three additions:

    Importing the Jinja2 library.

    Adding a new helper function outside the class to handle XML generation.

    Adding a new high-level command method inside the SnapBridgeCommunicator class to send the XML.

    Updating the example_usage to demonstrate the new workflow.

Below is the complete, modified snap_communicator.py file. I have marked the new sections with # NEW: comments for clarity.