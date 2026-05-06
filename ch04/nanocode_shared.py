"""
Nanocode v0.4 - Switchable Brains Edition
Chapter 4: Using shared brains.py module

This version uses the shared brains module instead of duplicating brain code.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brains import (
    AgentStop,
    Thought,
    Brain,
    Claude,
    DeepSeek,
    ZaiCoding,
    BRAINS
)


class Agent:
    """A coding agent with a switchable brain."""

    def __init__(self, brain, brain_name="claude"):
        self.brain = brain
        self.brain_name = brain_name
        self.conversation = []

    def handle_input(self, user_input):
        """Handle user input. Returns output string, raises AgentStop to quit."""
        if user_input.strip() == "/q":
            raise AgentStop()

        if user_input.strip() == "/switch":
            self._switch_brain()
            return f"Switched to: {self.brain_name}"

        # Add user message to conversation
        self.conversation.append({"role": "user", "content": user_input})

        # Get thought from brain
        thought = self.brain.think(self.conversation)

        # Extract response text
        response_text = thought.text if thought.text else ""

        # Add assistant response to conversation
        if response_text:
            self.conversation.append({"role": "assistant", "content": response_text})

        return response_text

    def _switch_brain(self):
        """Switch to the next available brain."""
        names = list(BRAINS.keys())
        idx = names.index(self.brain_name)
        new_name = names[(idx + 1) % len(names)]
        
        # Initialize new brain (no tools/memory in ch04)
        self.brain = BRAINS[new_name]()
        self.brain_name = new_name


def main():
    import os
    
    # Get default brain from environment or use claude
    default_brain = os.getenv("NANOCODE_BRAIN", "claude")
    
    if default_brain not in BRAINS:
        print(f"❌ Unknown brain: {default_brain}")
        print(f"Available brains: {', '.join(BRAINS.keys())}")
        default_brain = "claude"
    
    # Initialize agent with selected brain
    brain = BRAINS[default_brain]()
    agent = Agent(brain, default_brain)
    
    print(f"🤖 Nanocode v0.4 (Shared Module)")
    print(f"🧠 Current brain: {agent.brain_name}")
    print(f"💭 Commands: /switch (change brain), /q (quit)")
    print()
    
    while True:
        try:
            user_input = input(f"[{agent.brain_name}] ❯ ")
            if not user_input.strip():
                continue
            
            response = agent.handle_input(user_input)
            print(response)
            
        except AgentStop:
            print("Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()