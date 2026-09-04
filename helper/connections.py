"""
Local LLM connection helper.

This project talks to a local Ollama server through its OpenAI-compatible
API (http://localhost:11434/v1). Ollama installs with a single command on
macOS/Linux/Windows and uses Metal (Apple Silicon) or CUDA acceleration
automatically, which makes it a much simpler local-LLM story than running
a vLLM server.

One-time setup:
    1. Install Ollama: https://ollama.com/download
    2. Pull a model, e.g.:  ollama pull qwen2.5:32b-instruct
    3. Ollama runs its server automatically after install. If it isn't
       running, start it with: ollama serve

Configure the model via a .env file in the project root (see .env.example):
    OLLAMA_MODEL="qwen2.5:32b-instruct"

Every agent script in this repo should get its LLM client from get_llm()
below rather than constructing ChatOpenAI directly, so the connection
details only live in one place.
"""

import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "qwen2.5:32b-instruct"
DEFAULT_PORT = 11434


def get_llm(
    model_name: str = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    port: int = DEFAULT_PORT,
) -> ChatOpenAI:
    """Returns a ChatOpenAI client pointed at a local Ollama server.

    Ollama exposes an OpenAI-compatible endpoint, so the rest of the
    codebase (LangChain / LangGraph agents) doesn't need to know it isn't
    talking to a hosted API.
    """
    model_name = model_name or os.getenv("OLLAMA_MODEL") or os.getenv("MODEL_NAME") or DEFAULT_MODEL

    print(f"🔌 Connecting to local Ollama server (model={model_name})...")
    llm = ChatOpenAI(
        model=model_name,
        base_url=f"http://localhost:{port}/v1",
        api_key="ollama",  # required by the OpenAI client, ignored by Ollama
        temperature=temperature,
        max_tokens=max_tokens,
    )
    print("✅ Successfully connected to Ollama.")
    return llm


# Backwards-compatible aliases: earlier versions of this codebase called
# these connect_to_vllm() / get_vllm_llm(). Keep them working so nothing
# else needs to change.
connect_to_vllm = get_llm
get_vllm_llm = get_llm


if __name__ == "__main__":
    get_llm()
