import os
from langchain_groq import ChatGroq

def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama3-8b-8192",   # fast + free tier
        temperature=0.3,
        max_tokens=1024,
    )