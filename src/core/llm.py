#llm.py
"""
Centralized LLM factory used across the application.

This module ensures all agents share a single initialized language model
instance instead of repeatedly creating new clients.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
import os

_llm = None

def get_llm(temperature=0.3):
    """
    Return shared Gemini chat model instance.

    The first call creates the model. Later calls reuse it.

    Args:
        temperature: Sampling temperature for response creativity.

    Returns:
        ChatGoogleGenerativeAI instance.
    """    

    global _llm

    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            google_api_key=os.getenv("GEMINI_KEY"),
            temperature=temperature
        )

    return _llm