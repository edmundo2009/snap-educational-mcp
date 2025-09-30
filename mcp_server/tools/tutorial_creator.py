# mcp_server/tools/tutorial_creator.py - Step-by-Step Tutorial Generator

import json
import os
from typing import Dict, List, Optional, Any


class TutorialCreator:
    """
    Creates step-by-step tutorials for Snap! programming projects.
    
    Generates structured learning experiences with clear objectives,
    progressive steps, and educational explanations.
    """

    def __init__(self, templates_path: str = "knowledge/tutorials.json"):
        self.templates_path = templates_path
        self.tutorials_db = {}
        self.load_tutorials()

    def load_tutorials(self):
        """Load tutorial templates from JSON file"""
        try:
            if os.path.exists(self.templates_path):
                with open(self.templates_path, 'r') as f:
                    self.tutorials_db = json.load(f)
                print(f"✓ Loaded {len(self.tutorials_db.get('tutorials', {}))} tutorial templates")
            else:
                print(f"⚠ Tutorials file not found: {self.templates_path}")
                self.tutorials_db = self._create_default_tutorials()

        except Exception as e:
            print(f"✗ Error loading tutorials: {e}")
            self.tutorials_db = self._create_default_tutorials()

    def _create_default_tutorials(self) -> Dict[str, Any]:
        """Create default tutorial templates"""
        return {
            "tutorials": {
                "jumping_game": {
                    "title": "Build a Jumping Game",
                    "description": "Create a simple game where a sprite jumps when you press the space key",
                    "difficulty": "beginner",
                    "estimated_time": "15 minutes",
                    "prerequisites": ["basic Snap! navigation"],
                    "objectives": [
                        "Learn about event blocks",
                        "Understand motion blocks",
                        "Create interactive programs"
                    ],
                    "overview": "In this tutorial, you'll create your first interactive Snap! program! Your sprite will jump up and down when you press the space key. This teaches you about events (things that start programs) and motion (making sprites move).",
                    "steps": [
                        {
                            "step": 1,
                            "title": "Set up your sprite",
                            "description": "Make sure you have a sprite ready to jump. The default cat sprite works great!",
                            "instructions": [
                                "Look at the sprite area (bottom right)",
                                "You should see a cat sprite",
                                "If not, click the sprite icon to add one"
                            ],
                            "success_criteria": "You can see a sprite in the sprite area"
                        },
                        {
                            "step": 2,
                            "title": "Add the event block",
                            "description": "Every interactive program needs an event block to start it. This tells Snap! when to run your code.",
                            "code_description": "when space key pressed",
                            "instructions": [
                                "Go to the Events category (yellow blocks)",
                                "Drag 'when [space] key pressed' to the scripts area",
                                "This is called a 'hat block' because of its shape"
                            ],
                            "teaching_moment": "Event blocks are like triggers - they start your program when something happens!",
                            "success_criteria": "You have a yellow hat block in your scripts area"
                        },
                        {
                            "step": 3,
                            "title": "Make the sprite jump up",
                            "description": "Now we'll add the motion that makes the sprite jump upward.",
                            "code_description": "change y by 50",
                            "instructions": [
                                "Go to the Motion category (blue blocks)",
                                "Drag 'change y by 10' block",
                                "Connect it under the event block",
                                "Change the number from 10 to 50"
                            ],
                            "teaching_moment": "Y coordinates control up and down movement. Positive numbers go up!",
                            "success_criteria": "Blue motion block is connected under the event block"
                        },
                        {
                            "step": 4,
                            "title": "Add a pause",
                            "description": "We need to wait a moment before the sprite comes back down, or it will happen too fast to see!",
                            "code_description": "wait 0.3 seconds",
                            "instructions": [
                                "Go to the Control category (orange blocks)",
                                "Drag 'wait 1 seconds' block",
                                "Connect it under the motion block",
                                "Change 1 to 0.3 for a quick pause"
                            ],
                            "teaching_moment": "Wait blocks create timing in your programs. Without them, everything happens instantly!",
                            "success_criteria": "Orange wait block is connected in the sequence"
                        },
                        {
                            "step": 5,
                            "title": "Make the sprite come back down",
                            "description": "Now we'll add the motion that brings the sprite back to its starting position.",
                            "code_description": "change y by -50",
                            "instructions": [
                                "Add another 'change y by' block",
                                "Connect it under the wait block",
                                "Change the number to -50 (negative fifty)"
                            ],
                            "teaching_moment": "Negative numbers make the sprite go down. This undoes the upward jump!",
                            "success_criteria": "Second motion block with -50 is connected"
                        },
                        {
                            "step": 6,
                            "title": "Test your jumping game!",
                            "description": "Time to see your creation in action!",
                            "instructions": [
                                "Click the green flag to start your program",
                                "Press the space key",
                                "Watch your sprite jump!",
                                "Try pressing space multiple times"
                            ],
                            "success_criteria": "Sprite jumps when you press space key",
                            "troubleshooting": [
                                "If nothing happens: Check that blocks are connected",
                                "If sprite disappears: It might have jumped off screen - click the green flag to reset"
                            ]
                        }
                    ],
                    "completion_message": "🎉 Congratulations! You've created your first interactive Snap! program!",
                    "what_you_learned": [
                        "Event blocks start programs when things happen",
                        "Motion blocks move sprites around the screen",
                        "Wait blocks control timing",
                        "Negative numbers reverse direction"
                    ],
                    "next_challenges": [
                        "Make the sprite jump higher or lower",
                        "Add a sound when the sprite jumps",
                        "Make the sprite change colors while jumping",
                        "Create a double-jump by pressing space twice quickly"
                    ]
                },
                "bouncing_ball": {
                    "title": "Create a Bouncing Ball",
                    "description": "Build a ball that bounces around the screen forever",
                    "difficulty": "beginner",
                    "estimated_time": "20 minutes",
                    "prerequisites": ["basic motion blocks"],
                    "objectives": [
                        "Learn about forever loops",
                        "Understand edge detection",
                        "Create continuous motion"
                    ],
                    "steps": [
                        {
                            "step": 1,
                            "title": "Create a ball sprite",
                            "description": "First, we need a ball to bounce around",
                            "instructions": [
                                "Click the sprite icon to add a new sprite",
                                "Choose a ball costume or draw a circle",
                                "Make it a bright color so it's easy to see"
                            ]
                        },
                        {
                            "step": 2,
                            "title": "Start the bouncing",
                            "description": "Add blocks to make the ball move and bounce forever",
                            "code_description": "when flag clicked, forever move 10 steps, if on edge bounce",
                            "instructions": [
                                "Add 'when flag clicked' event block",
                                "Add 'forever' loop from Control category",
                                "Inside the loop: 'move 10 steps' and 'if on edge, bounce'"
                            ]
                        }
                    ]
                }
            }
        }

    def create_tutorial(self, goal: str, difficulty: str = "beginner") -> Optional[Dict[str, Any]]:
        """
        Create a tutorial for achieving a specific goal.
        
        Args:
            goal: What the user wants to create
            difficulty: Tutorial complexity level
            
        Returns:
            Complete tutorial with steps and explanations
        """
        goal_lower = goal.lower()
        
        # Find matching tutorial template
        for tutorial_name, tutorial_data in self.tutorials_db.get("tutorials", {}).items():
            # Check if goal matches tutorial name or description
            if (goal_lower in tutorial_name or 
                goal_lower in tutorial_data.get("description", "").lower() or
                any(keyword in goal_lower for keyword in tutorial_data.get("keywords", []))):
                
                # Adapt tutorial to requested difficulty if needed
                adapted_tutorial = self._adapt_tutorial_difficulty(tutorial_data, difficulty)
                return adapted_tutorial
        
        # If no exact match, try to generate a basic tutorial
        return self._generate_basic_tutorial(goal, difficulty)

    def _adapt_tutorial_difficulty(self, tutorial: Dict[str, Any], target_difficulty: str) -> Dict[str, Any]:
        """Adapt tutorial complexity to target difficulty level"""
        adapted = tutorial.copy()
        adapted["difficulty"] = target_difficulty
        
        if target_difficulty == "beginner":
            # Add more detailed explanations and teaching moments
            for step in adapted.get("steps", []):
                if "teaching_moment" not in step:
                    step["teaching_moment"] = f"This step helps you learn about {step.get('title', 'programming').lower()}!"
        
        elif target_difficulty == "advanced":
            # Add extension challenges and deeper concepts
            adapted["extension_challenges"] = [
                "Modify the code to add advanced features",
                "Experiment with different parameters",
                "Combine with other programming concepts"
            ]
        
        return adapted

    def _generate_basic_tutorial(self, goal: str, difficulty: str) -> Dict[str, Any]:
        """Generate a basic tutorial for goals not in the database"""
        return {
            "title": f"Create {goal.title()}",
            "description": f"Learn to build {goal} in Snap!",
            "difficulty": difficulty,
            "estimated_time": "10-15 minutes",
            "overview": f"This tutorial will guide you through creating {goal} step by step.",
            "steps": [
                {
                    "step": 1,
                    "title": "Plan your project",
                    "description": f"Think about what blocks you might need for {goal}",
                    "instructions": [
                        "Consider what the sprite should do",
                        "Think about what events should trigger actions",
                        "Plan the sequence of blocks needed"
                    ]
                },
                {
                    "step": 2,
                    "title": "Start building",
                    "description": "Begin with a simple version and add complexity",
                    "code_description": goal,
                    "instructions": [
                        "Start with an event block",
                        "Add the main action blocks",
                        "Test frequently as you build"
                    ]
                }
            ],
            "next_steps": [
                "Try the generate_snap_blocks tool to get specific blocks",
                "Ask for explanations of concepts you don't understand",
                "Experiment with different variations"
            ]
        }

    def get_popular_topics(self) -> List[str]:
        """Get list of popular tutorial topics"""
        topics = []
        for tutorial_name, tutorial_data in self.tutorials_db.get("tutorials", {}).items():
            topics.append(tutorial_data.get("title", tutorial_name.replace("_", " ").title()))
        
        # Add some common requests not in database
        topics.extend([
            "Animation Tutorial",
            "Game Creation Basics",
            "Interactive Story",
            "Art and Drawing",
            "Music and Sound Effects"
        ])
        
        return topics

    def get_tutorials_by_difficulty(self, difficulty: str) -> List[Dict[str, Any]]:
        """Get all tutorials for a specific difficulty level"""
        matching_tutorials = []
        
        for tutorial_name, tutorial_data in self.tutorials_db.get("tutorials", {}).items():
            if tutorial_data.get("difficulty") == difficulty:
                matching_tutorials.append({
                    "name": tutorial_name,
                    "title": tutorial_data.get("title"),
                    "description": tutorial_data.get("description"),
                    "estimated_time": tutorial_data.get("estimated_time")
                })
        
        return matching_tutorials

    def get_tutorial_prerequisites(self, tutorial_name: str) -> List[str]:
        """Get prerequisites for a specific tutorial"""
        tutorial_data = self.tutorials_db.get("tutorials", {}).get(tutorial_name)
        if tutorial_data:
            return tutorial_data.get("prerequisites", [])
        return []

    def suggest_next_tutorial(self, completed_tutorial: str) -> Optional[str]:
        """Suggest the next tutorial based on what was just completed"""
        # Simple progression logic
        progressions = {
            "jumping_game": "bouncing_ball",
            "bouncing_ball": "interactive_story",
            "interactive_story": "simple_game"
        }
        
        return progressions.get(completed_tutorial)
