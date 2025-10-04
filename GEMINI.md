# Project Overview

This project is a "Snap! Educational MCP System" that allows users to create Snap! programs using natural language. It consists of three main components:

1.  **Terminal (llm CLI):** A command-line interface that allows users to interact with the system.
2.  **MCP Server (Python):** A Python server that uses `FastMCP` to handle user requests, parse natural language into Snap! commands, and communicate with the browser extension via WebSockets. It uses `google-generativeai` for its generative AI capabilities.
3.  **Browser Extension (JavaScript):** A browser extension that injects a "bridge" into the Snap! IDE. This bridge communicates with the MCP server and manipulates the Snap! environment to create blocks, load projects, and provide visual feedback.

The system is designed to be educational, providing kid-friendly explanations of programming concepts and step-by-step tutorials.

# Building and Running

## Prerequisites

*   Python 3.8+
*   Node.js and npm (for browser extension development, if needed)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd snap-educational-mcp
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the System

1.  **Start the MCP Server:**
    ```bash
    python mcp_server/main.py
    ```
    This will start the MCP server and the WebSocket server on `ws://localhost:8765`.

2.  **Load the Browser Extension:**
    *   Open your browser's extension management page (e.g., `chrome://extensions`).
    *   Enable "Developer mode".
    *   Click "Load unpacked" and select the `browser_extension` directory.

3.  **Start a Snap! Session:**
    *   In a new terminal, run:
        ```bash
        llm "start a snap session"
        ```
    *   This will generate a connection token.

4.  **Connect the Browser Extension:**
    *   Open the Snap! IDE in your browser: [https://snap.berkeley.edu/snap/snap.html](https://snap.berkeley.edu/snap/snap.html)
    *   Click the Snap! Educational Assistant extension icon in your browser's toolbar.
    *   Enter the connection token from the previous step.

5.  **Start Programming:**
    *   You can now use the `llm` command to create Snap! programs with natural language:
        ```bash
        llm "make the sprite jump when space is pressed"
        ```

# Development Conventions

*   **Python:**
    *   The Python code follows the PEP 8 style guide.
    *   It uses `pydantic` for data validation and `FastMCP` for the server framework.
    *   The server is designed to be asynchronous, using `asyncio` and `websockets`.
*   **JavaScript:**
    *   The browser extension code is written in modern JavaScript.
    *   It uses a modular architecture, with separate files for the API wrapper, block creator, and WebSocket client.
*   **Communication:**
    *   Communication between the server and the browser extension is done via JSON messages over WebSockets.
    *   The message format is defined in the `mcp_server/main.py` and `browser_extension/snap_bridge/bridge.js` files.
*   **Knowledge Base:**
    *   The educational content, block definitions, and tutorials are stored in JSON files in the `mcp_server/knowledge` directory.
