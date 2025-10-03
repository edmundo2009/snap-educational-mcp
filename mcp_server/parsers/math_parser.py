# mcp_server/parsers/math_parser.py

import re
import json
import os
from typing import Dict, List, Optional, Any


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON file with error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {file_path} not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing {file_path}: {e}")
        return {}


def parse_math_problem(text: str) -> Dict[str, Any]:
    """
    Extract numbers and match to pattern triggers.
    
    Args:
        text: Natural language math problem
        
    Returns:
        Dict with pattern, numbers, and original text
    """
    
    # Extract all numbers (integers and decimals)
    numbers = [float(n) for n in re.findall(r'\d+\.?\d*', text)]
    
    # Load patterns from math_patterns.json
    patterns_path = os.path.join(os.path.dirname(__file__), '..', 'knowledge', 'math_patterns.json')
    patterns_data = load_json(patterns_path)
    
    if not patterns_data or 'patterns' not in patterns_data:
        return {"pattern": None, "numbers": numbers, "text": text}
    
    patterns = patterns_data["patterns"]
    
    # Find matching pattern by triggers
    text_lower = text.lower()
    for pattern_name, pattern_data in patterns.items():
        triggers = pattern_data.get("triggers", [])
        for trigger in triggers:
            if trigger in text_lower:
                return {
                    "pattern": pattern_name,
                    "numbers": numbers,
                    "text": text
                }
    
    return {"pattern": None, "numbers": numbers, "text": text}


def get_available_math_patterns() -> List[str]:
    """Get list of available math pattern names."""
    patterns_path = os.path.join(os.path.dirname(__file__), '..', 'knowledge', 'math_patterns.json')
    patterns_data = load_json(patterns_path)
    
    if not patterns_data or 'patterns' not in patterns_data:
        return []
    
    return list(patterns_data["patterns"].keys())


def get_pattern_info(pattern_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific pattern."""
    patterns_path = os.path.join(os.path.dirname(__file__), '..', 'knowledge', 'math_patterns.json')
    patterns_data = load_json(patterns_path)
    
    if not patterns_data or 'patterns' not in patterns_data:
        return None
    
    return patterns_data["patterns"].get(pattern_name)
