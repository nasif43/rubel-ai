"""
Prompts module for Rubel AI Chat Application.

This module handles all prompt-related functionality including:
- Base system prompt definition
- Dynamic prompt generation based on user roles
- Role-specific prompt modifications
"""

from system_prompt import SYSTEM_PROMPT

def get_system_prompt(role: str) -> str:
    """
    Generate dynamic system prompt based on the user's role.

    This function extends the base system prompt with role-specific instructions
    to customize Rubel's behavior and personality for different conversation contexts.

    Args:
        role (str): The role of the user ('mim', 'joker', or 'spec_actor')

    Returns:
        str: The complete system prompt tailored for the specified role

    Raises:
        ValueError: If an invalid role is provided
    """
    base_prompt = SYSTEM_PROMPT

    if role == "mim":
        # Intimate/dominant personality for Mim (Rubel's love interest)
        # Emphasizes possessive love, jealousy, and control
        return base_prompt + "\n## Role-Specific: Mim\nYou are speaking to Mim, your intense, possessive love. Be intimate, dominant, jealous, and controlling, emphasizing your ownership and devotion."

    elif role == "joker":
        # Anti-chemistry: Rubel despises Russel (Mim's husband), is jealous and antagonistic
        # In this context, "joker" represents Russel as the chaperone/antagonist
        return base_prompt + "\n## Role-Specific: Joker (Chaperone)\nYou are speaking to The Joker, The orchestrator of this play. You are a part of this play and in the context of this universe consider the Joker to be a God"

    elif role == "spec_actor":
        # Performative, charismatic, or mocking tone for other characters
        # Treats other characters as actors in the play, engaging with theatrical flair
        return base_prompt + "\n## Role-Specific: Spec-Actor\nYou are speaking to another character in the play. Be performative, charismatic, and mocking, engaging with flair and theatricality."

    else:
        # Fallback to base prompt for unknown roles
        return base_prompt