# mcp_server/tools/concept_explainer.py - Educational Concept Explanations

import json
import os
from typing import Dict, List, Optional, Any


class ConceptExplainer:
    """
    Educational concept explainer for Snap! programming concepts.
    
    Provides age-appropriate explanations of programming concepts,
    from basic blocks to advanced features like first-class functions.
    """

    def __init__(self, concepts_path: str = "knowledge/concepts.json"):
        self.concepts_path = concepts_path
        self.concepts_db = {}
        self.load_concepts()

    def load_concepts(self):
        """Load concept definitions from JSON file"""
        try:
            if os.path.exists(self.concepts_path):
                with open(self.concepts_path, 'r') as f:
                    self.concepts_db = json.load(f)
                print(f"✓ Loaded {len(self.concepts_db.get('concepts', {}))} concept explanations")
            else:
                print(f"⚠ Concepts file not found: {self.concepts_path}")
                self.concepts_db = self._create_default_concepts()

        except Exception as e:
            print(f"✗ Error loading concepts: {e}")
            self.concepts_db = self._create_default_concepts()

    def _create_default_concepts(self) -> Dict[str, Any]:
        """Create default concept explanations"""
        return {
            "concepts": {
                "loops": {
                    "beginner": {
                        "text": "Loops are like doing the same thing over and over! Instead of writing the same blocks many times, you can use a loop block to repeat them automatically.",
                        "key_points": [
                            "Loops save time by repeating actions",
                            "The 'repeat' block is the simplest loop",
                            "You can loop forever or a specific number of times"
                        ],
                        "examples": [
                            "Repeat 10 times: move 10 steps (makes sprite move in a line)",
                            "Forever: turn 15 degrees (makes sprite spin continuously)"
                        ],
                        "try_commands": [
                            "make sprite move in a square using loops",
                            "create a spinning animation"
                        ]
                    },
                    "intermediate": {
                        "text": "Loops are control structures that repeat a set of instructions. Snap! has several types: repeat (fixed number), repeat until (condition-based), and forever (infinite).",
                        "key_points": [
                            "Different loop types serve different purposes",
                            "Conditions can control when loops stop",
                            "Nested loops create complex patterns"
                        ],
                        "examples": [
                            "Repeat until touching edge: move and bounce",
                            "Nested loops: repeat 4 [repeat 10 [move 10 steps] turn 90 degrees]"
                        ]
                    }
                },
                "events": {
                    "beginner": {
                        "text": "Events are things that happen that can start your program! Like pressing a key, clicking the mouse, or clicking the green flag. Event blocks are the hat-shaped blocks at the top of scripts.",
                        "key_points": [
                            "Events start scripts running",
                            "Hat blocks (green, rounded top) are event blocks",
                            "Multiple scripts can respond to the same event"
                        ],
                        "examples": [
                            "When flag clicked: starts when you click green flag",
                            "When space key pressed: starts when you press spacebar",
                            "When this sprite clicked: starts when you click the sprite"
                        ],
                        "try_commands": [
                            "make sprite jump when space is pressed",
                            "change color when sprite is clicked"
                        ]
                    }
                },
                "first-class functions": {
                    "intermediate": {
                        "text": "In Snap!, blocks can be inputs to other blocks! This means you can pass blocks around like data. It's like having blocks inside blocks that can change what they do.",
                        "key_points": [
                            "Blocks can be inputs to other blocks",
                            "The 'for each' block takes another block as input",
                            "Custom blocks can accept block inputs",
                            "This enables powerful programming patterns"
                        ],
                        "examples": [
                            "for each item in list: [say item for 1 seconds]",
                            "map [multiply by 2] over [1, 2, 3, 4] = [2, 4, 6, 8]"
                        ],
                        "related": ["custom blocks", "lists", "higher-order functions"]
                    },
                    "advanced": {
                        "text": "First-class functions are a powerful feature where functions (blocks) are treated as data. You can store them in variables, pass them as arguments, and return them from other functions.",
                        "key_points": [
                            "Functions are values that can be manipulated",
                            "Enables functional programming patterns",
                            "Critical for advanced computer science concepts",
                            "Allows for elegant solutions to complex problems"
                        ],
                        "examples": [
                            "Creating function factories",
                            "Implementing map, filter, reduce operations",
                            "Building domain-specific languages"
                        ]
                    }
                },
                "variables": {
                    "beginner": {
                        "text": "Variables are like boxes that hold information! You can put numbers, words, or other data in them and use them later. The variable's name is like a label on the box.",
                        "key_points": [
                            "Variables store data for later use",
                            "You can change what's in a variable",
                            "Variables have names so you can find them",
                            "Use 'set' to put data in, 'change' to modify"
                        ],
                        "examples": [
                            "Set score to 0 (creates a score counter)",
                            "Change score by 10 (adds 10 to current score)",
                            "Say score (shows the current score)"
                        ],
                        "try_commands": [
                            "create a score counter that increases when sprite is clicked",
                            "make a timer that counts seconds"
                        ]
                    }
                },
                "custom blocks": {
                    "intermediate": {
                        "text": "Custom blocks let you create your own blocks! It's like making a new tool that does exactly what you want. You can reuse it many times and make your programs easier to read.",
                        "key_points": [
                            "Create reusable pieces of code",
                            "Make programs easier to understand",
                            "Can have inputs (parameters) to customize behavior",
                            "Promotes good programming practices"
                        ],
                        "examples": [
                            "Make a 'draw square' block that draws any size square",
                            "Create a 'jump with sound' block that plays a sound while jumping"
                        ],
                        "try_commands": [
                            "create a custom block for drawing shapes",
                            "make a custom block that combines movement and sound"
                        ]
                    }
                }
            }
        }

    def explain(self, concept: str, age_level: str = "beginner") -> Optional[Dict[str, Any]]:
        """
        Get explanation for a programming concept.
        
        Args:
            concept: The concept to explain (e.g., "loops", "events")
            age_level: Complexity level ("beginner", "intermediate", "advanced")
            
        Returns:
            Dictionary with explanation, examples, and related concepts
        """
        concept_lower = concept.lower()
        
        # Find matching concept
        for concept_name, concept_data in self.concepts_db.get("concepts", {}).items():
            if concept_lower in concept_name or concept_name in concept_lower:
                if age_level in concept_data:
                    return concept_data[age_level]
                else:
                    # Fall back to beginner if requested level not available
                    return concept_data.get("beginner", concept_data.get(list(concept_data.keys())[0]))
        
        return None

    def get_available_concepts(self) -> List[str]:
        """Get list of all available concepts"""
        return list(self.concepts_db.get("concepts", {}).keys())

    def list_concepts(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List concepts organized by category.
        
        Args:
            category: Optional filter for specific category
            
        Returns:
            Dictionary of concepts organized by category
        """
        # For now, organize by complexity since we don't have categories in the data
        organized = {
            "basic": [],
            "intermediate": [],
            "advanced": []
        }
        
        for concept_name, concept_data in self.concepts_db.get("concepts", {}).items():
            if "beginner" in concept_data:
                organized["basic"].append(concept_name)
            if "intermediate" in concept_data:
                organized["intermediate"].append(concept_name)
            if "advanced" in concept_data:
                organized["advanced"].append(concept_name)
        
        if category:
            return {category: organized.get(category, [])}
        
        return organized

    def get_related_concepts(self, concept: str) -> List[str]:
        """Get concepts related to the given concept"""
        concept_data = self.explain(concept, "intermediate")
        if concept_data:
            return concept_data.get("related", [])
        return []

    def search_concepts(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for concepts matching a query.
        
        Args:
            query: Search term
            
        Returns:
            List of matching concepts with brief descriptions
        """
        query_lower = query.lower()
        matches = []
        
        for concept_name, concept_data in self.concepts_db.get("concepts", {}).items():
            # Check if query matches concept name
            if query_lower in concept_name.lower():
                beginner_explanation = concept_data.get("beginner", {})
                matches.append({
                    "concept": concept_name,
                    "brief": beginner_explanation.get("text", "")[:100] + "...",
                    "difficulty_levels": list(concept_data.keys())
                })
                continue
            
            # Check if query matches in explanation text
            for level, level_data in concept_data.items():
                if query_lower in level_data.get("text", "").lower():
                    matches.append({
                        "concept": concept_name,
                        "brief": level_data.get("text", "")[:100] + "...",
                        "difficulty_levels": list(concept_data.keys()),
                        "matched_level": level
                    })
                    break
        
        return matches

    def get_concept_progression(self, start_concept: str) -> List[str]:
        """
        Get a suggested learning progression starting from a concept.
        
        Args:
            start_concept: Starting concept
            
        Returns:
            List of concepts in suggested learning order
        """
        # Simple progression based on typical CS education
        progressions = {
            "events": ["variables", "loops", "conditions", "custom blocks"],
            "variables": ["loops", "conditions", "lists", "custom blocks"],
            "loops": ["conditions", "custom blocks", "lists", "first-class functions"],
            "conditions": ["custom blocks", "lists", "recursion"],
            "custom blocks": ["first-class functions", "recursion", "data structures"],
            "lists": ["first-class functions", "data structures", "algorithms"],
            "first-class functions": ["recursion", "data structures", "algorithms"]
        }
        
        return progressions.get(start_concept.lower(), [])
