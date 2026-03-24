from langchain_google_genai import ChatGoogleGenerativeAI
import os

_llm = None

def get_llm(temperature=0.3):

    global _llm

    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            google_api_key=os.getenv("GEMINI_KEY"),
            temperature=temperature
        )

    return _llm