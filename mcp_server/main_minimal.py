#!/usr/bin/env python3
"""
Minimal MCP Server for Math POC - Only Essential Functions
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Literal, List
from datetime import datetime

# MCP imports
from mcp.server import FastMCP

# Initialize MCP server
mcp = FastMCP("Math POC MCP Server")

# Global components (initialized at startup)
parser = None
generator = None
bridge_communicator = None

# Active sessions - simplified for POC
active_sessions = {}

def initialize_snap_system():
    """Initialize essential Snap! components for math POC"""
    global parser, generator, bridge_communicator
    
    try:
        print("🚀 Initializing Math POC System...")
        
        # Initialize block generator
        from mcp_server.tools.block_generator import SnapBlockGenerator
        generator = SnapBlockGenerator(
            knowledge_path="mcp_server/knowledge/snap_blocks.json",
            patterns_path="mcp_server/knowledge/patterns.json"
        )
        
        # Initialize WebSocket bridge communicator
        from mcp_server.tools.snap_communicator import SnapBridgeCommunicator
        bridge_communicator = SnapBridgeCommunicator(
            host="localhost",
            port=8765
        )
        
        print("✅ Math POC System initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

# ============================================================================
# MCP TOOLS - SESSION MANAGEMENT
# ============================================================================

@mcp.tool()
def start_snap_session(user_id: str = "default") -> Dict[str, Any]:
    """Start a new Snap! programming session for math POC"""
    try:
        import uuid
        session_id = str(uuid.uuid4())[:8]
        token = str(uuid.uuid4())[:12]
        
        active_sessions[session_id] = {
            "user_id": user_id,
            "token": token,
            "created_at": datetime.now().isoformat(),
            "connected": False
        }
        
        return {
            "success": True,
            "session_id": session_id,
            "connection_token": token,
            "instructions": [
                "1. Open Snap! in your browser",
                "2. Install the browser extension",
                "3. Enter this connection token: " + token
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def check_snap_connection(session_id: str) -> Dict[str, Any]:
    """Check if browser extension is connected"""
    if session_id not in active_sessions:
        return {
            "success": False,
            "error": "Session not found"
        }
    
    session = active_sessions[session_id]
    return {
        "success": True,
        "session_id": session_id,
        "connected": session.get("connected", False),
        "snap_ready": session.get("connected", False)
    }

# ============================================================================
# MCP TOOLS - MATH BLOCK GENERATION
# ============================================================================

@mcp.tool()
async def generate_math_blocks(
    problem_text: str,
    grade_level: int = 6,
    execution_mode: Literal["execute", "preview", "explain"] = "execute",
    target_sprite: str = "Sprite",
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate Snap! blocks for a 6th grade math word problem.
    
    Args:
        problem_text: Math problem (e.g., "If 7 hours to mow 4 lawns, how many in 35 hours?")
        grade_level: Grade level (6, 7, or 8)
        execution_mode: "execute" (send to Snap!), "preview" (return JSON), "explain" (return explanation)
        target_sprite: Which sprite to add blocks to
        session_id: Optional session ID
    
    Returns:
        Dict with success status, generated blocks, and execution results
    """
    
    try:
        from mcp_server.parsers.math_parser import parse_math_problem
        
        print(f"🧮 Processing math problem: '{problem_text}'")
        
        # Parse the math problem
        parsed = parse_math_problem(problem_text)
        print(f"📊 Parsed: pattern={parsed['pattern']}, numbers={parsed['numbers']}")
        
        if not parsed["pattern"]:
            return {
                "success": False,
                "error": "Could not identify math pattern in the problem",
                "suggestions": [
                    "Try: 'If 7 hours to mow 4 lawns, how many in 35 hours?'",
                    "Try: 'Ratio 3:2, scale by 4'",
                    "Try: 'Divide 20 cookies among 5 kids'"
                ],
                "available_patterns": ["unit_rate", "ratio_equivalent", "simple_division"]
            }
        
        # Generate blocks using math pattern
        snap_json = generator.generate_from_math_pattern(parsed)
        
        if "error" in snap_json.get("payload", {}):
            return {
                "success": False,
                "error": f"Math block generation failed: {snap_json['payload']['error']}",
                "pattern": parsed["pattern"],
                "numbers": parsed["numbers"]
            }
        
        print(f"✓ Generated math blocks for pattern: {parsed['pattern']}")
        
        # Handle different execution modes
        if execution_mode == "explain":
            return {
                "success": True,
                "mode": "explain",
                "pattern": parsed["pattern"],
                "numbers": parsed["numbers"],
                "explanation": f"This is a {parsed['pattern']} problem. The numbers {parsed['numbers']} will be used to create step-by-step calculations in Snap! blocks.",
                "block_count": len(snap_json.get("payload", {}).get("scripts", [{}])[0].get("blocks", [])),
                "math_concept": parsed["pattern"].replace("_", " ").title()
            }
        
        elif execution_mode == "preview":
            return {
                "success": True,
                "mode": "preview",
                "pattern": parsed["pattern"],
                "numbers": parsed["numbers"],
                "snap_json": snap_json,
                "block_count": len(snap_json.get("payload", {}).get("scripts", [{}])[0].get("blocks", []))
            }
        
        # Execute mode - send to Snap!
        if not session_id:
            if not active_sessions:
                return {
                    "success": False,
                    "error": "No active Snap! session found",
                    "next_action": "Call start_snap_session to begin"
                }
            session_id = max(active_sessions.keys(),
                           key=lambda k: active_sessions[k]["created_at"])
        
        # Send to Snap! via bridge communicator
        result = await bridge_communicator.create_blocks(session_id, snap_json)
        
        return {
            "success": True,
            "mode": "execute",
            "pattern": parsed["pattern"],
            "numbers": parsed["numbers"],
            "blocks_sent": len(snap_json.get("payload", {}).get("scripts", [{}])[0].get("blocks", [])),
            "session_id": session_id,
            "execution_result": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "math_generation_failed",
            "debug_info": {
                "problem_text": problem_text,
                "grade_level": grade_level,
                "execution_mode": execution_mode
            }
        }

# ============================================================================
# SERVER STARTUP
# ============================================================================

def main():
    """Main server entry point"""
    print("🚀 Starting Math POC MCP Server...")

    # Initialize system
    if not initialize_snap_system():
        print("❌ Failed to initialize system")
        return

    print("✅ Math POC MCP Server ready!")
    print("📋 Available tools:")
    print("   - start_snap_session: Start a new session")
    print("   - check_snap_connection: Check connection status")
    print("   - generate_math_blocks: Generate math blocks")

    # Run MCP server
    mcp.run()

if __name__ == "__main__":
    main()
