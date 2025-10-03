# mcp_server/main.py - Snap! Educational MCP Server
from pathlib import Path
import time
from mcp_server.tools.snap_communicator import SnapBridgeCommunicator
from mcp_server.parsers.intent_parser import SnapIntentParser, ParsedIntent
from mcp_server.tools.tutorial_creator import TutorialCreator
from mcp_server.tools.concept_explainer import ConceptExplainer
from mcp_server.tools.block_generator import SnapBlockGenerator, BlockSequence
import websockets
from mcp.server import FastMCP
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Literal, Any
from datetime import datetime, timedelta
import asyncio
import uuid
import hashlib
import hmac
import json
import sys
import os
from dotenv import load_dotenv
load_dotenv()


# Import our Snap! specific modules

# Initialize MCP server
mcp = FastMCP("snap-edu")

# Global components (initialized at startup)
parser = None
generator = None
explainer = None
tutorial_creator = None
bridge_communicator = None

# Active sessions and tokens - now with file persistence

SESSIONS_FILE = Path("active_sessions.json")
LOCK_FILE = Path("active_sessions.json.lock")


def load_sessions():
	"""Load sessions from file"""
	if SESSIONS_FILE.exists():
		try:
			with open(SESSIONS_FILE, 'r') as f:
				data = json.load(f)
				# Convert datetime strings back to datetime objects
				for session_id, session_data in data.items():
					if 'created_at' in session_data and isinstance(session_data['created_at'], str):
						session_data['created_at'] = datetime.fromisoformat(
						    session_data['created_at'])
					if 'expires_at' in session_data and isinstance(session_data['expires_at'], str):
						session_data['expires_at'] = datetime.fromisoformat(
						    session_data['expires_at'])
				return data
		except Exception as e:
			print(f"⚠️ Error loading sessions: {e}")
	return {}


def save_sessions():
	"""Save sessions to file"""
	try:
		# Convert datetime objects to strings for JSON serialization
		data_to_save = {}
		for session_id, session_data in active_sessions.items():
			session_copy = session_data.copy()
			if 'created_at' in session_copy and hasattr(session_copy['created_at'], 'isoformat'):
				session_copy['created_at'] = session_copy['created_at'].isoformat()
			if 'expires_at' in session_copy and hasattr(session_copy['expires_at'], 'isoformat'):
				session_copy['expires_at'] = session_copy['expires_at'].isoformat()
			data_to_save[session_id] = session_copy

		with open(SESSIONS_FILE, 'w') as f:
			json.dump(data_to_save, f, indent=2)
	except Exception as e:
		print(f"⚠️ Error saving sessions: {e}")


def update_session_file(session_id: str, updates: dict):
	"""
	Atomically update a session in the JSON file using a lock file.
	This is the key fix to prevent race conditions.
	"""
	retries = 5
	delay = 0.1
	for i in range(retries):
		try:
			with open(LOCK_FILE, 'w') as lock:
				# Apply an exclusive lock using lock file existence
				# This will prevent other processes from modifying the file simultaneously

				# 1. Read the current state from disk
				current_sessions = {}
				if SESSIONS_FILE.exists():
					with open(SESSIONS_FILE, 'r') as f:
						current_sessions = json.load(f)

				# 2. Modify the specific session
				if session_id in current_sessions:
					current_sessions[session_id].update(updates)

					# Convert datetime objects back to strings for JSON
					for key, value in current_sessions[session_id].items():
						if isinstance(value, datetime):
							current_sessions[session_id][key] = value.isoformat()

					# 3. Write the entire file back
					with open(SESSIONS_FILE, 'w') as f:
						json.dump(current_sessions, f, indent=2)

					print(
					    f"✅ Successfully updated session '{session_id}' in JSON file with {list(updates.keys())}")
					return True
				else:
					print(f"⚠️ Session '{session_id}' not found in file")
					return False
			# Lock is released when 'with' block exits
			break  # Exit retry loop on success
		except (IOError, BlockingIOError) as e:
			print(f"⚠️ Session file is locked, retrying in {delay}s... ({e})")
			time.sleep(delay)
			delay *= 2  # Exponential backoff
		except Exception as e:
			print(f"❌ Error updating session file: {e}")
			return False
		finally:
			# Ensure lock file is removed
			try:
				if LOCK_FILE.exists():
					os.remove(LOCK_FILE)
			except:
				pass

	print(
	    f"❌ Failed to acquire lock and update session file for '{session_id}' after {retries} retries.")
	return False


# Load existing sessions on startup
active_sessions: Dict[str, Dict] = load_sessions()
used_tokens: set = set()

# ============================================================================
# INITIALIZATION
# ============================================================================


def initialize_snap_system():
	"""Initialize all Snap! educational components"""
	global parser, generator, explainer, tutorial_creator, bridge_communicator

	try:
		print("🚀 Initializing Snap! Educational System...")

		# Initialize knowledge-driven components
		parser = SnapIntentParser()
		generator = SnapBlockGenerator(
			knowledge_path="mcp_server/knowledge/snap_blocks.json",
			patterns_path="mcp_server/knowledge/patterns.json"
		)
		explainer = ConceptExplainer(
			concepts_path="mcp_server/knowledge/concepts.json"
		)
		tutorial_creator = TutorialCreator(
			templates_path="mcp_server/knowledge/tutorials.json"
		)

		# Initialize WebSocket bridge communicator with token validator and session callbacks
		bridge_communicator = SnapBridgeCommunicator(
			host="localhost",
			port=8765,
			token_validator=validate_token,  # Pass our token validation function
			session_connected_callback=mark_session_connected,  # Called when session connects
			# Called when session disconnects
			session_disconnected_callback=mark_session_disconnected
		)

		print("✓ Snap! educational system initialized")
		print(
			f"✓ {len(generator.get_available_actions())} programming patterns loaded")
		print(f"✓ WebSocket bridge ready on ws://localhost:8765")

		return True

	except Exception as e:
		print(f"✗ Failed to initialize Snap! system: {e}")
		return False

# ============================================================================
# SECURITY & TOKEN MANAGEMENT
# ============================================================================


def generate_secure_token(session_id: str) -> Dict[str, Any]:
	"""Generate cryptographically secure one-time token"""

	# Get secret key from environment
	secret_key = os.environ.get(
		"SNAP_MCP_SECRET_KEY", "default-dev-key-change-in-production")

	# Token data
	token_uuid = str(uuid.uuid4())
	issued_at = datetime.utcnow()
	expires_at = issued_at + timedelta(minutes=30)

	token_data = {
		"token_id": f"snap-mcp-{token_uuid}",
		"session_id": session_id,
		"issued_at": issued_at.isoformat(),
		"expires_at": expires_at.isoformat(),
		"permissions": [
			"create_blocks",
			"read_project",
			"execute_script",
			"inspect_state",
			"create_custom_block"
		]
	}

	# Generate HMAC signature
	message = json.dumps(token_data, sort_keys=True).encode()
	signature = hmac.new(
		secret_key.encode(),
		message,
		hashlib.sha256
	).hexdigest()

	token_data["hmac"] = signature

	# Store token info
	active_sessions[session_id] = {
		"token": token_data["token_id"],
		"created_at": issued_at,
		"expires_at": expires_at,
		"connected": False
	}

	# Save sessions to file for sharing between processes
	save_sessions()

	return token_data


def find_session_by_display_token(display_token: str) -> Optional[str]:
    """
    Safely find a session ID by its display token, reloading from disk every time.
    """
    sessions_on_disk = load_sessions()  # load_sessions already handles file-not-found, etc.

    for session_id, session_data in sessions_on_disk.items():
        full_token = session_data.get("token")
        if full_token:
            # Generate the display token from the full token for comparison
            token_display_part = full_token.split("-")[-1][:8].upper()
            if token_display_part == display_token.upper():
                return session_id
    return None


def validate_token(display_token: str) -> tuple[Optional[str], Optional[str]]:
    """
    Validate a display token, returning (session_id, error_message).
    This function is now completely self-contained and robust against TypeErrors.
    """
    try:
        session_id = find_session_by_display_token(display_token)

        if not session_id:
            return None, "Session not found for this token."

        # Reload the sessions from disk to get the most current, raw data
        sessions_on_disk = load_sessions()
        session_data = sessions_on_disk.get(session_id)

        if not session_data:
            return None, "Session data disappeared after being found. Please try again."

        # --- THIS IS THE CRITICAL FIX ---
        # Get the expiration date string from the session data
        expires_at_str = session_data.get("expires_at")
        if not expires_at_str:
            return None, "Session is invalid: missing expiration date."

        # Ensure the expiration date is a proper datetime object before comparing
        if isinstance(expires_at_str, str):
            expires_at_dt = datetime.fromisoformat(expires_at_str)
        else:
            # It should already be a datetime object if load_sessions worked, but this is safer
            expires_at_dt = expires_at_str

        # Now, perform the comparison safely
        if datetime.utcnow() > expires_at_dt:
            return None, "Token has expired."

        # The token is valid and not expired. Return the session ID.
        return session_id, None

    except Exception as e:
        # Catch any unexpected errors (like a malformed date string)
        import traceback
        print("❌ UNEXPECTED ERROR during token validation:")
        traceback.print_exc()
        return None, f"An internal error occurred during token validation: {e}"


def mark_session_connected(session_id: str) -> bool:
	"""Mark a session as connected by atomically updating the session file."""
	print(
	    f"🔗 Attempting to mark session '{session_id}' as connected in the session file...")
	updates = {
		"connected": True,
		"connected_at": datetime.now().isoformat()
	}
	result = update_session_file(session_id, updates)
	if result:
		print(f"✅ Session '{session_id}' marked as connected")
	else:
		print(f"❌ Failed to mark session '{session_id}' as connected")
	return result


def mark_session_disconnected(session_id: str) -> bool:
	"""Mark a session as disconnected by atomically updating the session file."""
	print(
	    f"🔌 Attempting to mark session '{session_id}' as disconnected in the session file...")
	updates = {
		"connected": False,
		"disconnected_at": datetime.now().isoformat()
	}
	result = update_session_file(session_id, updates)
	if result:
		print(f"✅ Session '{session_id}' marked as disconnected")
	else:
		print(f"❌ Failed to mark session '{session_id}' as disconnected")
	return result


# ============================================================================
# MCP TOOLS - SESSION MANAGEMENT
# ============================================================================


@mcp.tool()
def start_snap_session(user_id: str = "default") -> Dict[str, Any]:
	"""
	Start a new Snap! programming session and get connection token.

	This must be called first to establish a secure connection between
	the terminal and the Snap! browser extension.

	Args:
		user_id: Optional identifier for the user (for tracking)

	Returns:
		Dictionary containing:
		- token: Security token to enter in browser extension
		- ws_url: WebSocket URL for connection
		- expires_in: Token validity in seconds
		- instructions: How to connect
	"""
	try:
		# Generate new session ID
		session_id = f"sess_{uuid.uuid4().hex[:12]}"

		# Generate secure token
		token_data = generate_secure_token(session_id)

		# Format user-friendly response
		return {
			"success": True,
			"session_id": session_id,
			"token": token_data["token_id"],
			# Last 8 chars, uppercase
			"display_token": token_data["token_id"].split("-")[-1][:8].upper(),
			"ws_url": "ws://localhost:8765",
			"expires_in_seconds": 1800,
			"expires_at": token_data["expires_at"],
			"instructions": [
				"1. Open Snap! in your browser (https://snap.berkeley.edu/snap/snap.html)",
				"2. Click the browser extension icon",
				f"3. Enter this code: {token_data['token_id'].split('-')[-1][:8].upper()}",
				"4. Start creating programs with natural language!"
			],
			"next_step": "Once connected, try: 'make the sprite jump when space is pressed'"
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e),
			"error_type": "session_creation_failed"
		}


@mcp.tool()
def check_snap_connection(session_id: str) -> Dict[str, Any]:
    """
    Check if browser extension is connected and ready by ONLY reading the shared session file.

    Args:
        session_id: Session ID from start_snap_session

    Returns:
        Connection status and readiness information
    """
    try:
        # Reload sessions from file to get the latest data written by any process.
        sessions_on_disk = load_sessions()

        if session_id not in sessions_on_disk:
            return {
                "success": False,
                "connected": False,
                "error": "Session not found. Call start_snap_session first."
            }

        session = sessions_on_disk[session_id]

        # THIS IS THE FIX:
        # We get the connection status DIRECTLY from the dictionary loaded from the file.
        # We no longer ask the temporary bridge_communicator, which knows nothing.
        is_connected = session.get("connected", False)

        # The 'snap_ready' status would also need to be written to the file in a real
        # implementation, but for now, we can infer it.
        snap_ready = is_connected  # Assume if connected, Snap is ready.

        # Ensure 'expires_at' is a datetime object for comparison
        expires_at = session.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)

        session_active = datetime.utcnow() < expires_at

        return {
            "success": True,
            "connected": is_connected,
            "snap_ready": snap_ready,
            "session_active": session_active,
            "time_remaining_seconds": (expires_at - datetime.utcnow()).total_seconds() if session_active else 0,
            "status_message": (
                "✓ Connected and ready!" if (is_connected and snap_ready)
                else "⏳ Waiting for browser connection..."
            )
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# MCP TOOLS - BLOCK GENERATION
# ============================================================================


@mcp.tool()
async def generate_snap_blocks(
	description: str,
	complexity: Literal["beginner", "intermediate", "advanced"] = "beginner",
	execution_mode: Literal["execute", "preview", "explain"] = "execute",
	target_sprite: str = "Sprite",
	animate: bool = True,
	session_id: Optional[str] = None
) -> Dict[str, Any]:
	"""
	Convert natural language to Snap! blocks and optionally execute in browser.

	This is the main tool for creating Snap! programs from descriptions.

	Args:
		description: Natural language description (e.g., "make sprite jump when space pressed")
		complexity: Difficulty level for educational appropriateness
		execution_mode:
			- "execute": Create blocks in browser immediately
			- "preview": Show what would be created without executing
			- "explain": Just explain what the code would do
		target_sprite: Which sprite to add blocks to (default: "Sprite")
		animate: Show visual feedback during creation
		session_id: Session ID (optional, will use most recent if not provided)

	Returns:
		Results including block specifications, explanations, and execution status
	"""
	try:
		# Get active session
		if not session_id:
			if not active_sessions:
				return {
					"success": False,
					"error": "No active session. Call start_snap_session first.",
					"next_action": "Call start_snap_session to begin"
				}
			# Use most recent session
			session_id = max(active_sessions.keys(),
							 key=lambda k: active_sessions[k]["created_at"])

		# Parse natural language
		print(f"📝 Parsing: '{description}'")
		intents = parser.parse(description)

		if not intents:
			return {
				"success": False,
				"error": "Could not understand the request",
				"suggestions": [
					"Try: 'make sprite move right 10 steps'",
					"Try: 'when space key pressed jump up'",
					"Try: 'spin forever and change colors'",
					"Try: 'follow the mouse pointer'"
				],
				"available_patterns": generator.get_available_actions()[:10]
			}

		print(f"✓ Parsed {len(intents)} intent(s)")

		# Generate block sequence
		block_sequence = generator.generate_blocks(intents, complexity)

		print(f"✓ Generated {len(block_sequence.blocks)} block(s)")

		# Format for Snap! bridge
		snap_spec = generator.format_for_snap(block_sequence, target_sprite)

		# Handle different execution modes
		if execution_mode == "explain":
			return {
				"success": True,
				"mode": "explain",
				"explanation": block_sequence.explanation,
				"difficulty": block_sequence.difficulty,
				"block_count": len(block_sequence.blocks),
				"what_it_does": block_sequence.explanation,
				"blocks_summary": [
					{
						"category": block.category,
						"description": block.description
					}
					for block in block_sequence.blocks
				],
				"next_step": "Set execution_mode='execute' to create these blocks in Snap!"
			}

		elif execution_mode == "preview":
			return {
				"success": True,
				"mode": "preview",
				"explanation": block_sequence.explanation,
				"difficulty": block_sequence.difficulty,
				"blocks": [asdict(block) for block in block_sequence.blocks],
				"snap_specification": snap_spec,
				"estimated_creation_time_ms": len(block_sequence.blocks) * 100,
				"next_step": "Set execution_mode='execute' to create these blocks in Snap!"
			}

		elif execution_mode == "execute":
			# Check connection
			if not bridge_communicator.is_connected(session_id):
				return {
					"success": False,
					"error": "Browser not connected",
					"explanation": block_sequence.explanation,
					"blocks_ready": True,
					"blocks": [asdict(block) for block in block_sequence.blocks],
					"next_action": "Connect browser extension and try again"
				}

			# Execute via bridge
			print(f"🚀 Sending to Snap! browser...")

			result = await bridge_communicator.create_blocks(
				session_id=session_id,
				snap_spec=snap_spec,
				animate=animate
			)

			if result["status"] == "success":
				return {
					"success": True,
					"mode": "execute",
					"blocks_created": result["blocks_created"],
					"scripts_created": result["scripts_created"],
					"execution_time_ms": result["execution_time_ms"],
					"explanation": block_sequence.explanation,
					"difficulty": block_sequence.difficulty,
					"sprite": target_sprite,
					"next_steps": [
						"Click the green flag in Snap! to run your program",
						"Try modifying the blocks in Snap!",
						f"Ask me to explain: '{block_sequence.difficulty} programming concepts'"
					],
					"success_message": f"✨ Created {result['blocks_created']} blocks in Snap! {block_sequence.explanation}"
				}
			else:
				return {
					"success": False,
					"error": result.get("error", "Unknown error"),
					"error_details": result.get("details"),
					"recovery_suggestions": result.get("recovery_suggestions", [])
				}

	except Exception as e:
		return {
			"success": False,
			"error": str(e),
			"error_type": "generation_failed",
			"debug_info": {
				"description": description,
				"complexity": complexity,
				"execution_mode": execution_mode
			}
		}


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

	This tool specializes in converting math word problems into interactive
	Snap! block sequences that demonstrate mathematical reasoning step-by-step.

	Args:
		problem_text: Natural language math problem (e.g., "If 7 hours to mow 4 lawns, how many in 35 hours?")
		grade_level: Grade level (6, 7, or 8) - affects complexity and scaffolding
		execution_mode: "execute" (send to Snap!), "preview" (return JSON), "explain" (return explanation)
		target_sprite: Which sprite to add blocks to
		session_id: Optional session ID (uses most recent if not provided)

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
		# result = await bridge_communicator.send_blocks(session_id, snap_json)
		result = await bridge_communicator.create_blocks(session_id, snap_json)
    # result = await bridge_communicator.create_blocks(session_id, snap_spec, animate=True)

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
# MCP TOOLS - CONCEPT EXPLANATION
# ============================================================================


@mcp.tool()
def explain_snap_concept(
	concept: str,
	age_level: Literal["beginner", "intermediate", "advanced"] = "beginner",
	include_examples: bool = True
) -> Dict[str, Any]:
	"""
	Explain Snap! programming concepts in kid-friendly language.
	
	Great for learning before coding or understanding what blocks do.
	
	Args:
		concept: Programming concept (e.g., "loops", "events", "first-class functions")
		age_level: Complexity of explanation
		include_examples: Include code examples
	
	Returns:
		Educational explanation with examples and related concepts
	"""
	try:
		explanation = explainer.explain(concept, age_level)

		if not explanation:
			available = explainer.get_available_concepts()
			return {
				"success": False,
				"error": f"Concept '{concept}' not found",
				"available_concepts": available,
				"suggestion": f"Try: {', '.join(available[:5])}"
			}

		result = {
			"success": True,
			"concept": concept,
			"age_level": age_level,
			"explanation": explanation["text"],
			"key_points": explanation.get("key_points", []),
			"related_concepts": explanation.get("related", [])
		}

		if include_examples:
			result["examples"] = explanation.get("examples", [])
			result["try_it"] = explanation.get("try_commands", [])

		return result

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@mcp.tool()
def list_snap_concepts(category: Optional[str] = None) -> Dict[str, Any]:
	"""
	List all available Snap! concepts that can be explained.
	
	Args:
		category: Optional filter (e.g., "control", "data", "functions")
	
	Returns:
		List of concepts organized by category
	"""
	try:
		concepts = explainer.list_concepts(category)

		return {
			"success": True,
			"concepts": concepts,
			"total_count": sum(len(items) for items in concepts.values()),
			"tip": "Use explain_snap_concept(concept_name) to learn about any concept"
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}

# ============================================================================
# MCP TOOLS - TUTORIAL CREATION
# ============================================================================


@mcp.tool()
async def create_snap_tutorial(
	goal: str,
	difficulty: Literal["beginner", "intermediate", "advanced"] = "beginner",
	step_by_step: bool = True,
	auto_execute: bool = False,
	session_id: Optional[str] = None
) -> Dict[str, Any]:
	"""
	Create a complete step-by-step tutorial for achieving a programming goal.
	
	Perfect for guided learning and structured lessons.
	
	Args:
		goal: What to create (e.g., "a jumping game", "animated character")
		difficulty: Tutorial complexity level
		step_by_step: Include detailed steps
		auto_execute: Automatically create blocks for each step
		session_id: Session ID (optional)
	
	Returns:
		Complete tutorial with steps, code, and explanations
	"""
	try:
		# Generate tutorial
		tutorial = tutorial_creator.create_tutorial(goal, difficulty)

		if not tutorial:
			return {
				"success": False,
				"error": f"Could not create tutorial for '{goal}'",
				"suggestions": tutorial_creator.get_popular_topics()
			}

		result = {
			"success": True,
			"title": tutorial["title"],
			"goal": goal,
			"difficulty": difficulty,
			"estimated_time": tutorial["estimated_time"],
			"overview": tutorial["overview"],
			"prerequisites": tutorial.get("prerequisites", []),
			"learning_objectives": tutorial.get("objectives", [])
		}

		if step_by_step:
			result["steps"] = tutorial["steps"]
			result["total_steps"] = len(tutorial["steps"])

		if auto_execute and session_id:
			# Execute first step automatically
			first_step = tutorial["steps"][0]
			if "code_description" in first_step:
				exec_result = await generate_snap_blocks(
					description=first_step["code_description"],
					complexity=difficulty,
					execution_mode="execute",
					session_id=session_id
				)
				result["first_step_executed"] = exec_result["success"]
				result["next_step"] = tutorial["steps"][1] if len(
					tutorial["steps"]) > 1 else None

		result["completion_tips"] = tutorial.get("tips", [])
		result["challenges"] = tutorial.get("follow_up_challenges", [])

		return result

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}

# ============================================================================
# MCP TOOLS - PROJECT INSPECTION
# ============================================================================


@mcp.tool()
async def inspect_snap_project(
	session_id: Optional[str] = None,
	detail_level: Literal["summary", "detailed", "full"] = "summary"
) -> Dict[str, Any]:
	"""
	Inspect the current Snap! project state.
	
	Useful for understanding what's already in the project before adding more.
	
	Args:
		session_id: Session ID (optional)
		detail_level: How much detail to include
	
	Returns:
		Project information including sprites, scripts, variables
	"""
	try:
		# Get session
		if not session_id:
			session_id = max(active_sessions.keys(),
							 key=lambda k: active_sessions[k]["created_at"])

		# Check connection
		if not bridge_communicator.is_connected(session_id):
			return {
				"success": False,
				"error": "Browser not connected"
			}

		# Request project info from bridge
		project_info = await bridge_communicator.read_project(session_id, detail_level)

		return {
			"success": True,
			"project": project_info,
			"summary": {
				"sprite_count": len(project_info.get("sprites", [])),
				"total_scripts": sum(s.get("script_count", 0) for s in project_info.get("sprites", [])),
				"custom_blocks": len(project_info.get("custom_blocks", []))
			}
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}

# ============================================================================
# MCP TOOLS - DEBUGGING ASSISTANCE
# ============================================================================


@mcp.tool()
def debug_snap_program(
	problem_description: str,
	current_code_description: Optional[str] = None
) -> Dict[str, Any]:
	"""
	Help debug common Snap! programming issues.
	
	Provides kid-friendly debugging suggestions and solutions.
	
	Args:
		problem_description: What's going wrong (e.g., "sprite won't move")
		current_code_description: Optional description of current blocks
	
	Returns:
		Debugging suggestions and solutions
	"""
	try:
		# Common problem patterns
		debug_db = {
			"won't move": {
				"causes": [
					"Missing event block (like 'when flag clicked')",
					"Blocks not connected properly",
					"Sprite already at edge of screen"
				],
				"solutions": [
					"Add a 'when flag clicked' hat block at the top",
					"Make sure all blocks snap together",
					"Try 'go to x: 0 y: 0' to reset position"
				],
				"test": "Click green flag and watch sprite carefully"
			},
			"too fast": {
				"causes": [
					"No wait blocks between actions",
					"Numbers too large in motion blocks"
				],
				"solutions": [
					"Add 'wait 0.1 seconds' between movements",
					"Use smaller numbers (try 5 instead of 50)"
				],
				"test": "Try different wait times to find what feels right"
			},
			"no sound": {
				"causes": [
					"Computer volume is off",
					"Sound block not connected to event",
					"Wrong sound selected"
				],
				"solutions": [
					"Check computer volume settings",
					"Make sure sound block comes after an event block",
					"Try a different sound from the library"
				],
				"test": "Try 'play sound pop' to test audio"
			},
			"disappears": {
				"causes": [
					"Sprite moved off screen",
					"Hide block was used",
					"Size set to 0"
				],
				"solutions": [
					"Use 'go to x: 0 y: 0' to bring back",
					"Add 'show' block at start of script",
					"Set size to 100%"
				],
				"test": "Right-click sprite in sprite list and select 'show'"
			}
		}

		# Find matching problem
		problem_lower = problem_description.lower()
		matching = None
		for key, solution in debug_db.items():
			if key in problem_lower:
				matching = (key, solution)
				break

		if matching:
			problem_type, solution = matching
			return {
				"success": True,
				"problem_type": problem_type,
				"possible_causes": solution["causes"],
				"solutions": solution["solutions"],
				"how_to_test": solution["test"],
				"general_tips": [
					"Always start with an event block (green hat shape)",
					"Make sure blocks snap together properly",
					"Test one small part at a time",
					"Use 'say' blocks to see what's happening"
				]
			}
		else:
			# Generic debugging help
			return {
				"success": True,
				"problem_type": "general",
				"message": "Here are some general debugging tips:",
				"debugging_steps": [
					"1. Check that you have an event block at the start",
					"2. Make sure all blocks are connected (no gaps)",
					"3. Try running just one block at a time",
					"4. Use 'say' blocks to show what the sprite is thinking",
					"5. Click the green flag to restart fresh"
				],
				"common_problems": list(debug_db.keys()),
				"tip": "Describe your problem more specifically for better help"
			}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}

# ============================================================================
# MCP TOOLS - ADVANCED SNAP! FEATURES
# ============================================================================


@mcp.tool()
async def create_custom_snap_block(
	block_name: str,
	parameters: List[Dict[str, str]],
	definition_description: str,
	category: str = "custom",
	session_id: Optional[str] = None
) -> Dict[str, Any]:
	"""
	Create a custom Snap! block (leveraging Snap!'s advanced features).
	
	This teaches abstraction and code reuse.
	
	Args:
		block_name: Name for the custom block (e.g., "jump with sound")
		parameters: List of parameters [{name, type, default}]
		definition_description: Natural language description of what block does
		category: Block category (custom, motion, looks, etc.)
		session_id: Session ID (optional)
	
	Returns:
		Custom block creation status
	"""
	try:
		# Parse definition
		definition_intents = parser.parse(definition_description)
		definition_blocks = generator.generate_blocks(
			definition_intents, "intermediate")

		# Format for custom block creation
		custom_spec = {
			"name": block_name,
			"category": category,
			"parameters": parameters,
			"definition": [asdict(block) for block in definition_blocks.blocks]
		}

		# Get session
		if not session_id:
			session_id = max(active_sessions.keys(),
							 key=lambda k: active_sessions[k]["created_at"])

		# Send to bridge
		result = await bridge_communicator.create_custom_block(session_id, custom_spec)

		return {
			"success": result["status"] == "success",
			"block_name": block_name,
			"message": f"Created custom block '{block_name}'!",
			"how_to_use": f"Look for '{block_name}' in the {category} category",
			"teaching_moment": "Custom blocks let you reuse code and make programs easier to read!"
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
	print("=" * 60)
	print("🎓 Snap! Educational MCP Server")
	print("=" * 60)

	# Initialize system
	if not initialize_snap_system():
		print("❌ Failed to initialize. Check configuration and try again.")
		sys.exit(1)

	# Check if running in STDIO mode (for RovoDev/LLM clients) or standalone mode
	import sys
	is_stdio_mode = not sys.stdin.isatty() or len(sys.argv) > 1 and '--stdio' in sys.argv

	if is_stdio_mode:
		# Running as STDIO MCP server (for RovoDev) + WebSocket server (for browser extension)
		print("🔗 Starting in STDIO mode for MCP client communication")
		print("🔗 Also starting WebSocket server for browser extension")

		import threading
		import asyncio

		def run_websocket_server():
			"""Run WebSocket server in separate thread"""
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
			try:
				loop.run_until_complete(bridge_communicator.start_server())
				print("📡 WebSocket server started on ws://localhost:8765")
				print("✨ Both servers ready!")
				loop.run_forever()
			except Exception as e:
				print(f"❌ WebSocket server error: {e}")
			finally:
				loop.close()

		# Start WebSocket server in background thread
		websocket_thread = threading.Thread(target=run_websocket_server, daemon=True)
		websocket_thread.start()

		# Give WebSocket server time to start
		import time
		time.sleep(1)

		print("🔄 Both servers running... Use Ctrl+C to stop")

		try:
			# Run STDIO server in main thread (blocking)
			# Note: This will keep running until the client disconnects or Ctrl+C
			mcp.run(transport="stdio")
		except KeyboardInterrupt:
			print("\n👋 Servers stopped by user")
		except Exception as e:
			print(f"\n❌ Server error: {e}")
			sys.exit(1)

		# If STDIO server exits normally (e.g., client disconnects), keep WebSocket server running
		try:
			# Try to print to stdout, but handle case where it's closed
			print("\n🔄 STDIO client disconnected, but WebSocket server continues running...")
			print("🌐 Browser extension can still connect on ws://localhost:8765")
			print("⏳ Press Ctrl+C to stop the server")
		except (ValueError, OSError):
			# stdout is closed, redirect to stderr or log file
			import sys
			try:
				sys.stderr.write("\n🔄 STDIO client disconnected, but WebSocket server continues running...\n")
				sys.stderr.write("🌐 Browser extension can still connect on ws://localhost:8765\n")
				sys.stderr.flush()
			except:
				# If stderr is also closed, write to log file
				with open("server.log", "a") as f:
					f.write("\n🔄 STDIO client disconnected, but WebSocket server continues running...\n")
					f.write("🌐 Browser extension can still connect on ws://localhost:8765\n")

		try:
			# Keep the process alive so WebSocket server continues running
			while True:
				import time
				time.sleep(1)
		except KeyboardInterrupt:
			try:
				print("\n👋 All servers stopped")
			except:
				pass
	else:
		# Running in standalone mode with WebSocket server (for browser extension)
		async def run_websocket_server():
			"""Run WebSocket server for browser extension"""
			try:
				# Start WebSocket server
				await bridge_communicator.start_server()

				print("\n✨ Server ready! Next steps:")
				print("1. In your terminal: llm 'start a snap session'")
				print("2. Open Snap! in browser and install extension")
				print("3. Enter the connection code")
				print("4. Start creating: llm 'make sprite jump when space pressed'")
				print("\n" + "=" * 60)

				# Keep the server running
				print("🔄 WebSocket server running... Press Ctrl+C to stop")
				while True:
					await asyncio.sleep(1)

			except KeyboardInterrupt:
				print("\n👋 Server stopped by user")
			except Exception as e:
				print(f"\n❌ Server error: {e}")
				raise

		# Run the WebSocket server
		try:
			asyncio.run(run_websocket_server())
		except KeyboardInterrupt:
			print("\n👋 Goodbye!")
		except Exception as e:
			print(f"\n❌ Fatal error: {e}")
			sys.exit(1)
